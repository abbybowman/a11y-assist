"""2.C and 2.D end to end on custom pages in tests/fixtures/2x/ (draft
checks, tests/drafts.py). Expected outcomes and scripted answers live here,
never in a page. 2.C stays NEEDS REVIEW wherever it applies until the
mechanism probe tries controls with the keyboard; its rows are also tested
on hand-built evidence in test_rows_2x.py."""

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
    # No control near the content or at the top of the page: K6.
    "t-live-ticker.html": ("FAIL", ["K6"], "PASS", ["N2"]),
    "t-no-control.html": ("FAIL", ["K6"], "FAIL", ["N5"]),
    "t-pause-far.html": ("FAIL", ["K6"], "FAIL", ["N5"]),
    # Five instances: three are probed (K6), the rest are not (K7).
    "t-live.html": ("FAIL", ["K6", "K7"], "FAIL", ["N2", "N5"]),
    "t-carousels.html": ("FAIL", ["K6"], "FAIL", ["N5"]),
    # Starts only when scrolled into view: the scrolled watch finds it (Q3).
    "t-scroll-start.html": ("FAIL", ["K6"], "FAIL", ["N5"]),
    # It stops while its own Previous button has focus: never PASS.
    "t-focus-pause.html": ("NEEDS_REVIEW", ["K2"], "FAIL", ["N5"]),
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


@pytest.mark.parametrize(
    "page, answers, outcome, row",
    [
        # The pause button just before the ticker stops it; J1 decides
        # evident, and ER 3 holds PASS back until 6.A, 13.C ... are built.
        ("t-pause-button.html", {"J1": {"choice": "evident"}}, "NEEDS_REVIEW", "K3/E3"),
        ("t-pause-button.html", {"J1": {"choice": "not_evident"}}, "FAIL", "K3/E1"),
        # The page's first text names a key; J2 gives it, the tool presses it
        # once, and it stops the counter.
        (
            "t-hotkey.html",
            {
                "J2": {"choice": "describes", "key": "Ctrl+Shift+P"},
                "J1": {"choice": "evident"},
            },
            "NEEDS_REVIEW",
            "K4/E3",
        ),
        ("t-hotkey.html", {"J2": {"choice": "no"}}, "FAIL", "K6"),
        # A button that stops it but says "Options": works, not evident (E1).
        ("t-options-button.html", {"J1": {"choice": "not_evident"}}, "FAIL", "K3/E1"),
        # A control that makes it update less often counts for 2.C (a
        # frequency control): judged on the time between two changes.
        ("t-slower.html", {"J1": {"choice": "evident"}}, "NEEDS_REVIEW", "K3/E3"),
    ],
)
async def test_2c_mechanism(page, answers, outcome, row, settings, server, drafts):  # noqa: F811
    got = await run_tests(
        settings, f"{server.base}/2x/{page}", ["2.C"], {"2.C": answers}
    )
    f = got["2.C"]
    assert f.outcome.value == outcome, (f.rows, f.summary)
    assert any(r.endswith(row) for r in f.rows), f.rows


async def test_a2_note_says_what_was_checked(settings, server, drafts):  # noqa: F811
    """O1 (Abby, 2026-11-04): the note says how long we watched, what we
    looked for, and what changed and when it stopped."""
    got = await run_tests(settings, f"{server.base}/2x/t-spinner.html", ["2.C"], {})
    s = got["2.C"].summary
    assert "6.5 seconds" in s and "after 5 seconds" in s, s
    assert "changed until" in s and "and then stopped" in s, s


# For the judge eval (evals/judge_eval.py): pages whose outcome a fresh
# agent's answers decide, with the outcome a correct agent gets.
EVAL = {
    "t-pause-button": ("2.C", "NEEDS_REVIEW"),  # evident; ER 3 holds PASS back
    "t-options-button": ("2.C", "FAIL"),  # "Options" is not evident
    "t-slower": ("2.C", "NEEDS_REVIEW"),  # "Update less often": evident
    "t-hotkey": ("2.C", "NEEDS_REVIEW"),  # J2 gives Ctrl+Shift+P, then J1
    "t-focus-news": ("2.D", "PASS"),  # "New message 3 from Ana" says it
    "t-update-dialog": ("2.D", "PASS"),  # "Prices were updated."
}


async def test_2d_explains_a_carousel_with_announcements_off(settings, server, drafts):  # noqa: F811
    """Plan risk 11: W3C's carousel pattern sets aria-live="off" while it
    rotates; TT 2.D still fails it, and the note says why."""
    got = await run_tests(
        settings, f"{server.base}/2x/t-apg-carousel.html", ["2.D"], {}
    )
    f = got["2.D"]
    assert f.outcome.value == "FAIL", (f.rows, f.summary)
    assert 'aria-live="off"' in f.summary, f.summary
