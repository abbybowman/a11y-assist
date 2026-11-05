"""Pass T's own browser (plan Q1 and Q11): full Chromium, headless, with
autoplay allowed, launched only for the 2.x checks. The walk's browser is
unchanged."""

from __future__ import annotations

import json

from playwright.async_api import async_playwright

from a11y_assist.browser import MOTION_BROWSER, launch_browser, launch_for
from a11y_assist.capture import record, replay_context
from a11y_assist.egress import EgressProxy
from a11y_assist.models import TestId
from a11y_assist.motion import MOTION_INIT_JS, pass_t
from a11y_assist.pipeline import run_tt_tests

from .conftest import noop_log
from .drafts import drafts  # noqa: F401 (a fixture)


async def _watch(pw, settings, proxy, browser, url, tmp_path):
    rec = await launch_browser(pw, settings, proxy)
    cap = await record(rec, settings, url, tmp_path / "p.har.zip", noop_log)
    await rec.close()

    async def open_page():
        r = await replay_context(
            browser, settings, cap.har_path, noop_log, init_scripts=(MOTION_INIT_JS,)
        )
        page = await r.context.new_page()
        await r.guard.goto(page, cap.final_url)
        return r.context, page

    return cap, await pass_t(open_page, cap.har_path)


async def test_autoplay_plays_only_in_the_motion_browser(settings, server, tmp_path):
    """Item 1, as a test: on replay, autoplay audio stays paused without the
    flag and plays with it."""
    url = f"{server.base}/2x/t-autoplay.html"
    async with EgressProxy(settings) as proxy, async_playwright() as pw:
        plain = await launch_browser(pw, settings, proxy)
        motion = await launch_for(pw, settings, proxy, full=True, autoplay=True)
        _, a = await _watch(pw, settings, proxy, plain, url, tmp_path)
        _, b = await _watch(pw, settings, proxy, motion, url, tmp_path)
        await plain.close()
        await motion.close()

    def reads(mp):
        return [m for m in mp.media if m.css == "#a"]

    assert reads(a) and all(m.paused and m.time == 0 for m in reads(a)), reads(a)
    # Played: running at a read, and reached the end of the 4 s tone.
    assert any(not m.paused and m.time > 0 for m in reads(b)), reads(b)
    assert reads(b)[-1].time == reads(b)[-1].duration == 4.0, reads(b)


async def test_cross_site_frame_in_full_chromium(settings, server, tmp_path):
    """Item 16: regions and live regions inside an out-of-process frame."""
    async with EgressProxy(settings) as proxy, async_playwright() as pw:
        motion = await launch_for(pw, settings, proxy, full=True, autoplay=True)
        cap, mp = await _watch(
            pw,
            settings,
            proxy,
            motion,
            f"{server.base}/2x/t-frame-xsite.html",
            tmp_path,
        )
        cdp = await motion.new_browser_cdp_session()
        await motion.close()
    assert cap.cross_site_frames, cap
    assert mp.ok, mp.error
    inner = [r for r in mp.regions if r.frame > 0]
    assert [r.css for r in inner] == ["#tick"], mp.regions
    assert "localhost" in inner[0].frame_url
    assert all(c.live == "#tick" and c.live_at_start for c in inner[0].changes)
    assert [mp.elements[i].css for i in inner[0].elements] == ["#tick"]
    del cdp


async def test_run_uses_the_motion_browser(settings, server, drafts):  # noqa: F811
    res = await run_tt_tests(
        settings, f"{server.base}/2x/t-autoplay.html", [TestId.T2C, TestId.T2D]
    )
    run_dir = settings.runs_dir / res.run_id
    st = json.loads((run_dir / "evidence" / "2c.json").read_text())
    assert st["mp"]["browser"] == MOTION_BROWSER
    assert any(not m["paused"] for m in st["mp"]["media"]), st["mp"]["media"]
    steps = (run_dir / "steps.jsonl").read_text().replace(": ", ":")
    assert f'"kind":"{MOTION_BROWSER}"' in steps
    # The page itself (no cross-site frames) still replays in the shell.
    report = json.loads((run_dir / "report.json").read_text())
    assert report["replay_browser"] == "headless shell"


async def test_pass_t_runs_beside_the_walk(settings, server, drafts):  # noqa: F811
    """Plan Q2: pass T's browser starts before the walk ends, once, and the
    checks share that one watch."""
    res = await run_tt_tests(
        settings,
        f"{server.base}/2x/t-live-ticker.html",
        [TestId.T4C, TestId.T2C, TestId.T2D],
    )
    assert res.errors == [], res.errors
    path = settings.runs_dir / res.run_id / "steps.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    steps = [e["step"] for e in events]
    launched = [
        i
        for i, e in enumerate(events)
        if e["step"] == "browser_launched"
        and (e.get("detail") or {}).get("kind") == MOTION_BROWSER
    ]
    assert len(launched) == 1, launched  # one pass T browser, one watch
    assert launched[0] < steps.index("walk"), steps
    by = {f.test_id.value: f for f in res.report.findings}
    assert by["2.D"].outcome.value == "PASS", by["2.D"].rows
    assert "4.C" in by  # the walk ran beside it


async def test_moving_content_gets_ignored_and_more_time(settings, server, drafts):  # noqa: F811
    """T1 (a) and (b): pass T runs beside the walk; the ticker is handed to
    the settle rule and the run limit grows. (With only the walk's tests on a
    page this short, the run ends before pass T and cancels it: 2.D waits.)"""
    res = await run_tt_tests(
        settings, f"{server.base}/2x/t-ticker-below.html", [TestId.T4C, TestId.T2D]
    )
    assert res.errors == [], res.errors
    path = settings.runs_dir / res.run_id / "steps.jsonl"
    events = {
        json.loads(line)["step"]: json.loads(line)
        for line in path.read_text().splitlines()
    }
    assert events["settle_ignore"]["detail"]["regions"] == 1
    assert events["time_allowance"]["detail"]["seconds"] == settings.moving_allowance_s
