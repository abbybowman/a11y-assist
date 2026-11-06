"""ANDI injection from local files, verified in a real browser.

The browser here uses a proxy on a closed port, so any request that is not
fulfilled locally by a route fails. ANDI fully loading proves that its CSS,
module script, icons and jQuery came from third_party/, not the network.
"""

from __future__ import annotations

import pytest_asyncio
from playwright.async_api import async_playwright

from tobi508.andi import ANDI_HOST_URL, inject_andi, install_andi_routes
from tobi508.browser import NavigationGuard, new_context
from tobi508.capture import record, replay_context

from .conftest import FIXTURES, noop_log

DEAD_PROXY = {"server": "http://127.0.0.1:9", "bypass": "<-loopback>"}


@pytest_asyncio.fixture
async def offline_browser(settings):
    channel = (
        None if settings.browser_channel == "chromium" else settings.browser_channel
    )
    async with async_playwright() as pw:
        b = await pw.chromium.launch(
            channel=channel, headless=settings.headless, proxy=DEAD_PROXY
        )
        yield b
        await b.close()


async def _assert_andi_fully_loaded(page, settings, aborted, failed):
    version = await inject_andi(page, settings.third_party_dir)
    assert version == "29.2.2"
    await page.wait_for_function(
        "window.AndiModule && document.getElementById('andiModuleScript')"
    )
    state = await page.evaluate(
        """() => ({
            jq: window.jQuery && jQuery.fn.jquery,
            module: AndiModule.module,
            cssApplied: getComputedStyle(document.getElementById('ANDI508')).position,
        })"""
    )
    assert state == {"jq": "3.7.1", "module": "f", "cssApplied": "fixed"}
    assert aborted == []
    assert failed == []


async def test_andi_injects_on_file_page_without_network(offline_browser, settings):
    ctx = await new_context(offline_browser, settings)
    aborted = await install_andi_routes(ctx, settings.third_party_dir)
    guard = NavigationGuard(settings, live=False, log=noop_log)
    await guard.install(ctx)
    page = await ctx.new_page()
    requested, failed = [], []
    page.on("request", lambda r: requested.append(r.url))
    page.on("requestfailed", lambda r: failed.append(r.url))

    await guard.goto(page, (FIXTURES / "no_trap.html").as_uri())
    await _assert_andi_fully_loaded(page, settings, aborted, failed)
    andi_requests = [u for u in requested if u.startswith(ANDI_HOST_URL)]
    assert any(u.endswith("andi.css") for u in andi_requests)
    assert any(u.endswith("fandi.js") for u in andi_requests)
    assert any("/icons/" in u for u in andi_requests)
    assert any("jquery.min.js" in u for u in requested)
    await ctx.close()


async def test_andi_missing_local_file_is_aborted_not_fetched(
    offline_browser, settings
):
    ctx = await new_context(offline_browser, settings)
    aborted = await install_andi_routes(ctx, settings.third_party_dir)
    page = await ctx.new_page()
    await page.goto((FIXTURES / "no_trap.html").as_uri())
    for url in (f"{ANDI_HOST_URL}nope.js", "https://www.ssa.gov/other/page.js"):
        status = await page.evaluate(f"fetch('{url}').then(r => r.status, () => 'err')")
        assert status == "err"
    assert aborted == [f"{ANDI_HOST_URL}nope.js", "https://www.ssa.gov/other/page.js"]
    await ctx.close()


async def test_andi_injects_on_har_replay(
    browser, offline_browser, settings, server, tmp_path
):
    har = tmp_path / "page.har.zip"
    cap = await record(browser, settings, f"{server.base}/dyn", har, noop_log)
    server.stop()

    replay = await replay_context(
        offline_browser, settings, har, noop_log, with_andi=True
    )
    ctx, guard = replay.context, replay.guard
    page = await ctx.new_page()
    failed = []
    page.on("requestfailed", lambda r: failed.append(r.url))
    await guard.goto(page, cap.final_url)
    await page.wait_for_function("document.getElementById('xhr').textContent")
    await _assert_andi_fully_loaded(page, settings, replay.andi_aborted, failed)
    await ctx.close()
