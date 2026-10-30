"""Keyboard evidence collection on local fixtures.

These tests check what was recorded (stops, selectors, frames, screenshots),
never whether the page passes or fails a TT test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from a11y_assist.browser import NavigationGuard, new_context
from a11y_assist.evidence import focus_walk, parse_aria_line

from .conftest import FIXTURES, noop_log


async def _walk(browser, settings, fixture: str, forward: bool, tmp_path: Path, n: int):
    ctx = await new_context(browser, settings)
    guard = NavigationGuard(settings, live=False, log=noop_log)
    await guard.install(ctx)
    page = await ctx.new_page()
    await guard.goto(page, (FIXTURES / fixture).as_uri())
    walk = await focus_walk(page, forward, n, tmp_path / "shots", tmp_path, noop_log)
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
async def test_walk_on_simple_trap_records_repeated_stops(
    browser, settings, tmp_path, forward
):
    walk = await _walk(browser, settings, "simple_trap.html", forward, tmp_path, 8)
    assert walk.presses == 8
    assert walk.stopped_because == "max_presses"
    ids = _ids(walk)
    first_trap = ids.index("#trap")
    assert set(ids[first_trap:]) == {"#trap"}
    beyond_trap = "#after" if forward else "#before"
    assert beyond_trap not in ids


async def test_walk_on_modal_dialog_stays_in_dialog_or_leaves_page(
    browser, settings, tmp_path
):
    walk = await _walk(browser, settings, "modal_dialog.html", True, tmp_path, 12)
    in_page = [s.selector for s in walk.stops if not s.is_body]
    assert set(in_page) <= {"#name", "#save", "#close"}
    assert "#behind-link" not in in_page and "#open" not in in_page
    assert {"#name", "#save", "#close"} <= set(in_page)


async def test_max_presses_is_respected(browser, settings, tmp_path):
    walk = await _walk(browser, settings, "no_trap.html", True, tmp_path, 3)
    assert walk.presses == 3 and len(walk.stops) == 3
    assert walk.stopped_because == "max_presses"


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
