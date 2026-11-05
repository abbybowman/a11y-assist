"""4.D (2.4.7-focus-visible): W3C ACT rule oj04fd cases (with DHS TT 5.1
results) and custom fixtures for gaps. Expected outcomes live in
tests/fixtures/act/manifest.json and here, never in a page."""

from __future__ import annotations

import json

import pytest

from a11y_assist.models import TestId

from .conftest import ACT_ROOT
from .harness import instance_rows, run_check

MANIFEST = json.loads((ACT_ROOT / "manifest.json").read_text())
ACT = {c["id"]: c for c in MANIFEST["cases"] if c["tt_test"] == "4.D"}
# What a correct judge answers where J1 is asked (test data).
ACT_CHOICE: dict[str, str] = {"dd9628d8": "yes"}


def test_oj04fd_cases_are_the_7_approved():
    assert len(ACT) == 7
    for c in ACT.values():
        assert c["dhs_tt51"] == c["expected"], c["id"]  # DHS agrees on all 7


@pytest.mark.parametrize("case_id", sorted(ACT))
async def test_act_case(case_id, settings, act_server):
    c = ACT[case_id]
    got = await run_check(
        settings, f"{act_server}/{c['path']}", TestId.T4D, ACT_CHOICE.get(case_id)
    )
    f = got["finding"]
    assert f.outcome.value == c["expected"], (f.rationale, f.summary, instance_rows(f))


# Custom fixtures (docs/rules/4d-focus-visible.md). "choice" is the scripted J1
# answer where J1 is asked.
EXPECTED: dict[str, dict] = {
    "f01-background-change": {"outcome": "PASS"},
    "f02-text-field-caret": {"outcome": "PASS"},
    "f03-skip-link": {"outcome": "PASS"},
    "f04-radio-label-highlight": {"outcome": "PASS"},
    "f05-outline-transition": {"outcome": "PASS"},
    "f06-slideshow-behind-links": {"outcome": "FAIL", "choice": "no"},
    "f07-sticky-header-covers": {"outcome": "FAIL"},
    "f08-focusable-iframe": {"outcome": "PASS"},
    "f09-faint-outline": {"outcome": "NEEDS_REVIEW", "choice": "unsure"},
    # ~59-62 s alone on the 2026-11-01 container (was ~55 s when the guard was
    # set), and over 65 s now and then under -n 8 with the full suite: 75 s
    # still catches a real slowdown (Abby, 2026-11-01). Pausing the mutation
    # log around 4.D's own screenshots costs ~2 s here (solutions/time-budget.md).
    "f10-100-links": {"outcome": "PASS", "max_s": 75},
    "f11-blur-on-focus": {"outcome": "FAIL", "rows": ["M3"]},
    "f12-listbox-activedescendant": {"outcome": "PASS"},
    "f13-listbox-no-highlight": {"outcome": "FAIL"},
    "f14-menubar-roving-no-indicator": {"outcome": "FAIL"},
}


def test_every_fixture_is_listed():
    from .conftest import FIXTURES

    assert {p.stem for p in (FIXTURES / "4d").glob("*.html")} == set(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
async def test_fixture(name, settings, server):
    import time

    e = EXPECTED[name]
    t0 = time.monotonic()
    got = await run_check(
        settings, f"{server.base}/4d/{name}.html", TestId.T4D, e.get("choice")
    )
    took = time.monotonic() - t0
    f = got["finding"]
    assert f.outcome.value == e["outcome"], (f.rows, f.summary)
    if "rows" in e:
        assert set(e["rows"]) <= set(instance_rows(f)), f.rows
    if "max_s" in e:
        assert took < e["max_s"], took
