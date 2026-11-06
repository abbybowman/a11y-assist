"""Freeze a round's tested pages once, for both arms of the agent eval
(docs/plans/2026-10-31-agent-eval.md section 6).

    uv run python -m evals.agent.freeze evals/judging/<round>

(headless: BROWSER_CHANNEL=chromium HEADLESS=true; --accept-suspect calls a
recording frozen even when it looks broken: a 404 page, or most of its CSS,
fonts and scripts missing)

Each page in <round>/pages.txt is recorded once, as a live run records it
(capture.record: the allowlist and every redirect hop checked, scrolled to
load lazy content), into <round>/frozen/ (index.json, the recordings and
freeze.json). Nothing else is recorded: during the arms, other pages of the
tested site (site maps, search results, any route an agent tries) load live
for both arms, and the tested pages come only from these copies.

This step touches the live site, close to the tester's own testing; compare
each page's footer timestamp with the tester's after freezing.
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

from a11y_assist.browser import launch_browser
from a11y_assist.config import Settings
from a11y_assist.egress import EgressProxy
from a11y_assist.frozen import load, obtain
from a11y_assist.policy import check_url
from a11y_assist.redact import safe_error
from evals.judging import JudgingError, _pages

FROZEN = "frozen"
ASSET_TYPES = ("stylesheet", "script", "font")
MOST = 0.5  # more than half the CSS, font and script requests failed


def _kind(e: dict) -> str | None:
    t = (e.get("_resourceType") or "").lower()
    if t in ASSET_TYPES:
        return t
    mime = (e.get("response", {}).get("content", {}).get("mimeType") or "").lower()
    url = e.get("request", {}).get("url", "").split("?")[0].lower()
    if "css" in mime or url.endswith(".css"):
        return "stylesheet"
    if "javascript" in mime or url.endswith((".js", ".mjs")):
        return "script"
    if "font" in mime or url.endswith((".woff", ".woff2", ".ttf", ".otf")):
        return "font"
    return None


def check_recording(har_zip: Path, final_url: str) -> dict:
    """What a frozen page's recording holds (post-round 1 fix 7: a typo
    froze a 404 page, and a page frozen in the cloud container had its HTML
    but none of its CSS or scripts; both reached the agents). Returns the
    main document's status, the CSS, font and script requests and how many
    failed, the title and first heading, and `suspect` with the reason."""
    import html
    import re
    import zipfile

    with zipfile.ZipFile(har_zip) as z:
        name = next(n for n in z.namelist() if n.endswith(".har"))
        entries = json.loads(z.read(name))["log"]["entries"]

        def body(e: dict) -> str:
            c = e.get("response", {}).get("content", {})
            if c.get("text") is not None:
                return c["text"]
            f = c.get("_file")
            return z.read(f).decode("utf-8", "replace") if f in z.namelist() else ""

        want = final_url.split("#")[0].rstrip("/")
        doc = next(
            (
                e
                for e in entries
                if e["request"]["url"].split("#")[0].rstrip("/") == want
                and e["response"].get("status", 0) not in (301, 302, 303, 307, 308)
            ),
            None,
        )
        text = body(doc) if doc else ""
    assets = [e for e in entries if _kind(e)]
    failed = [e for e in assets if not 200 <= e["response"].get("status", -1) < 400]

    def first(pattern: str) -> str:
        m = re.search(pattern, text, re.I | re.S)
        raw = re.sub(r"<[^>]+>", " ", m.group(1)) if m else ""
        return html.unescape(re.sub(r"\s+", " ", raw)).strip()[:120]

    status = doc["response"].get("status") if doc else None
    out = {
        "document_status": status,
        "assets": len(assets),
        "assets_failed": len(failed),
        "title": first(r"<title[^>]*>(.*?)</title>"),
        "heading": first(r"<h1[^>]*>(.*?)</h1>"),
    }
    if status is None or not 200 <= status < 300:
        out["suspect"] = f"the page itself answered {status}"
    elif assets and len(failed) > MOST * len(assets):
        out["suspect"] = (
            f"{len(failed)} of {len(assets)} CSS, font and script requests failed"
        )
    return out


async def freeze(rd: Path, settings: Settings, accept: bool = False) -> dict:
    if (rd / "results" / "lock.json").exists():
        raise JudgingError("This round is locked")
    folder = rd / FROZEN
    s = settings.model_copy(
        update={"frozen_pages_dir": folder, "frozen_pages_mode": "record_missing"}
    )
    pages = [u for u, _ in _pages(rd)]
    log: dict = {"started_at": datetime.now(timezone.utc).isoformat(), "pages": {}}
    async with EgressProxy(s) as proxy, async_playwright() as pw:
        browser = await launch_browser(pw, s, proxy)
        try:
            for url in pages:
                t0 = time.monotonic()
                entry: dict = {}
                print(f"freezing {url}", flush=True)
                decision = check_url(url, s.allowed_domains, s.dev_mode)
                try:
                    if not decision.allowed:
                        raise ValueError(f"not allowed: {decision.reason}")
                    with tempfile.TemporaryDirectory() as tmp:
                        cap = await obtain(
                            browser,
                            s,
                            url,
                            Path(tmp) / "page.har.zip",
                            lambda *a, **k: None,
                            proxy,
                        )
                    entry.update(
                        status="frozen",
                        final_url=cap.final_url,
                        cross_site_frames=len(cap.cross_site_frames),
                    )
                    rec = load(folder).get(url)
                    if rec is not None:
                        entry.update(check_recording(folder / rec.har, cap.final_url))
                    if entry.get("suspect") and not accept:
                        entry["status"] = "suspect"
                except Exception as exc:  # recorded: the arms are refused it
                    entry.update(status="error", error=safe_error(exc)[:300])
                entry["seconds"] = round(time.monotonic() - t0, 1)
                log["pages"][url] = entry
        finally:
            await browser.close()
    folder.mkdir(parents=True, exist_ok=True)
    log["finished_at"] = datetime.now(timezone.utc).isoformat()
    log["recordings"] = len(load(folder))
    (folder / "freeze.json").write_text(json.dumps(log, indent=1) + "\n")
    return log


def main(argv: list[str]) -> None:
    accept = "--accept-suspect" in argv
    argv = [a for a in argv if a != "--accept-suspect"]
    if len(argv) != 1:
        sys.exit(__doc__)
    log = asyncio.run(freeze(Path(argv[0]), Settings(), accept))
    for u, e in log["pages"].items():
        print(
            f"{u}: {e['status']}; {e.get('document_status')}; "
            f"{e.get('assets_failed')} of {e.get('assets')} CSS/font/script failed; "
            f"title {e.get('title')!r}; heading {e.get('heading')!r}"
            + (f"; SUSPECT: {e['suspect']}" if e.get("suspect") else "")
        )
    bad = [u for u, e in log["pages"].items() if e["status"] != "frozen"]
    print(f"{log['recordings']} recordings; pages not frozen: {bad or 'none'}")
    if any(e["status"] == "suspect" for e in log["pages"].values()):
        sys.exit(
            "Some recordings look broken (above). Check them, freeze again, or "
            "rerun with --accept-suspect to call them frozen anyway."
        )


if __name__ == "__main__":
    main(sys.argv[1:])
