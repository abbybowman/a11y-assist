"""2.C on the vendored W3C ACT efbfc7 cases (draft check, tests/drafts.py);
expected outcomes are in fixtures/act/manifest.json. DHS scored all 11 under
2.C. Its three PASS cases with a button that works are NEEDS_REVIEW here
(ER 3 gate, reported as "gated"); scripted answers are what a correct agent
would say, never in a page."""

from __future__ import annotations

import json

import pytest

from .conftest import ACT_ROOT
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_tests
from .scoring import write_score

MANIFEST = json.loads((ACT_ROOT / "manifest.json").read_text())
CASES = {c["id"]: c for c in MANIFEST["cases"] if c["tt_test"] == "2.C"}

EVIDENT = {"J1": {"choice": "evident"}}
ANSWERS = {
    # "To control the random number updates activate the "Control changes"
    # button": it describes a way, with no key to press (K5).
    "9f538bf3": {"J2": {"choice": "describes"}},
}
# The row each case must reach (instance rows, then the page row).
ROWS = {
    "fd32eba8": "K3/E3",
    "18adb94c": "K3/E3",
    "337477ac": "K3/E3",
    "a17f7d74": "K5",
    "9f538bf3": "K5",
    "8f0a0534": "K6",
    "0d1564a1": "A4",
    "49cc7da7": "A3",
}


@pytest.mark.parametrize("case_id", sorted(CASES))
async def test_act_case(case_id, settings, act_server, drafts):  # noqa: F811
    case = CASES[case_id]
    got = await run_tests(
        settings,
        f"{act_server}/{case['path']}",
        ["2.C"],
        {"2.C": ANSWERS.get(case_id, EVIDENT)},
    )
    f = got["2.C"]
    write_score(case_id, f.outcome.value, f.rows)
    assert f.outcome.value == case["expected"], (f.rows, f.summary)
    want = ROWS.get(case_id)
    if want:
        have = [*f.rows, *instance_rows(f)]
        assert any(r == want or r.endswith(want) for r in have), (want, f.rows)
