"""Section 508 ICT Baseline Alignment cases (vendored byte for byte): every
(case, TT test) pair in the manifest, plus file integrity. Expected outcomes
live only in manifest.json; scripted answers (what a correct agent would
say) are test data here, never in a page."""

from __future__ import annotations

import hashlib
import json

import pytest

from a11y_assist.checks import REGISTRY
from a11y_assist.models import TestId

from .conftest import BASELINE_ROOT
from .drafts import DRAFTS
from .harness import run_check

MANIFEST = json.loads((BASELINE_ROOT / "manifest.json").read_text())
CASES = {c["id"]: c for c in MANIFEST["cases"]}
PAIRS = sorted((cid, tt) for cid, c in CASES.items() for tt in c["expected"])

HOLD = {"choice": "timing_required", "key": "Space", "duration_ms": 3000}
ANSWERS = {
    ("TC01.A-1-fail-1", "4.A"): {"J1": {"choice": "no_alternative"}},
    # Stops on TC01.A-2: user name, password, Log in, Request Password Reset.
    ("TC01.A-2-fail-1", "4.B"): {"J1": {**HOLD, "element": 4}},
    # 5.D: nothing on these pages warns about the change.
    **{
        (c, "5.D"): {
            "J1": {"choice": "not_told"},
            "J2": {"choice": "changes_context"},
        }
        for c in ("TC10.C-3-fail-1", "TC10.C-3-fail-2", "TC10.C-3-fail-3")
    },
}


def test_files_match_their_hashes():
    for rel, digest in MANIFEST["files"].items():
        assert hashlib.sha256((BASELINE_ROOT / rel).read_bytes()).hexdigest() == digest
    assert {c["path"] for c in CASES.values()} <= set(MANIFEST["files"])


@pytest.mark.parametrize(("case_id", "tt"), PAIRS)
async def test_case(case_id, tt, settings, baseline_server, monkeypatch):
    if TestId(tt) not in REGISTRY and TestId(tt) not in DRAFTS:
        pytest.skip(f"no {tt} check yet (being built)")
    if TestId(tt) in DRAFTS:  # a draft spec: registered for its tests only
        monkeypatch.setitem(REGISTRY, TestId(tt), DRAFTS[TestId(tt)])
    case = CASES[case_id]
    got = await run_check(
        settings,
        f"{baseline_server}/{case['path']}",
        TestId(tt),
        ANSWERS.get((case_id, tt)),
    )
    f = got["finding"]
    assert f.outcome.value == case["expected"][tt], (f.rationale, f.summary)
