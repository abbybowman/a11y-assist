"""URL allowlist for top-level navigations.

Pure functions only, so the policy is easy to test without a browser. The
browser module calls `check_url` for every top-level navigation and every
redirect hop.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class UrlDecision:
    allowed: bool
    reason: str


def _host_matches(host: str, entry: str) -> bool:
    entry = entry.strip().lower().rstrip(".")
    if not entry:
        return False
    if entry.startswith("."):
        return host.endswith(entry) or host == entry[1:]
    return host == entry


def check_url(url: str, allowed_domains: list[str], dev_mode: bool) -> UrlDecision:
    """Decide whether a top-level navigation to `url` is allowed."""
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return UrlDecision(False, "unparseable URL")

    scheme = parts.scheme.lower()
    if scheme == "about" and url == "about:blank":
        return UrlDecision(True, "about:blank")
    if scheme == "file":
        if dev_mode:
            return UrlDecision(True, "file:// allowed in dev mode")
        return UrlDecision(False, "file:// is allowed only in dev mode")
    if scheme not in ("http", "https"):
        return UrlDecision(False, f"scheme {scheme!r} is not allowed")
    if not host:
        return UrlDecision(False, "URL has no host")
    if parts.username is not None or parts.password is not None:
        return UrlDecision(False, "URLs with embedded credentials are not allowed")
    for entry in allowed_domains:
        if _host_matches(host, entry):
            return UrlDecision(True, f"host {host!r} matches {entry!r}")
    return UrlDecision(False, f"host {host!r} is not in the allowlist")
