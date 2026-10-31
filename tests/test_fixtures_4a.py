"""4.A (2.1.1-keyboard-access) on W3C ACT cases (akn7bn, 0ssw9k) and custom
fixtures for gaps, plus rules unit tests for rows no page triggers reliably.
Section 508 Baseline cases are in test_baseline_cases.py. Expected outcomes
and scripted answers (what a correct agent would say) live here and in the
manifests, never in a page."""

from __future__ import annotations

import json
import re

import pytest

from a11y_assist.checks import t4a
from a11y_assist.models import Outcome, TestId

from .conftest import ACT_ROOT, FIXTURES
from .harness import instance_rows, run_check
from .scoring import write_score

NO_ALT = {"J1": {"choice": "no_alternative"}}

EXPECTED: dict[str, dict] = {
    "f01-click-only-text": {"outcome": "FAIL", "rows": ["M6"], "choice": NO_ALT},
    "f02-custom-button-ignores-keys": {"outcome": "FAIL", "rows": ["M10"]},
    "f03-custom-button-with-keys": {"outcome": "PASS", "rows": ["M8"]},
    "f04-hover-only-menu": {"outcome": "FAIL", "rows": ["M6", "M6"], "choice": NO_ALT},
    "f05-hover-and-focus-menu": {"outcome": "PASS", "rows": []},
    "f06-print-icon-and-button": {
        "outcome": "PASS",
        "rows": ["M5"],
        "choice": {"J1": {"choice": "alternative", "element": 1}},
    },
    "f07-same-address-link": {"outcome": "PASS", "rows": ["M3"]},
    "f08-title-only-format": {
        "outcome": "FAIL",
        "rows": ["M14"],
        "choice": {"J2": {"choice": "essential"}},
    },
    "f09-title-repeats-label": {"outcome": "PASS", "rows": ["M11"]},
    "f10-canvas-map": {"outcome": "NEEDS_REVIEW", "rows": ["M16"]},
    "f11-pointer-cursor-decoration": {"outcome": "PASS", "rows": ["M2", "M2"]},
    "f12-roving-tabs": {"outcome": "PASS", "rows": []},
}

ACT = {
    c["id"]: c
    for c in json.loads((ACT_ROOT / "manifest.json").read_text())["cases"]
    if c["tt_test"] == "4.A"
}
ANSWERS = {"62673162": NO_ALT, "aa153f67": NO_ALT}


def test_every_fixture_is_listed():
    names = {p.stem for p in (FIXTURES / "4a").glob("*.html")}
    assert names == set(EXPECTED)
    for n in names:
        assert re.fullmatch(r"f\d{2}-[a-z0-9-]+", n), n


@pytest.mark.parametrize("name", sorted(EXPECTED))
async def test_outcome(name, settings, server):
    e = EXPECTED[name]
    got = await run_check(
        settings, f"{server.base}/4a/{name}.html", TestId.T4A, e.get("choice")
    )
    f = got["finding"]
    assert (f.outcome.value, instance_rows(f)) == (e["outcome"], e["rows"]), (
        f.rationale,
        f.summary,
    )


@pytest.mark.parametrize("case_id", sorted(ACT))
async def test_act_case(case_id, settings, act_server):
    case = ACT[case_id]
    got = await run_check(
        settings, f"{act_server}/{case['path']}", TestId.T4A, ANSWERS.get(case_id)
    )
    outcome = got["finding"].outcome.value
    write_score(case_id, outcome, got["finding"].rows)
    assert outcome == case["expected"], got["finding"].rationale


async def test_pass_says_what_was_looked_for_and_the_browser(settings, server):
    got = await run_check(
        settings, f"{server.base}/4a/f05-hover-and-focus-menu.html", TestId.T4A
    )
    s = got["finding"].summary
    assert "We looked for" in s and "Results are for the browser used" in s


# ── Rules on recorded evidence (rows no page triggers reliably) ──────────────


def _state(*insts: t4a.Inst4A, incomplete: list[str] | None = None) -> t4a.State4A:
    return t4a.State4A(
        p1={"end": "wrap"},
        p2={"end": "wrap"},
        stops=2,
        inventory=2,
        targets=2,
        stop_list=[
            t4a.StopRef(n=1, path_key="#a", role="link", name="A", index=0),
            t4a.StopRef(n=2, path_key="#b", role="button", name="B", index=1),
        ],
        instances=list(insts),
        incomplete=incomplete or [],
    )


def _k(**kw) -> t4a.Inst4A:
    return t4a.Inst4A(
        id="k1",
        kind="K",
        target={"css_path": "#k", "name": "K", "reason": "native"},
        **kw,
    )


def _x(**kw) -> t4a.Inst4A:
    return t4a.Inst4A(
        id="x1", kind="X", target={"css_path": "#x", "name": "X"}, keys=["Tab"], **kw
    )


EFF = t4a.Effect(kinds=["dom"], mutations=1)
NONE = t4a.Effect()
NOISY = t4a.Effect(kinds=["dom"], mutations=2, noise=3)


@pytest.mark.parametrize(
    ("inst", "outcome", "row"),
    [
        (_k(checked=False), "NEEDS_REVIEW", "C?"),
        (_k(unreliable=True), "NEEDS_REVIEW", "M1"),
        (_x(enter=NOISY), "NEEDS_REVIEW", "M1"),
        (_k(j={"choice": "unsure"}), "NEEDS_REVIEW", "M7"),
        # The named alternative must be a stop; otherwise it is unsure.
        (_k(j={"choice": "alternative", "element": 9}), "NEEDS_REVIEW", "M7"),
        (_k(j={"choice": "alternative", "element": 2}), "PASS", "M5"),
        (_x(enter=NONE, space=EFF), "PASS", "M8"),
        (_x(enter=NONE, space=NONE, click=NONE), "PASS", "M9"),
        (
            t4a.Inst4A(
                id="t1",
                kind="T",
                target={"name": "T"},
                title="x",
                elsewhere=False,
                j={"choice": "not_essential"},
            ),
            "PASS",
            "M13",
        ),
        (
            t4a.Inst4A(
                id="t1",
                kind="T",
                target={"name": "T"},
                title="x",
                elsewhere=False,
                j={"choice": "unsure"},
            ),
            "NEEDS_REVIEW",
            "M15",
        ),
    ],
)
def test_rows_on_recorded_evidence(inst, outcome, row):
    f = t4a.evaluate(_state(inst), [])
    page = {"M9": "PASS", "M5": "PASS", "M8": "PASS", "M13": "PASS"}.get(row, outcome)
    assert (f.outcome.value, instance_rows(f)) == (page, [row]), f.rationale


def test_incomplete_scan_is_never_pass():
    f = t4a.evaluate(_state(incomplete=["The run time limit was reached."]), [])
    assert f.outcome is Outcome.NEEDS_REVIEW and f.note


def test_p1_without_wrap_is_never_pass():
    st = _state()
    st.p1 = {"end": "stuck"}
    assert t4a.evaluate(st, []).outcome is Outcome.NEEDS_REVIEW


async def test_shadow_and_frame_stops_are_reached(settings, server):
    # no_trap.html: a button in a shadow root, one in a frame, and an inert
    # role=button div that neither keys nor a click change (not an instance).
    got = await run_check(settings, f"{server.base}/no_trap.html", TestId.T4A)
    f = got["finding"]
    assert (f.outcome.value, instance_rows(f)) == ("PASS", ["M9"]), f.rationale
