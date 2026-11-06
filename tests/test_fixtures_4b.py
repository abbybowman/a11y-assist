"""4.B (2.1.1-no-keystroke-timing) on custom fixtures (no ACT rule covers
keystroke timing), plus rules unit tests on recorded evidence. Section 508
Baseline cases are in test_baseline_cases.py. Expected outcomes and scripted
answers live here, never in a page."""

from __future__ import annotations

import re

import pytest

from tobi508.checks import t4a, t4b
from tobi508.models import TestId
from tobi508.observe import Effect

from .conftest import FIXTURES
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
    # The named button shows a help line, not the switch: an agent's wrong
    # "alternative" was a PASS before the alternative press (1.2.0).
    "f04-hold-alternative-does-other": {
        "outcome": "NEEDS_REVIEW",
        "rows": ["M10"],
        "choice": {"J1": HOLD, "J2": {"choice": "alternative", "element": 2}},
    },
}
REUSED = {"../no_trap.html": {"outcome": "PASS", "rows": ["M1"]}}


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


# ── Rules on recorded evidence ───────────────────────────────────────────────

EFF = Effect(kinds=["dom"], mutations=1).model_dump()
NONE = Effect().model_dump()


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


LOADED = {"url": "u", "text_sha256": "before"}
CHANGED = {"url": "u", "text_sha256": "after"}
PROVEN = {
    "normal": NONE,
    "timed": EFF,
    "timed2": EFF,
    "normal_end": LOADED,
    "timed_end": CHANGED,
}
ALT = {"choice": "alternative", "element": 2}


def _alt(end) -> dict:
    return {"reached": True, "key": "Enter", "effect": EFF, "end": end}


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
        # An alternative leads to PASS only when pressing it confirms it.
        ({"proof": PROVEN, "j2": ALT}, "NEEDS_REVIEW", "A?"),
        ({"proof": PROVEN, "j2": ALT, "alt": _alt(CHANGED)}, "PASS", "M7"),
        ({"proof": PROVEN, "j2": ALT, "alt": _alt(LOADED)}, "NEEDS_REVIEW", "M10"),
        (
            {"proof": PROVEN, "j2": ALT, "alt": {"reached": False}},
            "NEEDS_REVIEW",
            "M10",
        ),
        # The timed press left the text as the normal press did: nothing to
        # compare, so the text cannot confirm the alternative.
        (
            {
                "proof": {**PROVEN, "timed_end": LOADED},
                "j2": ALT,
                "alt": _alt(LOADED),
            },
            "NEEDS_REVIEW",
            "M10",
        ),
    ],
)
def test_rows_on_recorded_evidence(kw, outcome, row):
    f = t4b.evaluate(_state(**kw), [])
    assert (f.outcome.value, instance_rows(f)) == (outcome, [row]), f.rationale


def test_unread_text_is_never_pass():
    f = t4b.evaluate(_state(matches=[], text_read=False), [])
    assert f.outcome.value == "NEEDS_REVIEW"


async def test_page_text_goes_out_and_sentences_stay_whole(settings, server):
    # Judge eval 2026-10-31: page_text was empty for 4.B and the instruction
    # was cut at its line break.
    from tobi508.pipeline import run_tt_tests

    out = await run_tt_tests(
        settings, f"{server.base}/4b/f01-hold-space-to-switch.html", [TestId.T4B]
    )
    assert out.page_text and "press and hold" in out.page_text[0]["text"]
    [q] = out.open_questions
    assert any(
        m.startswith("To change the button") and m.endswith("release the spacebar.")
        for m in q.input["matches"]
    ), q.input["matches"]
