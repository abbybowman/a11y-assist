"""The shared walk's second pass (4.C spec section 2, 1.9.0): a trap event
ends a pass only when a fresh load repeats it.

F36 is a page whose survey dialog opens by itself on some loads only, takes
focus and keeps it inside (as Artemis III's did on about 1 load in 10). Here
a session cookie decides each load, so the test chooses which loads show it.
These record facts (how passes ended), never outcomes.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from tobi508.browser import new_context
from tobi508.traverse import INIT_JS
from tobi508.walk import trap_paths, walk_page

SURVEY = {"#yes", "#no", "#close"}


def _opener(browser, settings, url, show):
    """Open `url` in a fresh context; `show(n)` says whether load n (from 1)
    gets the survey. Records every load in `loads`."""
    loads: list[bool] = []

    async def new_page():
        ctx = await new_context(browser, settings)
        await ctx.add_init_script(INIT_JS)
        on = show(len(loads) + 1)
        loads.append(on)
        if on:
            host = urlsplit(url).hostname
            await ctx.add_cookies(
                [{"name": "survey", "value": "show", "domain": host, "path": "/"}]
            )
        page = await ctx.new_page()
        await page.goto(url)
        return ctx, page

    return new_page, loads


async def _walk(browser, settings, server, show):
    url = f"{server.base}/4c/f36-survey-on-some-loads.html"
    new_page, loads = _opener(browser, settings, url, show)
    return await walk_page(new_page, settings.settle_quiet_ms, None), loads


async def test_survey_on_the_first_load_only_does_not_end_the_walk(
    browser, settings, server
):
    walk, loads = await _walk(browser, settings, server, lambda n: n == 1)
    # P1 met the survey, P1 again did not, then P2: three loads.
    assert loads == [True, False, False]
    assert walk.p1.end == "wrap" and walk.p2.end == "wrap"
    first = walk.p1.unrepeated
    assert first is not None and first.end == "loop"
    assert trap_paths(first) == SURVEY
    assert not walk.p1.confirmed and walk.p2.unrepeated is None
    # The walk the checks read reached the whole page.
    assert walk.p1.steps[-2].stop.kind == "OUT"


async def test_survey_on_every_load_is_confirmed(browser, settings, server):
    walk, loads = await _walk(browser, settings, server, lambda n: True)
    assert loads == [True] * 4  # P1 twice, P2 twice
    for p in (walk.p1, walk.p2):
        assert p.end == "loop" and p.confirmed and p.unrepeated is None
        assert trap_paths(p) == SURVEY


async def test_no_survey_needs_no_second_pass(browser, settings, server):
    walk, loads = await _walk(browser, settings, server, lambda n: False)
    assert loads == [False, False]
    assert walk.p1.end == "wrap" and walk.p2.end == "wrap"
    assert walk.p1.unrepeated is None and walk.p2.unrepeated is None
