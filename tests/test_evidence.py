"""Keyboard evidence collection on local fixtures.

These tests check what was recorded (stops, selectors, frames, screenshots),
never whether the page passes or fails a TT test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from a11y_assist.browser import NavigationGuard, new_context
from a11y_assist.evidence import (
    dom_inventory,
    focus_walk,
    parse_aria_line,
    tab_press_cap,
)

from .conftest import FIXTURES, noop_log


async def _walk(browser, settings, fixture: str, forward: bool, tmp_path: Path, n: int):
    ctx = await new_context(browser, settings)
    guard = NavigationGuard(settings, live=False, log=noop_log)
    await guard.install(ctx)
    page = await ctx.new_page()
    await guard.goto(page, (FIXTURES / fixture).as_uri())
    walk = await focus_walk(page, forward, n, 0, tmp_path / "shots", tmp_path, noop_log)
    await ctx.close()
    return walk


def _ids(walk):
    return [s.selector for s in walk.stops]


async def test_forward_walk_no_trap(browser, settings, tmp_path):
    walk = await _walk(browser, settings, "no_trap.html", True, tmp_path, 25)
    assert walk.direction == "forward"
    assert walk.stopped_because == "returned_to_start"
    assert _ids(walk)[:7] == [
        "#first-link",
        "#btn",
        "#email",
        "#custom",
        "#inner-btn",
        "#host #shadow-btn",
        "#last-link",
    ]
    assert "#not-tabbable" not in _ids(walk)

    by_sel = {s.selector: s for s in walk.stops}
    assert (by_sel["#btn"].role, by_sel["#btn"].accessible_name) == (
        "button",
        "Plain button",
    )
    assert by_sel["#email"].accessible_name == "Email"
    assert by_sel["#custom"].tabindex == "0"
    assert by_sel["#custom"].accessible_name == "Custom control"
    assert by_sel["#inner-btn"].frame_path == ["#inner"]
    assert by_sel["#inner-btn"].accessible_name == "Inside frame"
    assert by_sel["#host #shadow-btn"].accessible_name == "Shadow button"
    assert by_sel["#first-link"].frame_path == []

    # After the last element focus leaves the page before wrapping.
    exit_stop = walk.stops[7]
    assert exit_stop.is_body and not exit_stop.page_has_focus

    for stop in walk.stops:
        assert (tmp_path / stop.screenshot).is_file()
        if not stop.is_body:
            assert stop.bounding_box and stop.bounding_box.width > 0
    # Inner-frame boxes are in top-page coordinates (offset by the iframe).
    assert by_sel["#inner-btn"].bounding_box.y > by_sel["#first-link"].bounding_box.y


async def test_backward_walk_no_trap(browser, settings, tmp_path):
    walk = await _walk(browser, settings, "no_trap.html", False, tmp_path, 25)
    assert walk.direction == "backward"
    assert all(s.key == "Shift+Tab" for s in walk.stops)
    assert _ids(walk)[:7] == [
        "#last-link",
        "#host #shadow-btn",
        "#inner-btn",
        "#custom",
        "#email",
        "#btn",
        "#first-link",
    ]


@pytest.mark.parametrize("forward", [True, False])
async def test_walk_on_f04_trap_records_repeated_stops(
    browser, settings, tmp_path, forward
):
    walk = await _walk(
        browser, settings, "4c/f04-field-swallows-tab.html", forward, tmp_path, 8
    )
    assert walk.presses == 8
    assert walk.stopped_because == "cap"
    ids = _ids(walk)
    first_trap = ids.index("#trap")
    assert set(ids[first_trap:]) == {"#trap"}
    beyond_trap = "#after" if forward else "#before"
    assert beyond_trap not in ids


async def test_walk_on_f10_dialog_stays_in_dialog_or_leaves_page(
    browser, settings, tmp_path
):
    walk = await _walk(
        browser, settings, "4c/f10-native-dialog.html", True, tmp_path, 12
    )
    in_page = [s.selector for s in walk.stops if not s.is_body]
    assert set(in_page) <= {"#name", "#save", "#close"}
    assert "#behind-link" not in in_page and "#open" not in in_page
    assert {"#name", "#save", "#close"} <= set(in_page)


async def test_max_presses_is_respected(browser, settings, tmp_path):
    walk = await _walk(browser, settings, "no_trap.html", True, tmp_path, 3)
    assert walk.presses == 3 and len(walk.stops) == 3
    assert walk.stopped_because == "cap"


@pytest.mark.parametrize(
    ("inventory", "cap"), [(0, 50), (1, 53), (8, 74), (983, 2999), (984, 3000)]
)
def test_tab_press_cap_follows_spec(inventory, cap):
    # 4.C spec section 2: 3 x inventory + 50 presses, max 3,000.
    assert tab_press_cap(inventory) == cap
    assert tab_press_cap(10_000) == 3000


async def test_dom_inventory_counts_frames_and_open_shadow_roots(browser, settings):
    ctx = await new_context(browser, settings)
    guard = NavigationGuard(settings, live=False, log=noop_log)
    await guard.install(ctx)
    page = await ctx.new_page()
    await guard.goto(page, (FIXTURES / "no_trap.html").as_uri())
    # Top: first-link, btn, email, custom, iframe, shadow-btn, last-link.
    # Inner frame: inner-btn. Not counted: span tabindex=-1, the <p>.
    assert await dom_inventory(page) == (8, 0)
    await page.set_content(
        "<button disabled>d</button><button hidden>h</button>"
        "<div inert><a href='#'>i</a></div><span tabindex='-1'>n</span>"
        "<input type='hidden'><div style='display:none'><button>x</button></div>"
        "<details><summary>s</summary></details><div tabindex='0'>t</div>"
    )
    assert await dom_inventory(page) == (2, 0)  # summary and tabindex=0 div
    await ctx.close()


@pytest.mark.parametrize(
    "line,expected",
    [
        ('- button "Save"', ("button", "Save")),
        ('- link "Home":', ("link", "Home")),
        ('- button "Custom control": Custom', ("button", "Custom control")),
        ('- textbox "Say \\"hi\\""', ("textbox", 'Say "hi"')),
        ("- generic", ("generic", None)),
        ("", (None, None)),
    ],
)
def test_parse_aria_line(line, expected):
    assert parse_aria_line(line) == expected
