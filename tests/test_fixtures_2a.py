"""2.A end to end on custom pages in tests/fixtures/2x/ (draft check,
tests/drafts.py), with generated audio from the test server (/tone20.wav,
/silence20.wav). Expected outcomes and scripted answers live here, never in
a page."""

from __future__ import annotations

import pytest

from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_tests

# page: (answers, outcome, a row that must appear)
CASES = {
    # "Stop sound" is the first element and pauses it: works; ER 3 gates PASS.
    "t-audio-stop-first": ({}, "NEEDS_REVIEW", "K3/E3"),
    # The same button as the fifth element: outside the first three, K6.
    "t-audio-stop-fifth": ({}, "FAIL", "K6"),
    # Not instances: silent (loudness), 2 s long, muted.
    "t-audio-silent": ({}, "DNA", "A3"),
    "t-audio-short": ({}, "DNA", "A3"),
    "t-audio-muted": ({}, "DNA", "A3"),
    # The first text names a key; J2 gives it; the tool presses it once.
    "t-audio-hotkey": (
        {"J2": {"choice": "describes", "key": "Ctrl+Shift+M"}},
        "NEEDS_REVIEW",
        "K4/E3",
    ),
    "t-audio-hotkey-no": ({"J2": {"choice": "no"}}, "FAIL", "K6"),
    # The audio's own controls, first on the page (V1): Tab reaches its play
    # button inside the element, and Enter pauses it.
    "t-audio-native": ({}, "NEEDS_REVIEW", "K3/E3"),
    # Audio in a cross-site frame (full Chromium, out of process), with its
    # "Stop sound" button first in the frame, the page's first element.
    "t-audio-frame": ({}, "NEEDS_REVIEW", "K3/E3"),
    # Web Audio: no bytes to measure (A2).
    "t-webaudio": ({}, "NEEDS_REVIEW", "A2"),
}


@pytest.mark.parametrize("case", sorted(CASES))
async def test_page(case, settings, server, drafts):  # noqa: F811
    answers, outcome, row = CASES[case]
    page = case.removesuffix("-no")
    got = await run_tests(
        settings, f"{server.base}/2x/{page}.html", ["2.A"], {"2.A": answers}
    )
    f = got["2.A"]
    assert f.outcome.value == outcome, (f.rows, f.summary)
    have = [*f.rows, *instance_rows(f)]
    assert any(r == row or r.endswith(row) for r in have), (row, f.rows)


# For the judge eval: page -> the outcome a correct agent gets.
EVAL = {"t-audio-hotkey": "NEEDS_REVIEW"}  # J2 gives Ctrl+Shift+M; K4, E3
