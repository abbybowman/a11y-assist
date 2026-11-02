"""5.B (2.4.6, labels) on the vendored W3C ACT cc0f0a cases; expected
outcomes are in fixtures/act/manifest.json (ours follow the visible label,
as DHS's verdicts do). Scripted answers (what a correct agent would say)
live here, never in a page. The TC10.A/TC10.E Baseline cases are in
test_baseline_cases.py."""

from __future__ import annotations

import json

import pytest

from .conftest import ACT_ROOT
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_tests
from .scoring import write_score

MANIFEST = json.loads((ACT_ROOT / "manifest.json").read_text())
CASES = {c["id"]: c for c in MANIFEST["cases"] if c["tt_test"] == "5.B"}

ALL = {"J1": {"choice": "all_descriptive"}}


def _not(*n: int) -> dict:
    return {"J1": {"choice": "some_not_descriptive", "elements": list(n)}}


ANSWERS = {
    "9b967559": _not(1),  # "Menu"
    "1e520607": _not(1),
    "fa5104f9": _not(1),
    "3ee841b7": _not(1),  # "Info:" on a date field
    "64994609": _not(1, 2, 3, 4),  # Name/Street twice, headings off screen
    "2f1d9641": _not(1),  # the field's only visible cue is "Go"
}


@pytest.mark.parametrize("case_id", sorted(CASES))
async def test_act_case(case_id, settings, act_server, drafts):  # noqa: F811
    case = CASES[case_id]
    got = await run_tests(
        settings,
        f"{act_server}/{case['path']}",
        ["5.B"],
        {"5.B": ANSWERS.get(case_id, ALL)},
    )
    f = got["5.B"]
    write_score(case_id, f.outcome.value, f.rows)
    assert f.outcome.value == case["expected"], (f.rows, f.summary)
    if case["expected"] == "FAIL":
        assert "M2" in instance_rows(f)
