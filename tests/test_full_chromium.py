"""Pages with cross-site iframes replay in full Chromium, never the headless
shell (docs/solutions/full-chromium-iframes.md): the shell runs those frames
in-process, unlike the Chrome people use."""

from __future__ import annotations

from playwright.async_api import async_playwright

from a11y_assist.browser import (
    FULL_CHROMIUM,
    launch_browser,
    replay_browser_name,
    replay_in_full_chromium,
)
from a11y_assist.capture import cross_site_frames, record, replay_context
from a11y_assist.egress import EgressProxy
from a11y_assist.models import TestId
from a11y_assist.pipeline import run_tt_tests

from .conftest import noop_log


def test_cross_site_frames_are_other_hosts_without_query():
    top = "https://www.example.gov/a?x=1"
    got = cross_site_frames(
        top,
        [
            "https://www.example.gov/same",
            "about:blank",
            "data:text/html,hi",
            "https://www.youtube.com/embed/abc?autoplay=1#t",
            "https://cdn.example.gov/x",  # same site to Chrome; counted anyway
        ],
    )
    assert got == ["https://cdn.example.gov/x", "https://www.youtube.com/embed/abc"]


def test_which_browser_replays(settings):
    frames = ["https://www.youtube.com/embed/abc"]
    assert settings.browser_channel == "chromium" and settings.headless
    assert replay_in_full_chromium(settings, frames)
    assert not replay_in_full_chromium(settings, [])
    assert replay_browser_name(settings, frames) == FULL_CHROMIUM
    assert replay_browser_name(settings, []) == "headless shell"
    chrome = settings.model_copy(update={"browser_channel": "chrome"})
    assert not replay_in_full_chromium(chrome, frames)  # already out-of-process
    assert replay_browser_name(chrome, frames) == "chrome"
    headed = settings.model_copy(update={"headless": False})
    assert not replay_in_full_chromium(headed, frames)
    assert replay_browser_name(headed, []) == FULL_CHROMIUM


async def _iframe_targets(browser) -> int:
    cdp = await browser.new_browser_cdp_session()
    targets = (await cdp.send("Target.getTargets"))["targetInfos"]
    return sum(t["type"] == "iframe" for t in targets)


async def test_full_chromium_puts_the_frame_out_of_process(settings, server, tmp_path):
    """Why the rule exists: the same recording, replayed in each browser."""
    url = f"{server.base}/framed"
    async with EgressProxy(settings) as proxy, async_playwright() as pw:
        shell = await launch_browser(pw, settings, proxy)
        cap = await record(shell, settings, url, tmp_path / "p.har.zip", noop_log)
        assert cap.cross_site_frames == [f"http://localhost:{server.port}/inner"]
        full = await launch_browser(pw, settings, proxy, full_chromium=True)
        counts = []
        for b in (shell, full):
            r = await replay_context(b, settings, cap.har_path, noop_log)
            page = await r.context.new_page()
            await r.guard.goto(page, cap.final_url)
            await page.frame_locator("iframe").locator("button").wait_for()
            counts.append(await _iframe_targets(b))
            await r.context.close()
        await shell.close()
        await full.close()
    assert counts == [0, 1]  # in-process in the shell, out-of-process in full


async def test_run_records_and_uses_full_chromium(settings, server):
    res = await run_tt_tests(settings, f"{server.base}/framed", [TestId.T4C])
    run_dir = settings.runs_dir / res.run_id
    report = (run_dir / "report.json").read_text()
    assert f'"replay_browser": "{FULL_CHROMIUM}"' in report
    assert "/inner" in report
    steps = (run_dir / "steps.jsonl").read_text()
    assert '"kind":"full Chromium"' in steps.replace(": ", ":")


async def test_page_without_frames_stays_in_the_shell(settings, server):
    res = await run_tt_tests(settings, f"{server.base}/dyn", [TestId.T4C])
    run_dir = settings.runs_dir / res.run_id
    assert '"replay_browser": "headless shell"' in (run_dir / "report.json").read_text()
    assert "full Chromium" not in (run_dir / "steps.jsonl").read_text()
