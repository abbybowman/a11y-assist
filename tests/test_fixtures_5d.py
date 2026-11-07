"""5.D (3.2.2-on-input) on custom fixtures (the Baseline Alignment TC10.C
cases are in test_baseline_cases.py; 5.D is a draft, registered by
tests/drafts.py), plus behavior tests that each page
does what it is meant to in Chrome. Expected outcomes live here, never in a
page."""

from __future__ import annotations

import re

import pytest

from tobi508.checks import t5d
from tobi508.engine import first_match
from tobi508.models import TestId
from tobi508.observe import Effect
from tobi508.pipeline import run_tt_tests

from .conftest import FIXTURES
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_check

TOLD = {"J1": {"choice": "told"}}
NOT_TOLD = {"J1": {"choice": "not_told"}}

# Scripted answers stand in for the calling agent (test data, never in a
# page). J1 "told" answers carry the quote the mechanical check looks for.
EXPECTED: dict[str, dict] = {
    "f01-jump-menu": {"outcome": "FAIL", "rows": ["M9"], "answers": NOT_TOLD},
    "f02-jump-menu-notice-before": {
        "outcome": "PASS",
        "rows": ["M8"],
        "answers": {
            "J1": {
                "choice": "told",
                "quote": "Pick a state from the list and its office page opens "
                "right away.",
            }
        },
    },
    "f03-submit-when-last-field-filled": {
        "outcome": "FAIL",
        "rows": ["M9"],
        "answers": NOT_TOLD,
    },
    "f04-radio-opens-window": {"outcome": "FAIL", "rows": ["M9"], "answers": NOT_TOLD},
    "f05-phone-auto-advance": {
        "outcome": "FAIL",
        "rows": ["M9", "M9"],
        "answers": NOT_TOLD,
    },
    "f06-phone-auto-advance-notice": {
        "outcome": "PASS",
        "rows": ["M8", "M8"],
        "answers": {
            "J1": {
                "choice": "told",
                "quote": "the cursor jumps on to the next part",
            }
        },
    },
    "f07-checkbox-reveals-fields": {
        "outcome": "PASS",
        "rows": ["M11"],
        "answers": {"J2": {"choice": "content_only"}, "J1": {"choice": "not_told"}},
    },
    # 1.2.0: checking a box puts a panel over most of the window; J2's input
    # says how much changed (test_j2_says_how_much_of_the_window_changed).
    "f16-checkbox-shows-full-terms": {
        "outcome": "FAIL",
        "rows": ["M9"],
        "answers": {"J2": {"choice": "changes_context"}, "J1": {"choice": "not_told"}},
    },
    "f08-autocomplete-list": {"outcome": "PASS", "rows": []},
    "f09-field-in-iframe": {"outcome": "FAIL", "rows": ["M9"], "answers": NOT_TOLD},
    "f10-zip-submits-when-valid": {
        "outcome": "FAIL",
        "rows": ["M9"],
        "answers": {"J3": {"choice": "value", "value": "20500"}, **NOT_TOLD},
    },
    "f11-jump-menu-notice-after": {
        "outcome": "FAIL",
        "rows": ["M9"],
        "answers": NOT_TOLD,
    },
    "f12-slider-reloads": {"outcome": "FAIL", "rows": ["M9"], "answers": NOT_TOLD},
    "f13-spinbutton-updates-total": {"outcome": "PASS", "rows": []},
    "f14-plain-form-controls": {"outcome": "PASS", "rows": []},
    # Four filter boxes that each go to another page, one question for all.
    "f15-filter-checkboxes-navigate": {
        "outcome": "FAIL",
        "rows": ["M9", "M9", "M9", "M9"],
        "answers": NOT_TOLD,
    },
}
HELPERS = {"f01-other", "f09-frame"}
# Pages from other tests: no form fields at all. A small page: row A1 does
# not depend on page size, and the 100-link page cost a 50 s walk here.
REUSED = {"../4d/f01-background-change.html": {"outcome": "DNA", "rows": []}}


def test_every_fixture_is_listed():
    names = {p.stem for p in (FIXTURES / "5d").glob("*.html")}
    assert names == set(EXPECTED) | HELPERS
    for n in names:
        assert re.fullmatch(r"f\d{2}-[a-z0-9-]+", n), n


@pytest.mark.parametrize("name", sorted(EXPECTED) + sorted(REUSED))
async def test_outcome(name, settings, server, drafts):  # noqa: F811
    e = EXPECTED.get(name) or REUSED[name]
    path = name if name.endswith(".html") else f"{name}.html"
    got = await run_check(
        settings, f"{server.base}/5d/{path}", TestId.T5D, e.get("answers")
    )
    f = got["finding"]
    assert (f.outcome.value, instance_rows(f)) == (e["outcome"], e["rows"]), (
        f.rationale,
        f.summary,
    )
    if name in COVERS:
        # 1.2.0: J2's input gives the share of the window that changed (or a
        # new dialog or layer covers) and whether a new dialog is modal.
        [q] = [q for q in got["asked"] if q.question_id.endswith("-J2")]
        low, high = COVERS[name]
        share = int(q.input["covers_window"].rstrip("%"))
        assert low <= share <= high and q.input["modal"] is False, q.input


# Fixture -> the range J2's covers_window must fall in (percent).
COVERS = {
    "f16-checkbox-shows-full-terms": (51, 100),
    "f07-checkbox-reveals-fields": (0, 49),
}


async def test_f15_one_question_for_a_list_of_alike_fields(
    settings,
    server,
    drafts,  # noqa: F811
):
    """Post-round 1 fix 15: alike fields in a list are asked about once, and
    the one answer decides each of them (an instance per field)."""
    url = f"{server.base}/5d/f15-filter-checkboxes-navigate.html"
    out = await run_tt_tests(settings, url, [TestId.T5D])
    qs = [q for q in out.report.open_questions if q.test_id is TestId.T5D]
    assert len(qs) == 1, [q.question_id for q in qs]
    [q] = qs
    assert len(q.also_instances) == 3
    assert [f["label"] for f in q.input["fields"]] == [
        "Active",
        "Future",
        "Past",
        "Inactive",
    ]
    assert q.input["before"] == "Mission status"


# ── The pages behave as designed (plain Chrome, no tool) ─────────────────────


@pytest.fixture
async def page(browser, settings, server):
    ctx = await browser.new_context()
    p = await ctx.new_page()

    async def open_(name: str):
        await p.goto(f"{server.base}/5d/{name}.html")
        await p.wait_for_load_state("load")
        return p

    yield open_
    await ctx.close()


async def test_f01_jump_menu_navigates_on_arrow_down(page):
    p = await page("f01-jump-menu")
    await p.focus("#state")
    async with p.expect_navigation():
        await p.keyboard.press("ArrowDown")
    assert p.url.endswith("f01-other.html?state=al")


async def test_f03_submits_only_when_every_field_is_filled(page):
    p = await page("f03-submit-when-last-field-filled")
    await p.focus("#topic")
    await p.keyboard.type("Test")
    await p.keyboard.press("Tab")  # change fires; name and email empty
    assert "f03" in p.url
    await p.fill("#name", "Test")
    await p.fill("#email", "test@example.gov")
    await p.focus("#topic")
    await p.keyboard.type("x")
    async with p.expect_navigation():
        await p.keyboard.press("Tab")
    assert "f01-other.html" in p.url


async def test_f04_choosing_yes_opens_a_window(page):
    p = await page("f04-radio-opens-window")
    await p.focus("#no")
    async with p.context.expect_page():
        await p.keyboard.press("ArrowDown")  # selects Yes


async def test_f05_full_area_code_moves_focus(page):
    p = await page("f05-phone-auto-advance")
    await p.focus("#p1")
    await p.keyboard.type("123")
    assert await p.evaluate("document.activeElement.id") == "p2"


async def test_f07_checkbox_reveals_mailing_fields(page):
    p = await page("f07-checkbox-reveals-fields")
    assert await p.is_hidden("#mstreet")
    await p.focus("#diff")
    await p.keyboard.press("Space")
    assert await p.is_visible("#mstreet")


async def test_f10_submits_only_on_a_valid_zip(page):
    p = await page("f10-zip-submits-when-valid")
    await p.focus("#zip")
    await p.keyboard.type("Test")
    await p.keyboard.press("Tab")
    assert "f10" in p.url
    assert await p.evaluate("!document.getElementById('zip').checkValidity()")
    await p.fill("#zip", "")
    await p.focus("#zip")
    await p.keyboard.type("20500")
    async with p.expect_navigation():
        await p.keyboard.press("Tab")


async def test_f12_slider_arrow_navigates(page):
    p = await page("f12-slider-reloads")
    await p.focus("#min")
    async with p.expect_navigation():
        await p.keyboard.press("ArrowRight")
    assert p.url.endswith("min=20")


async def test_f13_spinbutton_updates_total_only(page):
    p = await page("f13-spinbutton-updates-total")
    await p.focus("#qty")
    await p.keyboard.press("ArrowUp")
    assert await p.text_content("#total") == "Total: 2 copies"
    assert "f13" in p.url


# ── Rules on recorded evidence (rows no page triggers reliably) ──────────────


def _inst(**kw) -> t5d.Inst5D:
    field = t5d.Field5D(n=1, index=0, path_key="#f", css_path="#f", control="select")
    attempt = kw.pop("attempt", {})
    return t5d.Inst5D(
        id="f1",
        field=field,
        info={"label": "State", "before": "Choosing a state  takes you to its page."},
        attempts=[t5d.Attempt(**attempt)] if attempt is not None else [],
        **kw,
    )


def _row(inst: t5d.Inst5D) -> str:
    return first_match(t5d.INSTANCE_ROWS, inst).id


NAV = {"complete": [Effect(kinds=["navigation"])], "completed": True}


def test_rows_on_recorded_evidence():
    assert _row(_inst(arrived=False, attempt=None)) == "M1"
    assert _row(_inst(attempt={"completed": False})) == "M2"
    assert _row(_inst(attempt=NAV)) == "J1?"
    # J1's quote is checked against the text before the field, whitespace and
    # case aside; a quote that is not there is not a notice.
    told = {"choice": "told", "quote": "choosing a state takes you to its PAGE."}
    assert _row(_inst(attempt=NAV, j1=told)) == "M8"
    made_up = {"choice": "told", "quote": "You will be redirected."}
    assert _row(_inst(attempt=NAV, j1=made_up)) == "M10"
    assert _row(_inst(attempt=NAV, j1={"choice": "unsure"})) == "M10"
    assert _row(_inst(attempt=NAV, j1={"choice": "not_told"})) == "M9"
    content = {
        "complete": [Effect(kinds=["dom"], mutations=3)],
        "outside_changed": True,
    }
    assert _row(_inst(attempt=content)) == "M13"  # J2 not answered yet
    assert _row(_inst(attempt=content, j2={"choice": "unsure"})) == "M13"
    assert _row(_inst(attempt=content, j2={"choice": "content_only"})) == "M11"
    taken = {"choice": "changes_context"}
    assert _row(_inst(attempt=content, j2=taken)) == "J1?"
    assert _row(_inst(attempt=content, j2=taken, j1={"choice": "not_told"})) == "M9"
    # 1.2.0, row M15: content_only for a change over most of the window, or
    # a modal dialog, is left for a person, never PASS.
    only = {"choice": "content_only"}
    wide = {**content, "cover": {"changed": 0.7, "layer": 0.0, "modal": False}}
    modal = {**content, "cover": {"changed": 0.1, "layer": 0.2, "modal": True}}
    small = {**content, "cover": {"changed": 0.1, "layer": 0.0, "modal": False}}
    assert _row(_inst(attempt=wide, j2=only)) == "M15"
    assert _row(_inst(attempt=modal, j2=only)) == "M15"
    assert _row(_inst(attempt=small, j2=only)) == "M11"
    # Page noise during the action, and only DOM changes: unreliable.
    noisy = {
        "complete": [Effect(kinds=["dom"], mutations=2, noise=3)],
        "outside_changed": True,
    }
    assert _row(_inst(attempt=noisy)) == "M1"
    # Nothing happened.
    assert _row(_inst(attempt={"complete": [Effect()], "completed": True})) == "M14"


def test_rejected_value_asks_j3_then_stands_when_unsure():
    rejected = {
        "complete": [Effect()],
        "completed": True,
        "rejected": True,
        "value": "Test",
    }
    assert _row(_inst(attempt=rejected)) == "M3"
    assert _row(_inst(attempt=rejected, j3={"choice": "unsure"})) == "M14"
