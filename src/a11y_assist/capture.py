"""Record a page to HAR once, then replay it so every test run sees the same
network responses.

A HAR freezes network responses only. Client-side randomness or the clock can
still vary between replays.
"""

from __future__ import annotations

import json
import re
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from playwright.async_api import Browser, BrowserContext

from a11y_assist.andi import install_andi_routes
from a11y_assist.browser import LogFn, NavigationGuard, new_context
from a11y_assist.config import Settings
from a11y_assist.egress import EgressProxy
from a11y_assist.redact import safe_url
from a11y_assist.traverse import INIT_JS

MAX_FRAMES_KEPT = 20  # enough to show why; the decision needs only one


@dataclass
class Capture:
    target_url: str
    final_url: str
    har_path: Path
    redirects: list[dict[str, Any]] = field(default_factory=list)
    # Frames on another host than the top page, seen while recording. Their
    # replays run in full Chromium (browser.replay_in_full_chromium).
    cross_site_frames: list[str] = field(default_factory=list)
    # Media saved in full for replay, and files over the cap (media store).
    media: list[dict[str, Any]] = field(default_factory=list)
    frozen: bool = False  # replayed from a frozen pages folder (frozen.py)


async def record(
    browser: Browser,
    settings: Settings,
    url: str,
    har_path: Path,
    log: LogFn,
    egress: EgressProxy | None = None,
) -> Capture:
    """Load `url` live in a fresh context and save every response to `har_path`."""
    ctx = await new_context(
        browser, settings, record_har_path=str(har_path), record_har_mode="full"
    )
    guard = NavigationGuard(settings, live=True, log=log, egress=egress)
    await guard.install(ctx)
    try:
        page = await ctx.new_page()
        final_url = await guard.goto(page, url)
        await _idle(page, log, 10_000)
        # Scroll to the bottom so content loaded on scroll is recorded (4.C spec
        # section 2, Recording).
        for i in range(settings.record_scroll_passes):
            height = await page.evaluate("document.documentElement.scrollHeight")
            await page.evaluate(
                "window.scrollTo(0, document.documentElement.scrollHeight)"
            )
            await page.mouse.wheel(0, 400)
            await _idle(page, log, 3_000)
            grew = await page.evaluate("document.documentElement.scrollHeight") > height
            log("capture_scroll", pass_=i + 1, page_grew=grew)
        frames = cross_site_frames(page.url, [f.url for f in page.frames[1:]])
        if frames:
            log("capture_cross_site_frames", count=len(frames))
        media = await _fetch_media(ctx, page, settings, log)
    finally:
        await ctx.close()  # writes the HAR
    _add_media(har_path, media)
    return Capture(
        url,
        final_url,
        har_path,
        guard.redirects,
        frames,
        media=[{k: v for k, v in m.items() if k != "body"} for m in media],
    )


# ── Media store (2.A-2.D plan items 13-14, Q9) ─────────────────────────────
# A large video is fetched in byte ranges; the browser cancels the open
# ended request when it seeks, so the HAR keeps ranges with no body and the
# video never plays on replay. So while recording, each media URL is also
# fetched once in full (within a size and time cap) and stored inside the
# HAR zip; on replay its byte ranges are served from there.

MEDIA_INDEX = "a11y-media.json"
_MEDIA_JS = """() => Array.from(document.querySelectorAll('video, audio'))
  .flatMap((m) => [m.currentSrc, m.src,
    ...Array.from(m.querySelectorAll('source')).map((s) => s.src)])
  .filter((u) => /^https?:/.test(u || ''))"""


async def _media_size(ctx, url: str) -> tuple[int | None, str]:
    """A media file's size without downloading it: Content-Length from a
    HEAD that succeeded, else the total in Content-Range for byte 0 alone
    (a server that ignores ranges sends the file, whose length is the
    size)."""
    try:
        head = await ctx.request.head(url, timeout=5000)
        size = head.headers.get("content-length", "")
        if head.ok and size.isdigit():
            return int(size), head.headers.get("content-type", "")
    except Exception:
        pass
    try:
        one = await ctx.request.get(url, headers={"Range": "bytes=0-0"}, timeout=5000)
        kind = one.headers.get("content-type", "")
        total = re.search(r"/(\d+)$", one.headers.get("content-range", ""))
        if one.status == 206 and total:
            return int(total.group(1)), kind
        if one.ok:
            return len(await one.body()), kind
    except Exception:
        pass
    return None, ""


async def _fetch_media(
    ctx, page, settings: Settings, log: LogFn
) -> list[dict[str, Any]]:
    urls: list[str] = []
    for frame in page.frames:
        try:
            for u in await frame.evaluate(_MEDIA_JS):
                # Requests never carry the #fragment (#t=8,10): keyed without
                # it, so the range route matches and the media can seek.
                u = u.split("#", 1)[0]
                if u not in urls:
                    urls.append(u)
        except Exception:
            continue
    cap_mb, cap_s = settings.media_cap_mb, settings.media_cap_s
    left = None if cap_mb is None else int(cap_mb * 1_000_000)
    deadline = None if cap_s is None else time.monotonic() + cap_s
    out: list[dict[str, Any]] = []
    for n, url in enumerate(urls[:20]):
        entry: dict[str, Any] = {"url": url, "file": None, "size": None, "type": ""}
        out.append(entry)
        entry["size"], entry["type"] = await _media_size(ctx, url)
        if left is not None and (entry["size"] is None or entry["size"] > left):
            entry["over_cap"] = True  # unknown size counts as over a cap
            continue
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            entry["over_cap"] = True
            continue
        try:
            got = await ctx.request.get(
                url, timeout=int(1000 * remaining) if remaining else 0
            )
            body = await got.body()
        except Exception as exc:
            entry["over_cap"] = True  # too slow within the cap, or failed
            log("media_store", "error", n=n, error=type(exc).__name__)
            continue
        if not got.ok:
            entry["status"] = got.status
            continue
        if left is not None and len(body) > left:
            entry["over_cap"] = True
            continue
        if left is not None:
            left -= len(body)
        entry.update(
            file=f"a11y-media-{n}.bin",
            size=len(body),
            type=got.headers.get("content-type", entry["type"]),
            body=body,
        )
        log("media_store", n=n, bytes=len(body))
    return out


def _add_media(har_path: Path, media: list[dict[str, Any]]) -> None:
    if not media:
        return
    with zipfile.ZipFile(har_path, "a") as z:
        for m in media:
            if m.get("body") is not None:
                z.writestr(m["file"], m["body"])
        z.writestr(
            MEDIA_INDEX,
            json.dumps([{k: v for k, v in m.items() if k != "body"} for m in media]),
        )


def media_index(har_path: Path) -> list[dict[str, Any]]:
    """The media store's index in a recording ([] when it has none)."""
    try:
        with zipfile.ZipFile(har_path) as z:
            return json.loads(z.read(MEDIA_INDEX))
    except (KeyError, OSError, ValueError, zipfile.BadZipFile):
        return []


def media_body(har_path: Path, url: str) -> bytes | None:
    """A media file's bytes: from the media store, else the HAR's own body."""
    url = url.split("#", 1)[0]
    try:
        with zipfile.ZipFile(har_path) as z:
            for m in media_index(har_path):
                if m["url"] == url and m.get("file"):
                    return z.read(m["file"])
            name = next(n for n in z.namelist() if n.endswith(".har"))
            for e in json.loads(z.read(name))["log"]["entries"]:
                if e["request"]["url"] != url or e["response"].get("status") != 200:
                    continue
                c = e["response"].get("content", {})
                if c.get("_file"):
                    return z.read(c["_file"])
    except (KeyError, OSError, ValueError, StopIteration, zipfile.BadZipFile):
        return None
    return None


async def _serve_media(ctx: BrowserContext, har_path: Path) -> None:
    """Answer byte-range requests for stored media (after route_from_har)."""
    stored = {m["url"]: m for m in media_index(har_path) if m.get("file")}
    if not stored:
        return
    cache: dict[str, bytes] = {}

    async def serve(route) -> None:
        m = stored[route.request.url]
        if m["url"] not in cache:
            with zipfile.ZipFile(har_path) as z:
                cache[m["url"]] = z.read(m["file"])
        body = cache[m["url"]]
        total = len(body)
        headers = {"Accept-Ranges": "bytes", "Content-Type": m.get("type") or ""}
        rng = route.request.headers.get("range", "")
        hit = re.match(r"bytes=(\d*)-(\d*)", rng)
        if hit and (hit.group(1) or hit.group(2)):
            a = int(hit.group(1)) if hit.group(1) else max(0, total - int(hit.group(2)))
            b = int(hit.group(2)) if hit.group(1) and hit.group(2) else total - 1
            b = min(b, total - 1)
            if a > b:
                await route.fulfill(
                    status=416, headers={"Content-Range": f"bytes */{total}"}
                )
                return
            headers["Content-Range"] = f"bytes {a}-{b}/{total}"
            await route.fulfill(status=206, headers=headers, body=body[a : b + 1])
            return
        await route.fulfill(status=200, headers=headers, body=body)

    await ctx.route(lambda url: url in stored, serve)


def _host(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def cross_site_frames(top_url: str, frame_urls: list[str]) -> list[str]:
    """Frame URLs (query and fragment dropped) on another host than the top
    page. Another host is wider than Chrome's "site" (same registrable
    domain), so a same-site subdomain also counts: that only costs a slower
    replay, never a different one. about:blank, data: and srcdoc frames share
    the parent's process and are skipped."""
    top = _host(top_url)
    out = {
        safe_url(u)
        for u in frame_urls
        if u.startswith(("http:", "https:")) and _host(u) not in ("", top)
    }
    return sorted(out)[:MAX_FRAMES_KEPT]


def _failed_urls(har_path: Path) -> set[str]:
    """URLs the HAR recorded with no response (status -1)."""
    with zipfile.ZipFile(har_path) as z:
        name = next(n for n in z.namelist() if n.endswith(".har"))
        entries = json.loads(z.read(name))["log"]["entries"]
    return {e["request"]["url"] for e in entries if e["response"].get("status", 0) < 0}


async def _idle(page, log: LogFn, timeout_ms: int) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        log("capture_networkidle_timeout", "info", timeout_ms=timeout_ms)


@dataclass
class Replay:
    context: BrowserContext
    guard: NavigationGuard
    andi_aborted: list[str] | None  # None when ANDI routes are not installed


async def replay_context(
    browser: Browser,
    settings: Settings,
    har_path: Path,
    log: LogFn,
    with_andi: bool = False,
    init_scripts: tuple[str, ...] = (),
) -> Replay:
    """A fresh context that answers only from the HAR (unknown URLs abort).

    `init_scripts` run in every frame after INIT_JS and before page scripts
    (pass T's hooks, motion.py; plan Q7): INIT_JS stays the same for every
    other load."""
    ctx = await new_context(browser, settings)
    await ctx.add_init_script(INIT_JS)  # focus and mutation log (settle rule)
    for script in init_scripts:
        await ctx.add_init_script(script)
    await ctx.route_from_har(str(har_path), not_found="abort")
    failed = _failed_urls(har_path)
    if failed:
        # Requests that failed while recording (refused by the egress proxy,
        # DNS errors) are saved with status -1, and Playwright's HAR replay
        # waits on them forever. Fail them, as they failed live. Registered
        # after route_from_har, so it runs first.
        async def fail(route) -> None:
            await route.abort("failed")

        await ctx.route(lambda url: url in failed, fail)
    await _serve_media(ctx, har_path)  # after route_from_har: runs first
    andi_aborted = None
    if with_andi:
        andi_aborted = await install_andi_routes(ctx, settings.third_party_dir)
    guard = NavigationGuard(settings, live=False, log=log)
    await guard.install(ctx)  # last registered runs first
    return Replay(ctx, guard, andi_aborted)
