"""Record a page to HAR once, then replay it so every test run sees the same
network responses.

A HAR freezes network responses only. Client-side randomness or the clock can
still vary between replays.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext

from a11y_assist.andi import install_andi_routes
from a11y_assist.browser import LogFn, NavigationGuard, new_context
from a11y_assist.config import Settings
from a11y_assist.traverse import INIT_JS


@dataclass
class Capture:
    target_url: str
    final_url: str
    har_path: Path
    redirects: list[dict[str, Any]] = field(default_factory=list)


async def record(
    browser: Browser, settings: Settings, url: str, har_path: Path, log: LogFn
) -> Capture:
    """Load `url` live in a fresh context and save every response to `har_path`."""
    ctx = await new_context(
        browser, settings, record_har_path=str(har_path), record_har_mode="full"
    )
    guard = NavigationGuard(settings, live=True, log=log)
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
    finally:
        await ctx.close()  # writes the HAR
    return Capture(url, final_url, har_path, guard.redirects)


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
) -> Replay:
    """A fresh context that answers only from the HAR (unknown URLs abort)."""
    ctx = await new_context(browser, settings)
    await ctx.add_init_script(INIT_JS)  # focus and mutation log (settle rule)
    await ctx.route_from_har(str(har_path), not_found="abort")
    andi_aborted = None
    if with_andi:
        andi_aborted = await install_andi_routes(ctx, settings.third_party_dir)
    guard = NavigationGuard(settings, live=False, log=log)
    await guard.install(ctx)  # last registered runs first
    return Replay(ctx, guard, andi_aborted)
