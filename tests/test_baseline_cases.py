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
from .harness import run_tests

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
    # 5.A (visual label) and 5.C (announced text) on TC10.A / TC10.E.
    ("TC10.A-1-fail-1", "5.A"): {"J1": {"choice": "labeled", "quote": "First Name:"}},
    **{
        (c, "5.A"): {"J1": {"choice": "labeled", "quote": q}}
        for c, q in (
            ("TC10.A-all-pass-3", "Last Name:"),
            ("TC10.A-all-pass-4", "Middle Name:"),
            ("TC10.A-all-pass-5", "Company Name"),
            ("TC10.A-all-pass-6", "Official Name"),
        )
    },
    ("TC10.E-1-fail-1", "5.A"): {"J1": {"choice": "not_labeled"}},
    # 5.B: one field each; "The sky is blue" does not describe it.
    **{
        (c, "5.B"): {"J1": {"choice": "all_descriptive"}}
        for c in (
            "TC10.A-1-fail-1",
            "TC10.A-all-pass-2",
            "TC10.A-all-pass-3",
            "TC10.A-all-pass-4",
            "TC10.A-all-pass-5",
            "TC10.A-all-pass-6",
            "TC10.E-1-pass-2",
            "TC10.E-1-pass-3",
        )
    },
    # 5.H (TC10.G): one-page order forms; 2.c shows a cart before payment.
    **{
        (c, "5.H"): {"J1": {"choice": "one_page", "element": 1}}
        for c in ("TC10.G-2.a-pass-1", "TC10.G-2.b-pass-1", "TC10.G-all-fail-1")
    },
    # Its text says the form "does not change" data: the 1.1.0 hint word
    # "change" asks J1, and a correct agent answers no consequences.
    ("TC10.G-ic-dna-2", "5.H"): {"J1": {"choice": "not_consequential", "element": 1}},
    ("TC10.G-2.c-pass-1", "5.H"): {
        "J1": {"choice": "multi_step", "element": 1},
        "J2": {"choice": "review_step"},
    },
    ("TC10.E-1-pass-1", "5.B"): {
        "J1": {"choice": "some_not_descriptive", "elements": [1]}
    },
    # 5.F / 5.G (TC10.D): what a correct agent says about each error text.
    ("TC10.D-2-fail-1", "5.F"): {
        "J1": {"choice": "described", "quote": "Error: not a number."}
    },
    ("TC10.D-2-fail-1", "5.G"): {"J1": {"choice": "guides", "quote": "not a number"}},
    ("TC10.D-2-fail-2", "5.F"): {"J2": {"choice": "error"}},
    ("TC10.D-2-fail-2", "5.G"): {"J2": {"choice": "error"}},
    ("TC10.D-2-fail-3", "5.F"): {"J1": {"choice": "not_identified"}},
    ("TC10.D-2-fail-3", "5.G"): {"J1": {"choice": "no_guidance"}},
    **{
        (c, "5.F"): {"J1": {"choice": "described", "quote": "a number"}}
        for c in ("TC10.D-all-pass-1",)
    },
    **{
        (c, "5.F"): {"J1": {"choice": "described", "quote": "Error: not a number."}}
        for c in ("TC10.D-all-pass-2", "TC10.D-all-pass-3")
    },
    **{
        (c, "5.G"): {"J1": {"choice": "guides", "quote": "number"}}
        for c in ("TC10.D-all-pass-1", "TC10.D-all-pass-2", "TC10.D-all-pass-3")
    },
}


def test_files_match_their_hashes():
    for rel, digest in MANIFEST["files"].items():
        assert hashlib.sha256((BASELINE_ROOT / rel).read_bytes()).hexdigest() == digest
    assert {c["path"] for c in CASES.values()} <= set(MANIFEST["files"])


# All of a case's tests run in one call, as a client runs them: one browser
# run per page, and checks that share a pass (5.A-5.C, 5.F-5.H) or a replay
# (4.A with 4.D and 4.F) are tested sharing it.
@pytest.mark.parametrize("case_id", sorted(CASES))
async def test_case(case_id, settings, baseline_server, monkeypatch):
    case = CASES[case_id]
    tts = []
    for tt in sorted(case["expected"]):
        if TestId(tt) in DRAFTS:  # a draft spec: registered for its tests only
            monkeypatch.setitem(REGISTRY, TestId(tt), DRAFTS[TestId(tt)])
        if TestId(tt) in REGISTRY:
            tts.append(tt)
    if not tts:
        pytest.skip(f"no check yet for {sorted(case['expected'])} (being built)")
    url = f"{baseline_server}/{case['path']}"
    got = await run_tests(
        settings, url, tts, {t: ANSWERS.get((case_id, t)) or {} for t in tts}
    )
    wrong = {
        tt: (got[tt].outcome.value, case["expected"][tt], got[tt].rationale)
        for tt in tts
        if got[tt].outcome.value != case["expected"][tt]
    }
    assert wrong == {}, wrong
