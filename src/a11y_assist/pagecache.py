"""Other pages of the same site, recorded and read once per server session
(Abby, 2026-11-06; the plan's observation "other pages are read again on
every call").

An agent testing several pages of one site passes the same other pages
(home page, site map) on every call. Each call recorded each of them again
(about 20 s each for a live page) and read each again (the page read for
9.A-9.C and 19.A, and 9.C's ANDI read, 10-20 s). Now:

- a recording of an other page made in the last `page_cache_s` seconds
  (default 1800) is copied into the new run instead of recording the page
  again; the run's report says it was reused and when it was recorded;
- a page read or ANDI read of a recording is kept by the recording's
  SHA-256, so the same recording is never read twice.

Each run still keeps its own copy of every recording in its evidence, so a
run stays complete on its own. The cache lives in this process's memory
(and its recordings in `runs/_page_cache/`, pruned like runs): a restart
empties it. `page_cache_s = 0` turns it off. No outcome is decided here.
"""

from __future__ import annotations

import hashlib
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from a11y_assist.config import Settings


@dataclass
class Recording:
    path: Path
    final_url: str
    cross_site_frames: list[str] = field(default_factory=list)
    frozen: bool = False
    recorded_at: float = field(default_factory=time.time)


_RECORDINGS: dict[tuple, Recording] = {}
_READS: dict[tuple[str, str], Any] = {}


def _key(settings: Settings, url: str) -> tuple:
    # A frozen-pages folder and mode give other pages a different source.
    return (url, str(settings.frozen_pages_dir), settings.frozen_pages_mode)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def reused(settings: Settings, url: str, dest: Path) -> Recording | None:
    """Copy a recent recording of `url` to `dest` and return it, or None."""
    if settings.page_cache_s <= 0:
        return None
    hit = _RECORDINGS.get(_key(settings, url))
    if hit is None or time.time() - hit.recorded_at > settings.page_cache_s:
        return None
    if not hit.path.is_file():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(hit.path, dest)
    return hit


def keep(
    settings: Settings,
    url: str,
    har: Path,
    final_url: str,
    cross_site_frames: list[str],
    frozen: bool,
) -> None:
    """Remember a fresh recording of an other page."""
    if settings.page_cache_s <= 0 or not har.is_file():
        return
    folder = settings.runs_dir / "_page_cache"
    folder.mkdir(parents=True, exist_ok=True)
    copy = folder / f"{sha256(har)}.har.zip"
    if not copy.exists():
        shutil.copyfile(har, copy)
    _RECORDINGS[_key(settings, url)] = Recording(
        copy, final_url, list(cross_site_frames), frozen
    )


def read(kind: str, har_sha: str | None) -> Any | None:
    """A read of this recording kept earlier (`kind`: "site", "andi")."""
    if not har_sha:
        return None
    return _READS.get((kind, har_sha))


def keep_read(kind: str, har_sha: str | None, value: Any) -> None:
    if har_sha and not getattr(value, "error", None):
        _READS[(kind, har_sha)] = value


def clear() -> None:
    """Empty the cache (tests)."""
    _RECORDINGS.clear()
    _READS.clear()
