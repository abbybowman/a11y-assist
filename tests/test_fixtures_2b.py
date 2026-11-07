"""2.B end to end on custom pages in tests/fixtures/2x/ (draft check,
tests/drafts.py). Expected outcomes and scripted answers live here, never in
a page."""

from __future__ import annotations

import json

import pytest

from tobi508.models import TestId

from .conftest import ACT_ROOT
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_tests

NOT_ESSENTIAL = {"J1": {"choice": "not_essential"}}
EVIDENT = {"J1": {"choice": "not_essential"}, "J2": {"choice": "evident"}}

# page: (answers, outcome, a row that must appear)
CASES = {
    # Moving for more than 5 s with no control near it or at the top: K6.
    "t-css-infinite": (NOT_ESSENTIAL, "FAIL", "K6"),
    "t-marquee": (NOT_ESSENTIAL, "FAIL", "K6"),
    # Below the first screen: its animation's timing shows it (no frames).
    "t-below-fold": (NOT_ESSENTIAL, "FAIL", "K6"),
    # An animated image that loops forever, below the first screen: no frame
    # shows it, G152 on its recorded bytes does.
    "t-gif-below": (NOT_ESSENTIAL, "FAIL", "K6"),
    # Plays once for 2 s: not moving for more than 5 s.
    "t-gif-once": ({}, "DNA", "A2"),
    # Two colours back and forth is blinking: K6. Four colours: C1.
    "t-color-toggle": (NOT_ESSENTIAL, "FAIL", "K6"),
    "t-color-cycle": (NOT_ESSENTIAL, "NEEDS_REVIEW", "C1"),
    # A working pause button, evident: ER 3 holds PASS back.
    "t-anim-pause": (EVIDENT, "NEEDS_REVIEW", "K3/E3"),
    # Not moving for more than 5 s.
    "t-css-3s": ({}, "DNA", "A2"),
    "t-spinner": ({}, "DNA", "A2"),
    "t-elements": ({}, "DNA", "A2"),
    # A sliding carousel moves (2.B) and updates (2.C): one probe, no control.
    "t-carousels": (NOT_ESSENTIAL, "FAIL", "K6"),
    # Essential motion is excluded.
    "t-css-infinite-essential": (
        {"J1": {"choice": "essential", "reasons": "a game whose motion is the point"}},
        "DNA",
        "A4",
    ),
    # The guard: still moving at the end, on a page with a link, cannot be a
    # loading animation, so "essential, it is loading" counts as unsure.
    "t-css-infinite-loading": (
        {"J1": {"choice": "essential", "reasons": "a loading animation"}},
        "NEEDS_REVIEW",
        "A5",
    ),
}


@pytest.mark.parametrize("case", sorted(CASES))
async def test_page(case, settings, server, drafts):  # noqa: F811
    answers, outcome, row = CASES[case]
    page = case.removesuffix("-essential").removesuffix("-loading")
    got = await run_tests(
        settings, f"{server.base}/2x/{page}.html", ["2.B"], {"2.B": answers}
    )
    f = got["2.B"]
    assert f.outcome.value == outcome, (f.rows, f.summary)
    have = [*f.rows, *instance_rows(f)]
    assert any(r == row or r.endswith(row) for r in have), (row, f.rows)


async def test_act_color_cycle_with_stop(settings, act_server, drafts):  # noqa: F811
    """ACT efbfc7 inapplicable 3 (a 2.C case): only its colour changes, four
    colours, with a "Stop color changes" button after it. For 2.B it is
    blinking with a working, evident control (spec section 5)."""
    cases = json.loads((ACT_ROOT / "manifest.json").read_text())["cases"]
    [c] = [c for c in cases if c["id"] == "49cc7da7"]
    got = await run_tests(
        settings, f"{act_server}/{c['path']}", ["2.B", "2.C"], {"2.B": EVIDENT}
    )
    assert got["2.C"].outcome.value == "DNA"
    f = got["2.B"]
    assert f.outcome.value == "NEEDS_REVIEW", (f.rows, f.summary)
    assert any(r.endswith("K3/E3") for r in f.rows), f.rows


# For the judge eval (evals/judge_eval.py): page -> the outcome a correct
# agent gets. The badge below the first screen has no frame that shows it;
# since 1.1.0 J1 shows it in two crops, so a careful agent can settle it.
EVAL = {
    "t-css-infinite": "FAIL",
    "t-marquee": "FAIL",
    "t-color-toggle": "FAIL",
    "t-color-cycle": "NEEDS_REVIEW",
    "t-anim-pause": "NEEDS_REVIEW",
    "t-carousels": "FAIL",
    "t-below-fold": "FAIL",
}


async def test_j1_shows_content_below_the_first_screen_in_crops(
    settings,
    server,
    drafts,  # noqa: F811
):  # noqa: F811
    """1.1.0: content no frame shows whole gets two pictures cut around it,
    about 1 s apart (judge eval run 16: J1 for the badge below the first
    screen could only be unsure). Content on the first screen keeps the
    frames."""
    from tobi508.pipeline import run_tt_tests

    async def j1(name: str):
        out = await run_tt_tests(
            settings, f"{server.base}/2x/{name}.html", [TestId.T2B]
        )
        return [q for q in out.report.open_questions if q.question_id.endswith("-J1")]

    [q] = await j1("t-below-fold")
    assert [i.rsplit("/", 1)[1] for i in q.input["images"]] == [
        "2t-crop1-a.png",
        "2t-crop1-b.png",
    ]
    assert "first screen does not show" in q.input["images_show"]
    for q in await j1("t-marquee"):
        assert q.input["images_show"] == "the first screen of the page", q.input
