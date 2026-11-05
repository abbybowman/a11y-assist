"""The run limit (4.C spec section 2, Run limits): a run that cannot finish
stops early and says so, a run that runs out of time is NEEDS REVIEW (never
PASS), and the caller can turn the limit off."""

from __future__ import annotations

import asyncio
import math

import pytest

from a11y_assist.models import Outcome, TestId
from a11y_assist.pipeline import TIME_NOTE, RunRefused, _bounded, run_tt_tests
from a11y_assist.traverse import PACE_WARM, Pace, WalkTooLong

from .drafts import drafts  # noqa: F401 (a fixture)


def test_pace_waits_for_warm_up_then_estimates(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("a11y_assist.traverse.time.monotonic", lambda: now[0])
    pace = Pace(deadline=160.0)
    pace.check(0, 600)  # starts the clock
    now[0] = 110.0
    pace.check(PACE_WARM - 1, 600)  # too early to judge
    # 20 presses in 10 s: 0.5 s a press x 100 stops x 1.5 = 75 s > 60 s left.
    with pytest.raises(WalkTooLong) as exc:
        pace.check(PACE_WARM, 100)
    assert exc.value.candidates == 100 and exc.value.presses == PACE_WARM
    assert exc.value.estimate_s == pytest.approx(75.0)


def test_pace_lets_a_walk_that_fits_continue(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("a11y_assist.traverse.time.monotonic", lambda: now[0])
    pace = Pace(deadline=200.0)
    pace.check(0, 60)
    now[0] = 104.0
    pace.check(PACE_WARM, 60)  # 0.2 s x 60 x 1.5 = 18 s: fits
    # More presses than the inventory (a growing page) count instead.
    now[0] = 200.0
    with pytest.raises(WalkTooLong):
        pace.check(300, 60)


async def test_bounded_cancels_at_the_hard_limit():
    async def slow():
        await asyncio.sleep(5)

    loop = asyncio.get_running_loop()
    with pytest.raises(TimeoutError):
        await _bounded(slow(), loop.time() + 0.05)
    with pytest.raises(TimeoutError):
        await _bounded(slow(), loop.time() - 1)  # already past: not started
    assert await _bounded(asyncio.sleep(0, "ok"), math.inf) == "ok"


async def test_page_too_large_is_refused_early_with_the_way_out(settings, server):
    # F10 (100 links) needs ~50 s of walk; a 30 s limit leaves 20 s.
    settings.run_limit_s = 30
    loop = asyncio.get_running_loop()
    t0 = loop.time()
    with pytest.raises(RunRefused) as exc:
        await run_tt_tests(
            settings, f"{server.base}/4d/f10-100-links.html", list(TestId)
        )
    took = loop.time() - t0
    msg = str(exc.value)
    assert "about 100 places the keyboard can reach" in msg
    assert "no_time_limit=true" in msg and "Nothing was tested" in msg
    assert took < 20, took  # stopped at the pace check, not at the limit
    # Never tested: no run folder is left.
    assert not settings.runs_dir.exists() or not any(settings.runs_dir.iterdir())


async def test_out_of_time_is_needs_review_and_no_time_limit_finishes(settings, server):
    url = f"{server.base}/no_trap.html"
    settings.run_limit_s = 10  # the reserve leaves no time for the walk
    out = await run_tt_tests(settings, url, [TestId.T4C, TestId.T4D])
    assert out.walk["P1"]["end"] == "time"
    assert {f.outcome for f in out.report.findings} == {Outcome.NEEDS_REVIEW}
    assert TIME_NOTE.format(limit=10) in out.errors
    assert out.report.versions.run_settings["no_time_limit"] is False

    out = await run_tt_tests(
        settings, url, [TestId.T4C, TestId.T4D], no_time_limit=True
    )
    assert out.errors == []
    assert out.walk["P1"]["end"] == "wrap"
    assert out.report.versions.run_settings["no_time_limit"] is True
    assert {f.outcome for f in out.report.findings} == {Outcome.PASS}


async def test_more_fields_than_5d_checks_leaves_out_only_5d(
    settings,
    server,
    drafts,  # noqa: F811
    monkeypatch,
):
    """5.D's cap (spec section 2, Run limits): over FIELD_MAX form fields 5.D
    is left out at the first load, with the call that runs it; the other
    tests still run (post-round 1 fix 12: a refusal cost the whole page).
    no_time_limit lifts the cap."""
    from a11y_assist.checks import t5d

    monkeypatch.setattr(t5d, "FIELD_MAX", 2)
    url = f"{server.base}/5d/f03-submit-when-last-field-filled.html"  # 3 fields
    out = await run_tt_tests(settings, url, [TestId.T4C, TestId.T5D])
    got = {f.test_id: f for f in out.report.findings}
    assert got[TestId.T4C].note is None  # performed
    d = got[TestId.T5D]
    assert d.outcome is Outcome.NEEDS_REVIEW and d.note
    assert "this page has 3 form fields" in d.summary and "at most 2" in d.summary
    assert 'tests ["5.D"] and no_time_limit=true' in d.summary
    assert any(e.startswith("5.D was not run: this page") for e in out.errors)
    # Only 5.D, over the cap: nothing to walk, no refusal, 5.D says why.
    out = await run_tt_tests(settings, url, [TestId.T5D])
    assert out.report.findings[0].note and "no_time_limit=true" in (
        out.report.findings[0].summary
    )
    # With the limit off, every field is filled in.
    out = await run_tt_tests(settings, url, [TestId.T5D], no_time_limit=True)
    filled = [i for i in out.report.findings[0].rows if i.startswith("f")]
    assert filled == ["f3:J1?"]  # the third field submits the form


async def test_slow_other_page_drops_only_the_page_tests(settings, server):
    # The other page answers after 16 s, past its 5 s share: 4.C still runs
    # in full; 9.B is not performed (never compared on fewer pages).
    settings.run_limit_s, settings.other_page_s = 60, 5
    loop = asyncio.get_running_loop()
    t0 = loop.time()
    out = await run_tt_tests(
        settings,
        f"{server.base}/no_trap.html",
        [TestId.T4C, TestId.T9B],
        other_pages=[f"{server.base}/slow.html"],
    )
    took = loop.time() - t0
    got = {f.test_id: f for f in out.report.findings}
    assert got[TestId.T4C].outcome is Outcome.PASS
    assert got[TestId.T9B].outcome is Outcome.NEEDS_REVIEW
    summary = got[TestId.T9B].summary
    assert "Other page 1 could not be recorded within its 5 s" in summary
    assert "no_time_limit=true" in " ".join(out.errors)
    assert out.report.other_pages == []
    assert took < 45, took
