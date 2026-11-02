"""9.A, 9.B and 9.C on custom multi-page fixtures (tests/fixtures/9x/): no
W3C ACT rule or Baseline Alignment case covers 9.B or 9.C, and these fill
9.A's gaps. Each case is a tested page plus the other pages it is compared
with; all three tests run in one call. Expected outcomes and scripted
answers (what a correct agent would say) live here, never in a page."""

from __future__ import annotations

import pytest

from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_tests

DOC = {"choice": "documented", "key": "Alt+S", "quote": "press Alt+S to skip"}

# case -> (tested page, other pages, {test: expected outcome}, answers)
EXPECTED: dict[str, tuple[str, list[str], dict[str, str], dict]] = {
    "consistent-site": (
        "a1-home",
        ["a2-benefits"],
        {"9.A": "PASS", "9.B": "PASS", "9.C": "PASS"},
        {},
    ),
    "nav-reordered": (
        "a1-home",
        ["a3-nav-reordered"],
        {"9.A": "PASS", "9.B": "FAIL", "9.C": "PASS"},
        {},
    ),
    "nav-css-order": ("a1-home", ["a4-nav-css-order"], {"9.B": "FAIL"}, {}),
    "two-pages-one-reordered": (
        "a1-home",
        ["a2-benefits", "a3-nav-reordered"],
        {"9.B": "FAIL", "9.C": "PASS"},
        {},
    ),
    "renamed": (
        "a1-home",
        ["a5-renamed"],
        {"9.A": "PASS", "9.B": "PASS", "9.C": "FAIL"},
        {"9.C": {"J1": {"choice": "inconsistent"}}},
    ),
    "unrelated": (
        "a1-home",
        ["c1-unrelated"],
        {"9.A": "DNA", "9.B": "DNA", "9.C": "DNA"},
        {},
    ),
    "skip-past-heading": ("b1-skip-past-heading", ["a2-benefits"], {"9.A": "FAIL"}, {}),
    "skip-after-nav": ("b2-skip-after-nav", ["a2-benefits"], {"9.A": "FAIL"}, {}),
    "documented-key": (
        "b3-documented-key",
        ["a2-benefits"],
        {"9.A": "PASS"},
        {"9.A": {"J1": DOC}},
    ),
    "breadcrumbs-repeated": (
        "b4-no-main-breadcrumbs",
        ["a2-benefits"],
        {"9.A": "PASS"},
        {"9.A": {"J2": {"choice": "repeated"}}},
    ),
    "breadcrumbs-not-repeated": (
        "b4-no-main-breadcrumbs",
        ["a2-benefits"],
        {"9.A": "FAIL"},
        {"9.A": {"J2": {"choice": "not_repeated"}}},
    ),
    "two-links": ("b5-two-links", ["b6-sibling-with-aside"], {"9.A": "PASS"}, {}),
    "paging": (
        "d1-page4",
        ["d2-page5"],
        {"9.A": "DNA", "9.B": "PASS", "9.C": "PASS"},
        {"9.C": {"J1": {"choice": "consistent"}}},
    ),
}

# Rules tests only, left out of the judge eval: the same page and question
# as another case with the opposite scripted answer.
NOT_EVAL = {"breadcrumbs-not-repeated"}

ROWS = {
    ("skip-past-heading", "9.A"): ["M8"],
    ("documented-key", "9.A"): ["M7"],  # the documented key, pressed
    ("breadcrumbs-repeated", "9.A"): ["M9"],
    ("nav-reordered", "9.B"): ["N3"],
    ("nav-css-order", "9.B"): ["N4"],
    ("renamed", "9.C"): ["C1"] * 10 + ["C4", "C4"],
    ("paging", "9.C"): ["C1", "C3", "C3"],
}


@pytest.mark.parametrize("case", sorted(EXPECTED))
async def test_case(case, settings, server, drafts):  # noqa: F811
    page, others, want, answers = EXPECTED[case]
    got = await run_tests(
        settings,
        f"{server.base}/9x/{page}.html",
        list(want),
        answers,
        other_pages=[f"{server.base}/9x/{o}.html" for o in others],
    )
    for t, outcome in want.items():
        f = got[t]
        assert f.outcome.value == outcome, (t, f.rows, f.summary)
        if (case, t) in ROWS:
            assert sorted(instance_rows(f)) == sorted(ROWS[(case, t)]), f.rows
