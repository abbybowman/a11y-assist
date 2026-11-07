"""3.A end to end on custom pages in tests/fixtures/3a/ (draft check,
tests/drafts.py). No ACT rule, DHS verdict or Baseline Alignment case
exists for 2.3.1 (spec, Other sources), so every page is custom; expected
outcomes live here, never in a page. Each page runs once: the stepped
capture is about 180 screenshots."""

from __future__ import annotations

import pytest

from tobi508.models import TestId

from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_check

# page: (outcome, rows that must appear, words the summary must hold)
CASES = {
    # No trigger fires: no capture (A4 at no further cost).
    "f01-static": ("DNA", ["A4"], ["does not apply"]),
    # 1 flash a second: no trigger (2.B's, not 3.A's).
    "f02-blink-1hz": ("DNA", ["A4"], []),
    # 40 x 40 at 5 a second: flashing found, under the area.
    "f03-css-5hz-small": (
        "NOT_TESTED",
        ["A2", "F5"],
        ["does not fail", "5 flashes per second", "1,600"],
    ),
    # 400 x 300 by a timer every 80 ms: fails (general).
    "f04-timer-6hz-large": (
        "NOT_TESTED",
        ["A2", "F2"],
        ["fails WCAG 2.3.1", "light and dark"],
    ),
    # A canvas redrawn every frame: real-time screenshots alias it; stepped, it fails.
    "f05-raf-strobe": ("NOT_TESTED", ["A2", "F2"], ["fails"]),
    # Red and a grey of the same luminance: red flashes only.
    "f06-red-strobe": ("NOT_TESTED", ["A2", "F3"], ["red flashing"]),
    # Exactly 3 flashes a second (G19): the trigger fires, the count is 6.
    "f07-exactly-3": ("DNA", ["A4"], []),
    # Seven changes once, after the load: only the screencast sees it.
    "f08-seven-transitions": ("NOT_TESTED", ["A2"], ["3.5 flashes per second"]),
    # An animated image, decoded: fails.
    "f09-gif-5hz-large": ("NOT_TESTED", ["A2", "F2"], ["animated image"]),
    # A video, decoded at full screen: fails.
    "f10-video-strobe": ("NOT_TESTED", ["A2", "F2"], ["video"]),
    # Flashing from 12 s: past the 10 s analyzed.
    "f11-video-late-flash": ("NEEDS_REVIEW", ["A3"], ["first 10 seconds"]),
    # 2 px squares inverting: the cells average out, the pixels flash.
    "f12-checkerboard-fine": ("NOT_TESTED", ["A2", "F1"], ["fine pattern"]),
    # A CSS flasher beside an animated image, each 12,000 px: together over
    # the area, but their times cannot be aligned.
    "f13-mixed": ("NOT_TESTED", ["A2", "F4"], ["several places"]),
    # A strobe in a cross-site frame (full Chromium, out of process).
    "f14-strobe-in-iframe": ("NOT_TESTED", ["A2", "F2"], ["fails"]),
    # SMIL steps with setCurrentTime (V7); only the screencast triggers it.
    "f15-smil-strobe": ("NOT_TESTED", ["A2", "F2"], ["fails"]),
    # 2.B's marquee page: a marquee runs by the wall clock (V7): not measured.
    "../2x/t-marquee": ("NEEDS_REVIEW", ["A3"], ["marquee"]),
}


@pytest.mark.parametrize("case", sorted(CASES))
async def test_page(case, settings, server, drafts):  # noqa: F811
    outcome, rows, words = CASES[case]
    got = await run_check(settings, f"{server.base}/3a/{case}.html", TestId.T3A)
    f = got["finding"]
    have = [*f.rows, *instance_rows(f)]
    assert f.outcome.value == outcome, (f.rows, f.summary)
    for r in rows:
        assert any(h == r or h.endswith(":" + r) for h in have), (r, f.rows)
    for w in words:
        assert w in f.summary, (w, f.summary)
    assert got["asked"] == []  # 3.A asks no questions (spec section 4)
