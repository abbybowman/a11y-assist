"""2.C and 2.D end to end on custom pages in tests/fixtures/2x/ (draft
checks, tests/drafts.py). Expected outcomes and scripted answers live here,
never in a page. 2.C stays NEEDS REVIEW wherever it applies until the
mechanism probe is built (K7); its rows are tested on hand-built evidence in
test_rows_2x.py."""

from __future__ import annotations

import pytest

from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_tests

# page: (2.C outcome, 2.C rows that must appear, 2.D outcome, 2.D rows)
CASES = {
    "t-elements.html": ("DNA", ["A3"], "DNA", ["A2"]),
    "t-only-clock.html": ("DNA", ["A4"], "DNA", ["A2"]),
    "t-polling.html": ("NEEDS_REVIEW", ["A2"], "NEEDS_REVIEW", ["A1"]),
    "t-spinner.html": ("NEEDS_REVIEW", ["A2"], "NEEDS_REVIEW", ["A1"]),
    "t-live-ticker.html": ("NEEDS_REVIEW", ["K7"], "PASS", ["N2"]),
    "t-live.html": ("NEEDS_REVIEW", ["K7"], "FAIL", ["N2", "N5"]),
    "t-carousels.html": ("NEEDS_REVIEW", ["K7"], "FAIL", ["N5"]),
}


@pytest.mark.parametrize("page", sorted(CASES))
async def test_page(page, settings, server, drafts):  # noqa: F811
    c_out, c_rows, d_out, d_rows = CASES[page]
    got = await run_tests(settings, f"{server.base}/2x/{page}", ["2.C", "2.D"], {})
    c, d = got["2.C"], got["2.D"]
    assert c.outcome.value == c_out, (c.rows, c.summary)
    assert d.outcome.value == d_out, (d.rows, d.summary)
    for want, f in ((c_rows, c), (d_rows, d)):
        have = (
            set(f.rows)
            | set(instance_rows(f))
            | {p for r in instance_rows(f) for p in r.split("/")}
        )
        assert set(want) <= have, (want, f.rows)


@pytest.mark.parametrize(
    "page, q, choice, outcome",
    [
        ("t-focus-news.html", "J1", "sufficient", "PASS"),
        ("t-focus-news.html", "J1", "not_sufficient", "FAIL"),
        ("t-update-dialog.html", "J2", "sufficient", "PASS"),
        ("t-update-dialog.html", "J2", "unsure", "NEEDS_REVIEW"),
    ],
)
async def test_2d_questions(page, q, choice, outcome, settings, server, drafts):  # noqa: F811
    got = await run_tests(
        settings,
        f"{server.base}/2x/{page}",
        ["2.D"],
        {"2.D": {q: {"choice": choice}}},
    )
    f = got["2.D"]
    assert f.outcome.value == outcome, (f.rows, f.summary)
    row = {"J1": "N4", "J2": "N3"}[q]
    want = f"{row}/{q}" if choice != "unsure" else f"{row}/N6"
    assert any(r.endswith(want) for r in f.rows), f.rows
