"""9.A (2.4.1) on the vendored ACT bypass-blocks cases, each compared with
the rules' own other page (chapter 2). Expected outcomes are in
fixtures/act/manifest.json (ours; ACT's are kept there too, and DHS scored
none of these rules); scripted answers here, never in a page."""

from __future__ import annotations

import json

import pytest

from .conftest import ACT_ROOT
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import run_tests

MANIFEST = json.loads((ACT_ROOT / "manifest.json").read_text())
CASES = {c["id"]: c for c in MANIFEST["cases"] if c["tt_test"] == "9.A"}
CH2 = "WAI/content-assets/wcag-act-rules/test-assets/bypass-blocks-cf77f2/chapter2.html"

# Scripted answers (what a correct agent would say), by case.
ANSWERS: dict[str, dict] = {}


@pytest.mark.parametrize("case_id", sorted(CASES))
async def test_act_case(case_id, settings, act_server, drafts):  # noqa: F811
    case = CASES[case_id]
    got = await run_tests(
        settings,
        f"{act_server}/{case['path']}",
        ["9.A"],
        {"9.A": ANSWERS.get(case_id, {})},
        other_pages=[f"{act_server}/{CH2}"],
    )
    f = got["9.A"]
    print(case_id, f.outcome.value, f.rows)
    assert f.outcome.value == case["expected"], (f.rows, f.summary, f.rationale)


async def test_without_other_pages_nothing_runs(settings, act_server, drafts):  # noqa: F811
    case = CASES["235a899f"]
    got = await run_tests(settings, f"{act_server}/{case['path']}", ["9.A"], {})
    f = got["9.A"]
    assert f.outcome.value == "NEEDS_REVIEW" and f.rows == ["A1", "G1"]
    assert f.note == "This test could not be performed"
