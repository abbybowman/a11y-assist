"""2.A on the vendored W3C ACT cases of rules 80f0bf, 4c31df and aaa1bf
(draft check, tests/drafts.py); expected outcomes are in
fixtures/act/manifest.json. DHS scored none of these rules. A working
control is NEEDS_REVIEW while ER 3's tests are not all built ("gated")."""

from __future__ import annotations

import json

import pytest

from .conftest import ACT_ROOT
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_tests
from .scoring import write_score

MANIFEST = json.loads((ACT_ROOT / "manifest.json").read_text())
CASES = {c["id"]: c for c in MANIFEST["cases"] if c["tt_test"] == "2.A"}
ROWS = {
    "0d2dcde8": "K3/E3",
    "3e932531": "K3/E3",
    "29ea904e": "K3/E3",
    "f9af87d3": "K3/E3",
    "7304f139": "K3/E3",
    "968b12b1": "K6",
    "b712209d": "K6",
    "53b7029c": "K6",
    "7c96453d": "K6",
    "7d3d7214": "A3",
}


@pytest.mark.parametrize("case_id", sorted(CASES))
async def test_act_case(case_id, settings, act_server, drafts):  # noqa: F811
    case = CASES[case_id]
    got = await run_tests(settings, f"{act_server}/{case['path']}", ["2.A"], {})
    f = got["2.A"]
    write_score(case_id, f.outcome.value, f.rows)
    assert f.outcome.value == case["expected"], (f.rows, f.summary)
    want = ROWS.get(case_id)
    if want:
        have = [*f.rows, *instance_rows(f)]
        assert any(r == want or r.endswith(want) for r in have), (want, f.rows)
