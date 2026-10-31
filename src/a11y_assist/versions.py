"""Collect the versions recorded in every report."""

from __future__ import annotations

import platform
from importlib.metadata import version

from playwright.async_api import Browser

from a11y_assist import __version__
from a11y_assist.andi import provenance
from a11y_assist.config import Settings
from a11y_assist.models import Versions
from a11y_assist.rules import spec_versions


def collect_versions(settings: Settings, browser: Browser | None) -> Versions:
    prov = provenance(settings.third_party_dir)
    return Versions(
        a11y_assist=__version__,
        andi=f"{prov['andi']['version']} ({prov['andi']['commit'][:12]})",
        jquery=prov["jquery"]["version"],
        playwright=version("playwright"),
        browser_channel=settings.browser_channel,
        browser=browser.version if browser else None,
        os=platform.platform(),
        python=platform.python_version(),
        rules_spec=spec_versions(settings.rules_dir),
        judging_model=settings.judging_model,
        run_settings={
            "settle_quiet_ms": settings.settle_quiet_ms,
            "record_scroll_passes": settings.record_scroll_passes,
            "run_limit_s": settings.run_limit_s,
        },
    )
