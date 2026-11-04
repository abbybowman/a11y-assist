"""2.C's mechanism rows (K1-K8, E1-E4) on hand-built evidence: no page can
trigger them until the mechanism probe is built. Expected outcomes live here
(CLAUDE.md principle 2: the rows are the spec's, copied into t2c.py)."""

from __future__ import annotations

import pytest

from a11y_assist.checks import t2c
from a11y_assist.checks.t2c import State2C, evaluate, questions_for
from a11y_assist.motion import Candidate, Element, MotionPass, Probe, Region


def _state(probe: Probe, j1=None, j2=None) -> State2C:
    els = [
        Element(i=0, frame=0, kind="heading", name="News", css="h1"),
        Element(
            i=1,
            frame=0,
            kind="control",
            role="button",
            name="Pause",
            css="#p",
            stop=True,
        ),
        Element(
            i=2, frame=0, kind="text", name="Press Ctrl+Shift+P to pause", css="#t"
        ),
        Element(i=3, frame=0, kind="text", name="Latest story", css="#c > p"),
        Element(i=4, frame=0, kind="text", name="Footer", css="footer"),
    ]
    r = Region(
        key="0|#c",
        frame=0,
        css="#c",
        tag="div",
        content_css="#c",
        changed_at=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        kinds=["updating"],
        text="Latest story",
        elements=[3],
    )
    mp = MotionPass(regions=[r], elements=els)
    return State2C(
        mp=mp,
        probes={"r1": probe},
        j1={"r1": j1} if j1 else {},
        j2=j2 or {},
        selected=["2.C"],
    )


def ctl(result, focus_only=None) -> Candidate:
    return Candidate(
        element=1, window="before", kind="control", result=result, focus_only=focus_only
    )


def txt(result="untried", key=None) -> Candidate:
    return Candidate(element=2, window="top", kind="text", result=result, key=key)


@pytest.mark.parametrize(
    "probe, j1, j2, outcome, row",
    [
        (Probe(), None, None, "NEEDS_REVIEW", "K7"),  # not probed yet
        (Probe(probed=True, reads_failed=True), None, None, "NEEDS_REVIEW", "K1"),
        (
            Probe(probed=True, candidates=[ctl("unreliable")]),
            None,
            None,
            "NEEDS_REVIEW",
            "K1",
        ),
        (
            Probe(probed=True, candidates=[ctl("stopped", "stopped")]),
            None,
            None,
            "NEEDS_REVIEW",
            "K2",
        ),
        (
            Probe(probed=True, candidates=[ctl("stopped", "no_effect")]),
            {"choice": "not_evident"},
            None,
            "FAIL",
            "K3/E1",
        ),
        (
            Probe(probed=True, candidates=[ctl("stopped", "no_effect")]),
            {"choice": "evident"},
            None,
            "NEEDS_REVIEW",
            "K3/E3",
        ),
        (
            Probe(probed=True, candidates=[ctl("slowed", "no_effect")]),
            {"choice": "unsure"},
            None,
            "NEEDS_REVIEW",
            "K3/E4",
        ),
        (
            Probe(
                probed=True,
                candidates=[ctl("no_effect"), txt("stopped", key="Control+Shift+P")],
            ),
            {"choice": "evident"},
            None,
            "NEEDS_REVIEW",
            "K4/E3",
        ),
        (
            Probe(probed=True, cannot_try="a field that needs a value"),
            None,
            None,
            "NEEDS_REVIEW",
            "K5",
        ),
        (Probe(probed=True, candidates=[ctl("no_effect")]), None, None, "FAIL", "K6"),
        # Text that mentions pausing needs J2 before K6 can hold.
        (
            Probe(probed=True, candidates=[ctl("no_effect"), txt()]),
            None,
            None,
            "NEEDS_REVIEW",
            "K8",
        ),
        (
            Probe(probed=True, candidates=[ctl("no_effect"), txt()]),
            None,
            {"r1-e2": {"choice": "no"}},
            "FAIL",
            "K6",
        ),
        (
            Probe(probed=True, candidates=[ctl("no_effect")], untried=2),
            None,
            None,
            "NEEDS_REVIEW",
            "K7",
        ),
        (
            Probe(probed=True, candidates=[ctl("unreachable")]),
            None,
            None,
            "NEEDS_REVIEW",
            "K7",
        ),
    ],
)
def test_instance_rows(probe, j1, j2, outcome, row):
    f = evaluate(_state(probe, j1, j2), ["evidence/2c.json"])
    assert f.outcome.value == outcome, (f.rows, f.summary)
    assert f"r1:{row}" in f.rows, f.rows
    assert (f.note is not None) == (f.outcome.value == "NEEDS_REVIEW")


def test_e2_pass_needs_every_er3_test(monkeypatch):
    """E2 is reachable only when every test the mechanism needs is built and
    selected (ER 3; plan Q4). Today 6.A, 7.A, 13.A ... are not built."""
    st = _state(
        Probe(probed=True, candidates=[ctl("stopped", "no_effect")]),
        {"choice": "evident"},
    )
    f = evaluate(st, [])
    assert "6.A" in f.summary and f.outcome.value == "NEEDS_REVIEW"
    monkeypatch.setattr(t2c, "er3_missing", lambda tests, selected: [])
    f = evaluate(st, [])
    assert f.outcome.value == "PASS" and "r1:K3/E2" in f.rows, f.rows


def test_questions():
    # J2 for text that mentions pausing; nothing for the plain text.
    st = _state(Probe(probed=True, candidates=[ctl("no_effect"), txt()]))
    assert [q.question_id for q in questions_for(st, [])] == ["2.C-r1-e2-J2"]
    # J1 once a control worked.
    st = _state(Probe(probed=True, candidates=[ctl("stopped", "no_effect")]))
    [q] = questions_for(st, [])
    assert q.question_id == "2.C-r1-J1" and q.input["mechanism"]["name"] == "Pause"
    # None before the probe exists.
    assert questions_for(_state(Probe()), []) == []
