"""Frozen pages: a folder of recordings made once, replayed by every run
(the agent eval, docs/plans/2026-10-31-agent-eval.md section 6).

`index.json` maps each URL as requested to its recording. A page is
recorded by `capture.record`, under the same allowlist and redirect checks
as a live run, so a frozen copy is what a live run would have seen. URLs
match exactly, without the fragment.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urlsplit

from pydantic import BaseModel, Field

from a11y_assist.browser import LogFn
from a11y_assist.capture import Capture, record
from a11y_assist.config import Settings
from a11y_assist.egress import EgressProxy
from a11y_assist.redact import safe_url

INDEX = "index.json"


class NotFrozen(RuntimeError):
    """The server replays frozen pages only, and this URL has no recording."""


class FrozenPage(BaseModel):
    url: str
    final_url: str
    har: str = Field(description="Path relative to the frozen pages folder.")
    redirects: list[dict[str, Any]] = Field(default_factory=list)
    cross_site_frames: list[str] = Field(default_factory=list)
    recorded_at: str


def _key(url: str) -> str:
    return urldefrag(url)[0]


def load(folder: Path) -> dict[str, FrozenPage]:
    f = folder / INDEX
    if not f.exists():
        return {}
    raw = json.loads(f.read_text("utf-8"))
    return {k: FrozenPage.model_validate(v) for k, v in raw.items()}


def _save(folder: Path, index: dict[str, FrozenPage]) -> None:
    tmp = folder / (INDEX + ".tmp")
    data = {k: v.model_dump() for k, v in sorted(index.items())}
    tmp.write_text(json.dumps(data, indent=1) + "\n", "utf-8")
    tmp.replace(folder / INDEX)


def _host(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


async def obtain(
    browser,
    settings: Settings,
    url: str,
    har_path: Path,
    log: LogFn,
    egress: EgressProxy | None = None,
    tested: bool = True,
) -> Capture:
    """`capture.record`, or the frozen recording of `url` when the server
    has frozen pages. The HAR lands at `har_path` either way. `tested` is
    False for other pages and 19.A's search: in "tested_frozen" mode those
    are recorded live when they are on a frozen page's host."""
    folder = settings.frozen_pages_dir
    if folder is None:
        return await record(browser, settings, url, har_path, log, egress)
    index = load(folder)
    hit = index.get(_key(url))
    if hit is not None:
        shutil.copyfile(folder / hit.har, har_path)
        log("frozen_page", url=safe_url(url), har=hit.har)
        return Capture(
            url,
            hit.final_url,
            har_path,
            hit.redirects,
            hit.cross_site_frames,
            frozen=True,
        )
    mode = settings.frozen_pages_mode
    if mode == "tested_frozen" and not tested:
        hosts = {_host(p.url) for p in index.values()} | {
            _host(p.final_url) for p in index.values()
        }
        if _host(url) in hosts:
            log("frozen_page", url=safe_url(url), live=True)
            return await record(browser, settings, url, har_path, log, egress)
        log("frozen_page", "error", url=safe_url(url), error="not the tested site")
        raise NotFrozen(
            "This server tests frozen copies of pages; other pages may be "
            f"loaded live only from the tested site, not {safe_url(url)}."
        )
    if mode in ("replay", "tested_frozen"):
        log("frozen_page", "error", url=safe_url(url), error="no recording")
        raise NotFrozen(
            "This server tests frozen copies of pages only, and has no "
            f"recording of {safe_url(url)}."
        )
    cap = await record(browser, settings, url, har_path, log, egress)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "pages").mkdir(exist_ok=True)
    rel = f"pages/{len(index) + 1:03d}.har.zip"
    shutil.copyfile(har_path, folder / rel)
    index = load(folder)  # unchanged unless another writer ran; keep theirs
    index[_key(url)] = FrozenPage(
        url=_key(url),
        final_url=cap.final_url,
        har=rel,
        redirects=cap.redirects,
        cross_site_frames=cap.cross_site_frames,
        recorded_at=datetime.now(timezone.utc).isoformat(),
    )
    _save(folder, index)
    log("frozen_page", url=safe_url(url), har=rel, recorded=True)
    return cap
