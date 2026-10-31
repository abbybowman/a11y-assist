"""4.B (2.1.1-no-keystroke-timing) on custom fixtures and the Section 508
Baseline Alignment cases (no ACT rule covers keystroke timing), plus rules
unit tests on recorded evidence. Expected outcomes and scripted answers live
here and in the manifest, never in a page."""

from __future__ import annotations

import json
import re

import pytest

from a11y_assist.checks import t4a, t4b
from a11y_assist.models import TestId

from .conftest import BASELINE_ROOT, FIXTURES
from .harness import instance_rows, run_check

HOLD = {"choice": "timing_required", "element": 1, "key": "Space", "duration_ms": 3000}

EXPECTED: dict[str, dict] = {
    "f01-hold-space-to-switch": {
        "outcome": "FAIL",
        "rows": ["M8"],
        "choice": {"J1": HOLD, "J2": {"choice": "no_alternative"}},
    },
    "f02-hold-with-alternative": {
        "outcome": "PASS",
        "rows": ["M7"],
        "choice": {"J1": HOLD, "J2": {"choice": "alternative", "element": 2}},
    },
    "f03-timing-words-not-keys": {
        "outcome": "PASS",
        "rows": ["M3"],
        "choice": {"J1": {"choice": "no_timing"}},
    },
}
REUSED = {"../no_trap.html": {"outcome": "PASS", "rows": ["M1"]}}

BASELINE = {
    c["id"]: c
    for c in json.loads((BASELINE_ROOT / "manifest.json").read_text())["cases"]
}
# Stops on TC01.A-2: user name, password, Log in, Request Password Reset.
ANSWERS = {"TC01.A-2-fail-1": {"J1": {**HOLD, "element": 4}}}


def test_every_fixture_is_listed():
    names = {p.stem for p in (FIXTURES / "4b").glob("*.html")}
    assert names == set(EXPECTED)
    for n in names:
        assert re.fullmatch(r"f\d{2}-[a-z0-9-]+", n), n


@pytest.mark.parametrize("name", sorted(EXPECTED) + sorted(REUSED))
async def test_outcome(name, settings, server):
    e = EXPECTED.get(name) or REUSED[name]
    path = name if name.endswith(".html") else f"{name}.html"
    got = await run_check(
        settings, f"{server.base}/4b/{path}", TestId.T4B, e.get("choice")
    )
    f = got["finding"]
    assert (f.outcome.value, instance_rows(f)) == (e["outcome"], e["rows"]), (
        f.rationale,
        f.summary,
    )


@pytest.mark.parametrize("case_id", sorted(BASELINE))
async def test_baseline_case(case_id, settings, baseline_server):
    case = BASELINE[case_id]
    got = await run_check(
        settings,
        f"{baseline_server}/{case['path']}",
        TestId.T4B,
        ANSWERS.get(case_id),
    )
    assert got["finding"].outcome.value == case["expected"]["4.B"], got[
        "finding"
    ].rationale


# ── Rules on recorded evidence ───────────────────────────────────────────────

EFF = t4a.Effect(kinds=["dom"], mutations=1).model_dump()
NONE = t4a.Effect().model_dump()


def _state(**kw) -> t4b.State4B:
    base = dict(
        p1={"end": "wrap"},
        stops=2,
        inventory=2,
        text_read=True,
        matches=["Press and hold Space for 3 seconds."],
        stop_list=[
            t4a.StopRef(n=1, path_key="#a", name="A", role="button", index=0),
            t4a.StopRef(n=2, path_key="#b", name="B", role="button", index=1),
        ],
        j1={**HOLD, "key": "Space", "reasons": "r"},
    )
    return t4b.State4B(**{**base, **kw})


PROVEN = {"normal": NONE, "timed": EFF, "timed2": EFF}


@pytest.mark.parametrize(
    ("kw", "outcome", "row"),
    [
        ({"j1": {"choice": "timing_required", "reasons": "r"}}, "NEEDS_REVIEW", "M4"),
        ({"j1": {"choice": "unsure", "reasons": "r"}}, "NEEDS_REVIEW", "M4"),
        ({}, "NEEDS_REVIEW", "P?"),
        # A normal press already works: no timing is required.
        ({"proof": {"normal": EFF, "timed": EFF}}, "NEEDS_REVIEW", "M5"),
        (
            {"proof": {"normal": NONE, "timed": EFF, "timed2": NONE}},
            "NEEDS_REVIEW",
            "M5",
        ),
        ({"proof": PROVEN}, "NEEDS_REVIEW", "J2?"),
        # The alternative must be another stop than the timed one.
        (
            {"proof": PROVEN, "j2": {"choice": "alternative", "element": 1}},
            "NEEDS_REVIEW",
            "M9",
        ),
        ({"proof": PROVEN, "j2": {"choice": "unsure"}}, "NEEDS_REVIEW", "M9"),
    ],
)
def test_rows_on_recorded_evidence(kw, outcome, row):
    f = t4b.evaluate(_state(**kw), [])
    assert (f.outcome.value, instance_rows(f)) == (outcome, [row]), f.rationale


def test_unread_text_is_never_pass():
    f = t4b.evaluate(_state(matches=[], text_read=False), [])
    assert f.outcome.value == "NEEDS_REVIEW"
