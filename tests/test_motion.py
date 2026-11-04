"""Pass T (motion.py) on custom pages in tests/fixtures/2x/: the facts the
2.x checks will read. No outcomes here (CLAUDE.md principle 2).

These run in the suite's browser (the headless shell, or TEST_BROWSER_CHANNEL)
without the autoplay flag: none of these pages has media. Which browser
pass T gets in a real run is the pipeline's (plan Q1, Q11)."""

from __future__ import annotations

from pathlib import Path

import pytest

from a11y_assist.capture import record, replay_context
from a11y_assist.motion import (
    MOTION_INIT_JS,
    MotionPass,
    changed_tiles,
    components,
    pass_t,
)

from .conftest import noop_log


async def watch(settings, browser, server, name: str, tmp_path: Path) -> MotionPass:
    har = tmp_path / "page.har.zip"
    url = f"{server.base}/2x/{name}"
    cap = await record(browser, settings, url, har, noop_log)

    async def open_page():
        r = await replay_context(
            browser, settings, har, noop_log, init_scripts=(MOTION_INIT_JS,)
        )
        page = await r.context.new_page()
        await r.guard.goto(page, cap.final_url)
        return r.context, page

    return await pass_t(open_page, har, tmp_path / "shots", tmp_path)


def by_id(mp: MotionPass, css: str):
    """The region whose element or content is `css` (e.g. "#ticker")."""
    hits = [r for r in mp.regions if r.css == css or r.content_css == css]
    hits += [r for r in mp.regions if r.css.startswith(css + " ")]
    return hits[0] if hits else None


def test_tiles_and_components():
    from PIL import Image

    a = Image.new("RGB", (100, 60), "white")
    b = a.copy()
    b.putpixel((5, 5), (0, 0, 0))  # tile (0, 0)
    b.putpixel((25, 5), (0, 0, 0))  # tile (1, 0), touching
    b.putpixel((95, 55), (0, 0, 0))  # tile (4, 2), apart
    tiles = changed_tiles(a, b)
    assert set(tiles) == {(0, 0), (1, 0), (4, 2)}
    assert tiles[(1, 0)] == [25, 5, 26, 6]  # the changed pixels' box
    groups = components(set(tiles))
    assert [len(g) for g in groups] == [2, 1]
    assert changed_tiles(a, a.copy()) == {}


async def test_kinds(settings, browser, server, tmp_path):
    mp = await watch(settings, browser, server, "t-motion-kinds.html", tmp_path)
    assert mp.ok, mp.error
    assert len(mp.frames) >= 12 and mp.frames[-1] >= 6.4
    assert len(mp.reads) == 3 and len(mp.shots) == len(mp.frames)
    # Still changing after 5 s, pixels only: moving.
    for css in ("#css-inf", "#marq", "#cv"):
        r = by_id(mp, css)
        assert r is not None, (css, [x.css for x in mp.regions])
        assert r.changed_at[-1] >= 5, (css, r.changed_at)
        assert "moving" in r.kinds and "updating" not in r.kinds, (css, r.kinds)
    # Text that changes every second: updating, with its DOM changes.
    t = by_id(mp, "#t")  # the span that changes, inside #ticker
    assert t is not None and "updating" in t.kinds, t
    assert t.changed_at[-1] >= 5 and 0.8 <= (t.period_s or 0) <= 1.6, t.changed_at
    assert any(c.kind in ("text", "children") for c in t.changes)
    # The elements inside it, by index into the page's elements.
    assert [mp.elements[i].css for i in t.elements] == ["#t"], t.elements
    # Stopped before 5 s: the 3 s animation and the spinner removed at 2 s.
    for css in ("#css-3s", "#spinner"):
        r = by_id(mp, css)
        assert r is not None and r.changed_at[-1] < 4.5, (css, r and r.changed_at)
    # Never changed: the static text, the focused field (the caret is hidden).
    assert by_id(mp, "#field") is None
    assert not any("p" == r.tag and "intro" in r.text.lower() for r in mp.regions)
    # The 10 s slide never changed in the watch, but its timer was seen.
    assert by_id(mp, "#slow") is None
    assert any(t.kind == "interval" and t.ms == 10000 for t in mp.timers)
    assert any(t.kind == "timeout" and t.ms == 2000 for t in mp.timers)
    # The autofocus happened at load, before the watch: not a focus move.
    assert mp.focus_moves == []


async def test_live_regions(settings, browser, server, tmp_path):
    mp = await watch(settings, browser, server, "t-live.html", tmp_path)
    assert mp.ok, mp.error
    live = {lr.css: lr for lr in mp.live_regions}
    assert "#polite" in live and "#timer" in live
    assert "#off" not in live  # aria-live="off" is not a live region

    def changes(css):
        r = by_id(mp, css)
        assert r is not None and "updating" in r.kinds, (css, mp.regions)
        assert r.changes, css
        return r.changes

    assert all(c.live == "#polite" and c.live_at_start for c in changes("#polite"))
    assert all(c.live == "#timer" and c.live_at_start for c in changes("#timer"))
    assert all(c.live is None for c in changes("#plain"))
    assert all(c.live is None for c in changes("#off"))
    # The live region added with its text: never one that existed at 0 s.
    late = changes("#late")
    assert late and not any(c.live_at_start for c in late)


async def test_carousels(settings, browser, server, tmp_path):
    mp = await watch(settings, browser, server, "t-carousels.html", tmp_path)
    assert mp.ok, mp.error
    fade = by_id(mp, "#fade")
    assert fade is not None and fade.carousel and fade.css == "#fade", mp.regions
    assert "updating" in fade.kinds, fade
    # Slides that slide inside a clipped track: what is shown changes.
    track = by_id(mp, "#track-wrap") or by_id(mp, "#track")
    assert track is not None and "updating" in track.kinds, (track, mp.regions)
    assert 1.0 <= (fade.period_s or 0) <= 2.0, fade.changed_at


async def test_dialog_and_focus(settings, browser, server, tmp_path):
    mp = await watch(settings, browser, server, "t-dialog-focus.html", tmp_path)
    assert mp.ok, mp.error
    assert [d["css"] for d in mp.dialogs_opened] == ["#dlg"]
    assert any(f.css == "#news" and 1 <= f.t <= 3 for f in mp.focus_moves), (
        mp.focus_moves
    )


async def test_frame(settings, browser, server, tmp_path):
    mp = await watch(settings, browser, server, "t-frame.html", tmp_path)
    assert mp.ok, mp.error
    inner = [r for r in mp.regions if r.frame > 0]
    assert len(inner) == 1, inner
    [r] = inner
    assert r.css == "#tick" and "updating" in r.kinds, r
    assert r.frame_url.endswith("/2x/t-frame-inner.html")
    assert any(lr.frame == r.frame and lr.css == "#tick" for lr in mp.live_regions)
    assert all(c.live == "#tick" and c.live_at_start for c in r.changes)
    assert mp.frames_read == 2
    # Its elements are the frame's, counted inline after the top page's.
    inside = [mp.elements[i] for i in r.elements]
    assert [e.css for e in inside] == ["#tick"] and inside[0].frame == r.frame
    assert [e.name for e in mp.elements][:3] == [
        "Ticker in a frame",
        "Text before the frame.",
        "Inner static text.",
    ]


async def test_polling_is_in_the_har(settings, browser, server, tmp_path):
    mp = await watch(settings, browser, server, "t-polling.html", tmp_path)
    assert mp.ok, mp.error
    # Recording stops once the network is idle, so the HAR may hold only one
    # or two polls; the requests during the watch show the rest.
    [p] = [p for p in mp.polls if p.url.endswith("/data.json") and p.source == "watch"]
    assert p.count >= 6 and p.gap_ms is not None and 500 <= p.gap_ms <= 1000, p
    # The replay answers every poll with the first response: nothing changes.
    assert by_id(mp, "#v") is None, mp.regions


@pytest.mark.parametrize("fails", ["load", "hook"])
async def test_failure_is_recorded(settings, browser, server, tmp_path, fails):
    async def open_page():
        if fails == "load":
            raise RuntimeError("no page")
        ctx = await browser.new_context()
        page = await ctx.new_page()  # no hook installed
        await page.set_content("<p>x</p>")
        return ctx, page

    mp = await pass_t(open_page)
    assert not mp.ok and mp.error


async def test_elements(settings, browser, server, tmp_path):
    """V13: the element rules (Q6), read on their own."""
    from a11y_assist.motion import read_elements

    har = tmp_path / "page.har.zip"
    cap = await record(
        browser, settings, f"{server.base}/2x/t-elements.html", har, noop_log
    )
    r = await replay_context(
        browser, settings, har, noop_log, init_scripts=(MOTION_INIT_JS,)
    )
    try:
        page = await r.context.new_page()
        await r.guard.goto(page, cap.final_url)
        els, truncated, _ = await read_elements(page)
    finally:
        await r.context.close()
    assert not truncated
    names = [(e.kind, e.name) for e in els]
    assert names == [
        ("heading", "Elements"),
        ("text", "One paragraph."),
        ("control", "Same line"),  # its label shares the line: one element
        ("text", "Stacked label"),  # stacked above: its own element
        ("control", "Stacked label"),
        ("control", "Wrapping"),  # a wrapping label on one line
        ("image", "A described image"),  # alt-less images are skipped
        ("text", "Name"),  # each table cell is its own element
        ("text", "Score"),
        ("text", "Ann"),
        ("text", "5"),
        ("text", "Inside the frame."),  # the iframe's content, inline
        ("control", "Frame button"),
        ("text", "After the frame."),
    ], names
    assert [e.i for e in els] == list(range(len(els)))
    assert {e.frame for e in els if e.name in ("Frame button",)} == {1}
