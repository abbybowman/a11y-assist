"""Collect the versions recorded in every report."""

from __future__ import annotations

import asyncio
import platform
from importlib.metadata import version
from typing import Any

from playwright.async_api import Browser

from a11y_assist import __version__
from a11y_assist.andi import provenance
from a11y_assist.browser import new_context
from a11y_assist.config import Settings
from a11y_assist.models import Versions
from a11y_assist.rules import spec_versions


def collect_versions(
    settings: Settings, browser: Browser | None, no_time_limit: bool = False
) -> Versions:
    prov = provenance(settings.third_party_dir)
    return Versions(
        a11y_assist=__version__,
        andi=f"{prov['andi']['version']} ({prov['andi']['commit'][:12]})",
        jquery=prov["jquery"]["version"],
        scrt=f"{prov['scrt']['version'].split(' ')[0]} ({prov['scrt']['commit'][:12]})",
        playwright=version("playwright"),
        browser_channel=settings.browser_channel,
        browser=browser.version if browser else None,
        os=platform.platform(),
        python=platform.python_version(),
        rules_spec=spec_versions(settings.rules_dir),
        judging_model=settings.judging_model,
        display=configured_display(settings),
        run_settings={
            "settle_quiet_ms": settings.settle_quiet_ms,
            "record_scroll_passes": settings.record_scroll_passes,
            "run_limit_s": settings.run_limit_s,
            "other_page_s": settings.other_page_s,
            # The caller turned the run limit off for this run (a11y_run_tt_tests).
            "no_time_limit": no_time_limit,
        },
    )


def configured_display(settings: Settings) -> dict[str, int | float | None]:
    return {
        "viewport_width": settings.viewport_width,
        "viewport_height": settings.viewport_height,
        "inner_width": None,
        "inner_height": None,
        "device_pixel_ratio": None,
    }


_DISPLAY_JS = "() => [innerWidth, innerHeight, devicePixelRatio]"


async def measure_display(
    settings: Settings, browser: Browser, timeout_s: float = 5.0
) -> dict[str, int | float | None]:
    """The configured viewport plus what a blank page in a fresh context of
    `browser` reports. No page is loaded (about:blank); on any failure the
    measured values stay None."""
    out = configured_display(settings)
    ctx: Any = None
    try:
        async with asyncio.timeout(timeout_s):
            ctx = await new_context(browser, settings)
            page = await ctx.new_page()
            w, h, dpr = await page.evaluate(_DISPLAY_JS)
            out.update(inner_width=int(w), inner_height=int(h))
            out["device_pixel_ratio"] = float(dpr)
    except Exception:
        pass
    finally:
        if ctx is not None:
            try:
                await asyncio.wait_for(ctx.close(), timeout_s)
            except Exception:
                pass
    return out
