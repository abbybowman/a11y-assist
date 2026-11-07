"""Chrome via Playwright, plus the top-level navigation guard.

Verified behavior this module depends on (see tests/test_browser.py):
  * A context route sees the first request of a navigation, including file://
    navigations, but NOT the redirect hops the browser follows afterwards. Even
    fulfilling a 3xx from a route lets the browser follow the chain unrouted.
  * So in live mode the guard fetches each top-level navigation itself with
    max_redirects=0. On a 3xx it serves a stub page instead and `goto` checks
    the Location against the allowlist before navigating there. Every hop is
    checked before any request is sent to it.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from urllib.parse import urljoin, urlsplit

from playwright.async_api import Browser, BrowserContext, Page, Playwright, Route

from tobi508.config import Settings
from tobi508.egress import EgressProxy
from tobi508.policy import check_url
from tobi508.redact import safe_error, safe_url

REDIRECT_STUB = (
    "<!doctype html><title>tobi508 redirect hold</title>"
    "<!-- redirect held by tobi508 for an allowlist check -->"
)

LogFn = Callable[..., None]


class NavigationBlocked(RuntimeError):
    """A top-level navigation was refused by the allowlist or the egress
    proxy's address check."""


class PageUnreachable(RuntimeError):
    """A top-level navigation's host could not be connected to."""


FULL_CHROMIUM = "full Chromium"
# TT 5.1.3's setup: a browser "not set to block autoplay". Without it, media
# in a HAR replay never starts (2.A-2.D plan, item 1). Only pass T's browser
# gets it, so the walk and every other test see the page as before (Q1).
AUTOPLAY_ARG = "--autoplay-policy=no-user-gesture-required"
MOTION_BROWSER = "full Chromium, headless, autoplay allowed"


def replay_in_full_chromium(settings: Settings, cross_site_frames: list[str]) -> bool:
    """Replays of a page with cross-site iframes run in full Chromium, never
    the headless shell: the shell runs those frames in-process, unlike the
    Chrome users have (docs/solutions/full-chromium-iframes.md). Installed
    Chrome already runs them out-of-process, and headed "chromium" is
    already full Chromium."""
    return (
        settings.browser_channel == "chromium"
        and settings.headless
        and bool(cross_site_frames)
    )


def replay_browser_name(settings: Settings, cross_site_frames: list[str]) -> str:
    """What the report records as the browser that replays a page."""
    if replay_in_full_chromium(settings, cross_site_frames):
        return FULL_CHROMIUM
    if settings.browser_channel == "chromium":
        return "headless shell" if settings.headless else FULL_CHROMIUM
    return settings.browser_channel


async def launch_browser(
    pw: Playwright,
    settings: Settings,
    proxy: EgressProxy,
    full_chromium: bool = False,
    extra_args: tuple[str, ...] = (),
    headless: bool | None = None,
) -> Browser:
    """Chrome whose only way out is `proxy` (egress.py), which checks the
    address of every connection. There is no unproxied launch.

    `full_chromium` launches Playwright's full Chromium (new headless mode)
    instead of the configured browser; see replay_in_full_chromium.
    `extra_args` and `headless` serve pass T's browser (launch_for)."""
    if not proxy.url:
        raise RuntimeError("The egress proxy is not running")
    if full_chromium:
        channel = "chromium"
    else:
        channel = (
            None if settings.browser_channel == "chromium" else settings.browser_channel
        )
    return await pw.chromium.launch(
        channel=channel,
        headless=settings.headless if headless is None else headless,
        args=[
            *settings.browser_args,
            *extra_args,
            # No UDP outside the proxy (WebRTC could otherwise reach any address).
            "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
        ],
        # Playwright adds <-loopback>, so loopback goes through the proxy too.
        proxy={"server": proxy.url},
    )


async def launch_for(
    pw: Playwright, settings: Settings, proxy: EgressProxy, full: bool, autoplay: bool
) -> Browser:
    """The browser for one kind of load: the configured browser, full
    Chromium (cross-site frames, Q11), or pass T's (autoplay: full Chromium,
    always headless so a headed run's walk keeps its window and focus, Q1)."""
    if autoplay:
        return await launch_browser(
            pw, settings, proxy, True, (AUTOPLAY_ARG,), headless=True
        )
    return await launch_browser(pw, settings, proxy, full_chromium=full)


async def new_context(
    browser: Browser, settings: Settings, **kwargs: Any
) -> BrowserContext:
    """A fresh, isolated context. Service workers are blocked so routes see all.
    `viewport` may be given (3.A's flash capture is 1024 x 768); the page's
    Content-Security-Policy is bypassed when `settings.bypass_csp` is on."""
    kwargs.setdefault(
        "viewport",
        {"width": settings.viewport_width, "height": settings.viewport_height},
    )
    kwargs.setdefault("bypass_csp", settings.bypass_csp)  # ANDI (config)
    ctx = await browser.new_context(service_workers="block", **kwargs)
    ctx.set_default_navigation_timeout(settings.navigation_timeout_ms)
    return ctx


def _is_top_level_navigation(route: Route) -> bool:
    request = route.request
    if not request.is_navigation_request():
        return False
    try:
        return request.frame.parent_frame is None
    except Exception:  # no frame (e.g. worker); treat as top level to be safe
        return True


class NavigationGuard:
    """Enforces the allowlist on every top-level navigation in a context.

    live=True:  navigations are fetched by the guard so redirects can be held.
    live=False: replay mode; allowed navigations fall through to the HAR route.

    Register the guard AFTER any other routes: Playwright runs the most
    recently registered matching route first.
    """

    def __init__(
        self,
        settings: Settings,
        live: bool,
        log: LogFn | None = None,
        egress: EgressProxy | None = None,
    ):
        self.settings = settings
        self.live = live
        # The proxy this context's browser uses: a top-level fetch it refused
        # comes back as an ordinary 403 response, so the guard checks its
        # refusal list and blocks the navigation instead of serving that page.
        self.egress = egress
        self._log = log or (lambda *a, **k: None)
        self.blocked: list[dict[str, str]] = []
        self.unreachable: dict[str, str] = {}
        self.redirects: list[dict[str, Any]] = []
        self._pending_redirect: str | None = None

    async def install(self, context: BrowserContext) -> None:
        await context.route("**", self._handle)

    def _check(self, url: str) -> bool:
        decision = check_url(url, self.settings.allowed_domains, self.settings.dev_mode)
        if not decision.allowed:
            self.blocked.append({"url": url, "reason": decision.reason})
            self._log("navigation_blocked", "blocked", url=url, reason=decision.reason)
        return decision.allowed

    async def _handle(self, route: Route) -> None:
        url = route.request.url
        if url.startswith("file:"):
            # file:// is never in a HAR. Top-level file:// is policy-checked;
            # file:// subresources are only reachable from an allowed file page.
            if _is_top_level_navigation(route) and not self._check(url):
                return await route.abort("blockedbyclient")
            return await route.continue_()
        if not _is_top_level_navigation(route):
            return await route.fallback()
        if not self._check(url):
            return await route.abort("blockedbyclient")
        if not self.live:
            return await route.fallback()

        seen = len(self.egress.refused) if self.egress is not None else 0
        try:
            response = await route.fetch(max_redirects=0)
        except Exception as exc:
            # An exception escaping a route handler is printed to stderr with
            # Playwright's call log (full URL and headers). Log one redacted
            # line instead and fail the navigation.
            self._log("navigation_fetch_failed", "error", error=safe_error(exc))
            return await route.abort("failed")
        refusal = self._egress_refusal(url, seen)
        if refusal is not None:
            reason, policy = refusal
            if not policy:
                self.unreachable[url] = reason
                self._log("navigation_unreachable", "error", url=url, reason=reason)
                return await route.abort("connectionrefused")
            self.blocked.append({"url": url, "reason": reason})
            self._log("navigation_blocked", "blocked", url=url, reason=reason)
            return await route.abort("blockedbyclient")
        location = response.headers.get("location")
        if 300 <= response.status < 400 and location:
            target = urljoin(url, location)
            self._pending_redirect = target
            self.redirects.append(
                {"from": url, "status": response.status, "to": target}
            )
            self._log("redirect_held", "info", http_status=response.status, to=target)
            return await route.fulfill(
                status=200, content_type="text/html", body=REDIRECT_STUB
            )
        await route.fulfill(response=response)

    def _egress_refusal(self, url: str, since: int) -> tuple[str, bool] | None:
        if self.egress is None:
            return None
        parts = urlsplit(url)
        port = parts.port or (443 if parts.scheme == "https" else 80)
        for r in self.egress.refused[since:]:
            if r["host"] == parts.hostname and r["port"] == port:
                return f"{r['host']} {r['reason']}", r["policy"]
        return None

    async def goto(self, page: Page, url: str) -> str:
        """Navigate, following redirects only to allowed URLs. Returns final URL."""
        for _ in range(self.settings.max_redirects + 1):
            if not self._check(url):
                raise NavigationBlocked(
                    f"Navigation to {safe_url(url)} blocked: "
                    f"{self.blocked[-1]['reason']}"
                )
            self._pending_redirect = None
            try:
                await page.goto(url, wait_until="load")
            except Exception:
                if url in self.unreachable:
                    raise PageUnreachable(
                        f"{safe_url(url)}: {self.unreachable[url]}"
                    ) from None
                if self.blocked and self.blocked[-1]["url"] == url:
                    raise NavigationBlocked(
                        f"Navigation to {safe_url(url)} blocked: "
                        f"{self.blocked[-1]['reason']}"
                    ) from None
                raise
            if self._pending_redirect is None:
                return page.url
            url = self._pending_redirect
        raise NavigationBlocked(f"More than {self.settings.max_redirects} redirects")
