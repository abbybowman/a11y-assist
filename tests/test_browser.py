"""Navigation guard and HAR capture/replay, verified in a real browser.

The local server listens on 127.0.0.1 (allowed in test settings); redirects to
"localhost" stand in for a disallowed host. Both names reach the same server,
so hit counts show whether a blocked request was actually sent.
"""

from __future__ import annotations

import pytest

from tobi508.browser import NavigationBlocked, NavigationGuard, new_context
from tobi508.capture import record, replay_context

from .conftest import FIXTURES, noop_log


async def _guarded_page(browser, settings):
    ctx = await new_context(browser, settings)
    guard = NavigationGuard(settings, live=True, log=noop_log)
    await guard.install(ctx)
    return ctx, guard, await ctx.new_page()


async def test_allowed_redirect_chain_is_followed(browser, settings, server):
    ctx, guard, page = await _guarded_page(browser, settings)
    final = await guard.goto(page, f"{server.base}/redir-ok")
    assert final == f"{server.base}/dyn"
    assert [r["status"] for r in guard.redirects] == [302, 301]
    await ctx.close()


@pytest.mark.parametrize("path", ["/redir-bad", "/redir-bad-2"])
async def test_redirect_to_disallowed_host_is_blocked_before_request(
    browser, settings, server, path
):
    ctx, guard, page = await _guarded_page(browser, settings)
    with pytest.raises(NavigationBlocked):
        await guard.goto(page, f"{server.base}{path}")
    assert server.hits[("localhost", "/landed")] == 0
    assert guard.blocked[-1]["url"].startswith("http://localhost:")
    await ctx.close()


async def test_disallowed_url_is_blocked(browser, settings, server):
    ctx, guard, page = await _guarded_page(browser, settings)
    with pytest.raises(NavigationBlocked):
        await guard.goto(page, f"http://localhost:{server.port}/dyn")
    assert server.hits[("localhost", "/dyn")] == 0
    await ctx.close()


async def test_page_initiated_navigation_to_disallowed_host_is_blocked(
    browser, settings, server
):
    ctx, guard, page = await _guarded_page(browser, settings)
    await guard.goto(page, f"{server.base}/dyn")
    with pytest.raises(Exception):
        await page.evaluate(f"location.href = 'http://localhost:{server.port}/landed'")
        await page.wait_for_url("**/landed", timeout=2000)
    assert server.hits[("localhost", "/landed")] == 0
    assert any("localhost" in b["url"] for b in guard.blocked)
    await ctx.close()


async def test_file_url_blocked_without_dev_mode(browser, settings):
    settings.dev_mode = False
    ctx, guard, page = await _guarded_page(browser, settings)
    with pytest.raises(NavigationBlocked):
        await guard.goto(page, (FIXTURES / "no_trap.html").as_uri())
    await ctx.close()


async def test_har_replay_is_identical_with_server_down(
    browser, settings, server, tmp_path
):
    har = tmp_path / "page.har.zip"
    cap = await record(browser, settings, f"{server.base}/redir-ok", har, noop_log)
    assert cap.final_url == f"{server.base}/dyn"
    server.stop()

    seen = []
    for _ in range(2):
        replay = await replay_context(browser, settings, har, noop_log)
        ctx = replay.context
        page = await ctx.new_page()
        await replay.guard.goto(page, cap.final_url)
        await page.wait_for_function("document.getElementById('xhr').textContent")
        seen.append(await page.evaluate("[srv.textContent, xhr.textContent]"))
        await ctx.close()
    assert seen[0] == seen[1]
    assert all(seen[0])
