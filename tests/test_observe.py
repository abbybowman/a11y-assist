"""What an action changes (observe.observe): facts only, never outcomes."""

from __future__ import annotations

from a11y_assist.browser import new_context
from a11y_assist.observe import observe
from a11y_assist.traverse import INIT_JS, open_session


def _opener(browser, settings, url):
    async def new_page():
        ctx = await new_context(browser, settings)
        await ctx.add_init_script(INIT_JS)
        page = await ctx.new_page()
        await page.goto(url)
        return ctx, page

    return new_page


async def test_a_window_that_closes_at_once_is_still_a_new_window(
    browser, settings, tmp_path
):
    # The page count before and after is the same, as it is on Windows when a
    # new page joins the list after the settle; the browser saw it open.
    page_file = tmp_path / "flash.html"
    page_file.write_text(
        "<!doctype html><title>t</title><button id=b>Go</button><script>"
        "b.onclick = () => { const w = window.open('about:blank'); w.close(); };"
        "</script>"
    )
    s = await open_session(
        _opener(browser, settings, page_file.as_uri()), settings.settle_quiet_ms
    )
    try:
        e = await observe(
            s, settings.settle_quiet_ms, lambda: s.page.click("#b"), own="#b"
        )
    finally:
        await s.close()
    assert "new_page" in e.kinds, e.kinds


async def test_no_window_is_no_new_window(browser, settings, tmp_path):
    page_file = tmp_path / "quiet.html"
    page_file.write_text("<!doctype html><title>t</title><button id=b>Go</button>")
    s = await open_session(
        _opener(browser, settings, page_file.as_uri()), settings.settle_quiet_ms
    )
    try:
        e = await observe(
            s, settings.settle_quiet_ms, lambda: s.page.click("#b"), own="#b"
        )
    finally:
        await s.close()
    assert "new_page" not in e.kinds, e.kinds
