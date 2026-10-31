"""Traversal on local fixtures: stop identity, settle rule, pass end conditions.

These record facts (where focus went, how a pass ended), never outcomes.
"""

from __future__ import annotations

import pytest

from a11y_assist.browser import new_context
from a11y_assist.traverse import (
    INIT_JS,
    Traversal,
    detect_p1_end,
    dom_inventory,
    run_pass,
    tab_press_cap,
)

from .conftest import FIXTURES


def _opener(browser, settings, url):
    async def new_page():
        ctx = await new_context(browser, settings)
        await ctx.add_init_script(INIT_JS)
        page = await ctx.new_page()
        await page.goto(url)
        return ctx, page

    return new_page


def _paths(p):
    return [
        s.stop.path_key if s.stop.kind == "element" else s.stop.kind for s in p.steps
    ]


async def _pass(browser, settings, url, key="Tab", **kw):
    return await run_pass("P", _opener(browser, settings, url), key, 50, **kw)


def _fixture(name):
    return (FIXTURES / name).as_uri()


async def test_forward_pass_follows_frames_and_shadow_roots_and_wraps(
    browser, settings
):
    p = await _pass(browser, settings, _fixture("no_trap.html"))
    assert p.end == "wrap"
    assert _paths(p) == [
        "#first-link",
        "#btn",
        "#email",
        "#custom",
        "#inner >> #inner-btn",
        "#host #shadow-btn",
        "#last-link",
        "OUT",
        "#first-link",
    ]
    by_path = {s.stop.path_key: s for s in p.steps}
    custom = by_path["#custom"].stop
    assert (custom.role, custom.name) == ("button", "Custom control")
    inner = by_path["#inner >> #inner-btn"].stop
    assert inner.frame_chain == ["#inner"] and inner.frame_url.startswith(
        "about:srcdoc"
    )
    # Frame-relative boxes are converted to top-page coordinates.
    assert inner.bounding_box.y > by_path["#first-link"].stop.bounding_box.y
    assert not any(s.unsettled for s in p.steps)


async def test_backward_pass_wraps(browser, settings):
    p = await _pass(browser, settings, _fixture("no_trap.html"), "Shift+Tab")
    assert p.end == "wrap"
    assert _paths(p)[:3] == ["#last-link", "#host #shadow-btn", "#inner >> #inner-btn"]


async def test_stuck_field_ends_pass_as_stuck(browser, settings):
    p = await _pass(browser, settings, _fixture("4c/f04-field-swallows-tab.html"))
    assert p.end == "stuck"
    assert _paths(p) == ["#before", "#trap", "#trap", "#trap"]
    assert p.trap == [p.steps[-1].stop.key]


async def test_script_loop_ends_pass_as_loop(browser, settings):
    p = await _pass(browser, settings, _fixture("4c/f06-script-loop.html"))
    assert p.end == "loop"
    assert _paths(p) == ["#before", "#a1", "#a2", "#a3", "#a1", "#a2", "#a3"]
    assert len(p.trap) == 3


async def test_closed_shadow_root_stops_are_resolved(browser, settings):
    p = await _pass(browser, settings, _fixture("4c/f25-closed-shadow-loop.html"))
    assert p.end == "loop"
    assert _paths(p)[1:4] == ["#host #s1", "#host #s2", "#host #s3"]
    assert not any(s.stop.unresolved for s in p.steps)


async def test_body_stop_when_focused_element_removes_itself(browser, settings):
    p = await _pass(browser, settings, _fixture("4c/f26-element-removes-itself.html"))
    assert p.end == "wrap"
    assert _paths(p)[:4] == ["#a1", "BODY", "#a3", "#a4"]


async def test_body_leading_back_to_the_top_is_a_loop(browser, settings):
    p = await _pass(
        browser, settings, _fixture("4c/f27-focus-drops-to-body-cycles.html")
    )
    assert p.end == "loop"
    assert _paths(p)[:3] == ["#a1", "#a2", "BODY"]


async def test_cap_ends_pass(browser, settings):
    p = await _pass(browser, settings, _fixture("no_trap.html"), cap=3)
    assert (p.end, len(p.steps), p.complete) == ("cap", 3, False)


async def test_page_cannot_spoof_focus(browser, settings, tmp_path):
    page_file = tmp_path / "spoof.html"
    page_file.write_text(
        "<!doctype html><title>s</title><a id=a1 href=#>1</a><a id=a2 href=#>2</a>"
        "<script>Object.defineProperty(document,'activeElement',"
        "{get(){return document.getElementById('a2')}})</script>"
    )
    p = await _pass(browser, settings, page_file.as_uri(), cap=1)
    assert _paths(p) == ["#a1"]


@pytest.mark.xfail(
    strict=True,
    reason="Spec question: a refocus 600 ms after blur lands after the next key "
    "press (each step takes ~350 ms), so the next-press check cannot see it and "
    "the page reads as a 2-stop loop, not a stuck element.",
)
async def test_late_refocus_is_caught_by_the_rerun(browser, settings, tmp_path):
    """A refocus 600 ms after blur lands after the 50 ms window used here; the
    focus log shows it at the next press and the step is re-read (V14)."""
    page_file = tmp_path / "late.html"
    page_file.write_text(
        "<!doctype html><title>l</title><button id=b>b</button><a id=next href=#>n</a>"
        "<script>b.addEventListener('blur',()=>setTimeout(()=>b.focus(),600))</script>"
    )
    p = await _pass(browser, settings, page_file.as_uri(), cap=4)
    assert _paths(p)[1] == "#b" and p.steps[1].rerun
    assert p.end == "stuck"


def test_detect_p1_end_needs_two_full_cycles_without_out():
    from a11y_assist.models import Step, Stop

    def steps(keys):
        return [
            Step(
                n=i,
                key="Tab",
                stop=Stop(kind="OUT" if k == "OUT" else "element", key=k),
                top_url="u",
                top_has_focus=k != "OUT",
                open_pages=1,
                mutations=0,
            )
            for i, k in enumerate(keys, 1)
        ]

    assert detect_p1_end(steps(["a", "b", "a"]), "a") is None
    assert detect_p1_end(steps(["a", "b", "a", "b"]), "a") == ("loop", ["a", "b"])
    assert detect_p1_end(steps(["a", "OUT", "a"]), "a") == ("wrap", [])
    assert detect_p1_end(steps(["x", "a", "OUT", "a", "OUT"]), "x") is None
    assert detect_p1_end(steps(["a", "a", "a"]), "a") == ("stuck", ["a"])


@pytest.mark.parametrize(
    ("inventory", "cap"), [(0, 50), (1, 53), (8, 74), (983, 2999), (984, 3000)]
)
def test_tab_press_cap_follows_spec(inventory, cap):
    assert tab_press_cap(inventory) == cap
    assert tab_press_cap(10_000) == 3000


async def test_dom_inventory(browser, settings):
    ctx = await new_context(browser, settings)
    page = await ctx.new_page()
    await page.goto(_fixture("no_trap.html"))
    inv = await dom_inventory(page)
    # Top: first-link, btn, email, custom, iframe, shadow-btn, last-link; frame: 1.
    assert (inv.candidates, inv.unreachable_frames, inv.keyboard_unreachable) == (
        8,
        0,
        0,
    )
    await page.set_content(
        "<button disabled>d</button><button hidden>h</button>"
        "<div inert><a href='#'>i</a></div><span tabindex='-1'>n</span>"
        "<input type='hidden'><div style='display:none'><button>x</button></div>"
        "<a href='#' style='visibility:hidden'>v</a>"
        "<details><summary>s</summary></details><div tabindex='0'>t</div>"
    )
    assert (await dom_inventory(page)).candidates == 2  # summary, tabindex=0 div
    await ctx.close()


async def test_inventory_leaves_out_negative_tabindex_iframes(
    browser, settings, server
):
    ctx = await new_context(browser, settings)
    page = await ctx.new_page()
    await page.goto(f"{server.base}/4c/f33-negative-tabindex-iframe-loop.html")
    await page.frame_locator("#frame").locator("#b1").wait_for()
    inv = await dom_inventory(page)
    assert (inv.candidates, inv.keyboard_unreachable) == (2, 2)
    await ctx.close()


async def test_traversal_records_focus_events(browser, settings):
    ctx, page = await _opener(browser, settings, _fixture("no_trap.html"))()
    t = Traversal(ctx, page, 50)
    await t.start()
    step = await t.press("Tab", "x")
    assert [e["type"] for e in step.focus_events] == ["focusin"]
    step = await t.press("Tab", "x")
    assert [(e["type"], e["id"]) for e in step.focus_events] == [
        ("focusout", "first-link"),
        ("focusin", "btn"),
    ]
    await ctx.close()
