"""4.E (3.2.1-on-focus) on custom fixtures (no ACT rule covers 3.2.1), plus
rules unit tests for rows no page triggers reliably. Expected outcomes live
here, never in a page."""

from __future__ import annotations

import re

import pytest

from a11y_assist.checks import t4e
from a11y_assist.models import Outcome, TestId

from .conftest import FIXTURES
from .harness import instance_rows, run_check

EXPECTED: dict[str, dict] = {
    "f01-new-window-on-focus": {"outcome": "FAIL", "rows": ["M5"]},
    "f02-navigate-on-focus": {"outcome": "FAIL", "rows": ["M4"]},
    "f03-focus-moves-to-help": {"outcome": "FAIL", "rows": ["M6"]},
    "f04-blur-on-focus": {"outcome": "FAIL", "rows": ["M7"]},
    "f05-listbox-delegates-focus": {"outcome": "PASS", "rows": []},
    "f06-menu-and-tooltip-on-focus": {"outcome": "PASS", "rows": []},
    "f07-signup-dialog-on-focus": {
        "outcome": "FAIL",
        "rows": ["M9"],
        "choice": "changes_context",
    },
    "f08-help-bubble-on-focus": {
        "outcome": "PASS",
        "rows": ["M10"],
        "choice": "content_only",
    },
}
HELPERS = {"f02-other"}
# Pages from other tests that prove a "not an instance" rule for 4.E.
REUSED = {
    "../no_trap.html": {"outcome": "PASS", "rows": []},
    # A field that swallows Tab: focus never moves, no signal.
    "../4c/f04-field-swallows-tab.html": {"outcome": "PASS", "rows": []},
}


def test_every_fixture_is_listed():
    names = {p.stem for p in (FIXTURES / "4e").glob("*.html")}
    assert names == set(EXPECTED) | HELPERS
    for n in names:
        assert re.fullmatch(r"f\d{2}-[a-z0-9-]+", n), n


@pytest.mark.parametrize("name", sorted(EXPECTED) + sorted(REUSED))
async def test_outcome(name, settings, server):
    e = EXPECTED.get(name) or REUSED[name]
    path = name if name.endswith(".html") else f"{name}.html"
    got = await run_check(
        settings, f"{server.base}/4e/{path}", TestId.T4E, e.get("choice")
    )
    f = got["finding"]
    assert (f.outcome.value, instance_rows(f)) == (e["outcome"], e["rows"]), (
        f.rationale,
        f.summary,
    )


# ── Rules on recorded evidence (rows no page triggers reliably) ──────────────


def _state(**inst) -> t4e.State4E:
    base = dict(
        id="e1",
        pass_name="P1",
        step=2,
        key="Tab",
        keys=["Tab", "Tab"],
        target={"css_path": "#x", "role": "link", "name": "X"},
        signal=t4e.Signal(kind="navigation"),
    )
    return t4e.State4E(
        p1={"end": "navigation"},
        p2={"end": "wrap"},
        stops=3,
        inventory=3,
        instances=[t4e.Inst4E(**{**base, **inst})],
    )


@pytest.mark.parametrize(
    ("inst", "outcome", "row"),
    [
        ({"unreliable": True}, Outcome.NEEDS_REVIEW, "M1"),
        ({"reproduced": True, "timed": True}, Outcome.NEEDS_REVIEW, "M2"),
        ({"reproduced": False}, Outcome.NEEDS_REVIEW, "M3"),
        ({"reproduced": None}, Outcome.NEEDS_REVIEW, "R?"),
        ({"reproduced": True, "timed": False}, Outcome.FAIL, "M4"),
        (
            {"reproduced": True, "signal": t4e.Signal(kind="dialog")},
            Outcome.NEEDS_REVIEW,
            "J1?",
        ),
        (
            {
                "reproduced": True,
                "signal": t4e.Signal(kind="dialog"),
                "j1": {"choice": "unsure", "reasons": "", "decided_by": "model"},
            },
            Outcome.NEEDS_REVIEW,
            "M11",
        ),
    ],
)
def test_rows_on_recorded_evidence(inst, outcome, row):
    f = t4e.evaluate(_state(**inst), [])
    assert f.outcome is outcome and f"e1:{row}" in f.rows, (f.rows, f.summary)


def test_timed_redirect_is_a_note_not_an_instance():
    f = t4e.evaluate(_state(reproduced=True, timed=True), [])
    assert "goes to another page on its own" in f.summary
    assert f.instances == []


async def test_focus_pulled_back_by_the_element_left_is_not_an_instance(
    settings, act_server
):
    """ACT f5ea9fd3: a button refocuses itself on blur. That is 4.C's trap; the
    element receiving focus did not initiate it (spec section 3)."""
    import json

    case = next(
        c
        for c in json.loads((FIXTURES / "act" / "manifest.json").read_text())["cases"]
        if c["id"] == "f5ea9fd3"
    )
    got = await run_check(settings, f"{act_server}/{case['path']}", TestId.T4E)
    assert got["finding"].outcome is Outcome.PASS, got["finding"].rationale
