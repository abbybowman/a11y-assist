"""Test 3.A (2.3.1-flashing), from docs/rules/3a-flashing.md (spec 0.2.0,
a draft: registered in tests/drafts.py only).

Triggers come from pass T (motion.py: fast animations and callbacks,
animated images' frame delays, videos) and a 2 s screencast. Only when one
fires does the flash capture run (flashcap.py), and flash.py counts the
frames. Only evaluate() and the row tables decide the outcome: NOT TESTED
when flashing is found (the TT text names it, p. 18), DOES NOT APPLY when
nothing flashes and everything was measured, otherwise NEEDS REVIEW. The
WCAG 2.0 assessment is a note in the summary, never an outcome.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from tobi508 import capture, flash, flashcap, motion
from tobi508.checks.base import RunContext
from tobi508.engine import Row
from tobi508.models import DecidedBy, Finding, Instance, OpenQuestion, Outcome, TestId
from tobi508.redact import safe_error
from tobi508.walk import KeyboardWalk

FAST_MS = 334  # faster than every 334 ms: more than 3 changes a second
STREAMING = re.compile(
    r"^https?://(www\.)?(youtube(-nocookie)?\.com/embed|player\.vimeo\.com)/",
    re.IGNORECASE,
)


class Trigger(BaseModel):
    kind: str  # animation | timer | raf | image | video | screencast
    detail: str = ""
    css: str = ""
    src: str = ""
    frame_url: str = ""


class Place(BaseModel):
    """What is at a flashing box's centre at 1024 x 768 (for "where")."""

    css: str = ""
    tag: str = ""
    text: str = ""


class State3A(BaseModel):
    motion_ok: bool = True
    error: str = ""  # pass T could not run (A1)
    triggers: list[Trigger] = Field(default_factory=list)
    screencast: flash.Analysis | None = None
    stepped: flashcap.Stepped | None = None
    sources: list[flashcap.Source] = Field(default_factory=list)
    places: dict[str, Place] = Field(default_factory=dict)  # by source index
    unmeasured: list[flashcap.Unmeasured] = Field(default_factory=list)
    window: list[int] = Field(default_factory=lambda: list(flashcap.VIEWPORT))


# ── Triggers (spec section 2) ─────────────────────────────────────────────


def _fast_runs(times: list[float]) -> int:
    """The most of `times` (s) in any one second."""
    ts = sorted(times)
    best, j = 0, 0
    for i, t in enumerate(ts):
        while ts[j] < t - 1.0 + 1e-9:
            j += 1
        best = max(best, i - j + 1)
    return best


def played(reads: list[motion.Media]) -> bool:
    return any(not m.paused for m in reads) and max(m.time for m in reads) > min(
        m.time for m in reads
    )


def triggers(mp: motion.MotionPass) -> tuple[list[Trigger], list[flashcap.Unmeasured]]:
    """What may flash, from pass T (spec section 2), and what cannot be
    measured at all (A3)."""
    out: list[Trigger] = []
    gone: list[flashcap.Unmeasured] = []
    for a in mp.fast_animations:
        out.append(
            Trigger(
                kind="animation",
                css=a.get("css", ""),
                detail=f"{a.get('name') or 'an animation'}, {a.get('per_s')} changes a second",
            )
        )
    groups: dict[tuple[int, str], list[float]] = {}
    for f in mp.fast_callbacks:
        kind = "raf" if f["kind"] == "raf" else "timer"
        groups.setdefault((f["frame"], kind), []).append(f["t"])
    for (frame, kind), ts in sorted(groups.items()):
        n = _fast_runs(ts)
        if n > flash.MAX_TRANSITIONS:
            out.append(
                Trigger(kind=kind, detail=f"{n} changes in one second (frame {frame})")
            )
    for img in mp.animated_images:
        ms = img.get("min_ms")
        if ms is not None and ms < FAST_MS:
            out.append(
                Trigger(kind="image", src=img["src"], detail=f"frames of {ms} ms")
            )
    reads: dict[tuple[int, str], list[motion.Media]] = {}
    for m in mp.media:
        if m.tag == "video":
            reads.setdefault((m.frame, m.css), []).append(m)
    for (_, css), rs in reads.items():
        if played(rs):
            last = rs[-1]
            out.append(
                Trigger(kind="video", css=css, src=last.src, frame_url=last.frame_url)
            )
    for src in mp.iframes:
        if STREAMING.match(src):
            gone.append(
                flashcap.Unmeasured(
                    what="a video player from another site",
                    why="it streams its video, which we cannot play from our recording",
                    src=src[:200],
                )
            )
    for r in mp.regions:
        if r.source == "marquee" or r.tag == "marquee":
            gone.append(
                flashcap.Unmeasured(
                    what="scrolling text (a marquee)",
                    why="it moves by the clock on the wall, which our frame-by-frame capture cannot step",
                    css=r.css,
                )
            )
    return out, gone


# ── Collection ────────────────────────────────────────────────────────────


PLACE_JS = (
    "(pts) => {"
    + flashcap.PATH_JS
    + """
  return pts.map(([x, y]) => {
    const e = document.elementFromPoint(x, y);
    if (!e) return null;
    return { css: path(e), tag: e.tagName.toLowerCase(), text: (e.innerText || e.getAttribute('alt') || '').replace(/\\s+/g, ' ').trim().slice(0, 60) };
  });
}"""
)


def _evidence(ctx: RunContext, name: str) -> Path:
    ctx.shots.mkdir(parents=True, exist_ok=True)
    return ctx.shots / name


def _rel(ctx: RunContext, p: Path) -> str | None:
    return str(p.relative_to(ctx.rel)) if p.exists() else None


def _pictures(ctx, src: flashcap.Source, n: int, frames, scale: float = 1.0) -> None:
    a = src.analysis
    if not a.flashing or not a.boxes:
        return
    try:
        box = a.boxes[0]
        if src.kind == "image" and src.box:
            box = [box[0] - src.box[0], box[1] - src.box[1], box[2], box[3]]
        p = _evidence(ctx, f"3a-{n}-strip.png")
        flashcap.strip(frames, box, p, scale)
        src.strip = _rel(ctx, p)
        q = _evidence(ctx, f"3a-{n}-plot.png")
        flashcap.plot(a.series, a.span_ms, q)
        src.plot = _rel(ctx, q)
    except Exception:
        pass  # pictures are evidence for a person; the counts stand


async def collect(ctx: RunContext, walk: KeyboardWalk | None) -> State3A:
    mp = await motion.collect(ctx, keep_shots=False)
    st = State3A()
    if not mp.ok:
        st.motion_ok, st.error = False, mp.error or "the page could not be watched"
        return st
    st.triggers, st.unmeasured = triggers(mp)
    # The net (spec section 2): a short screencast of an ordinary load.
    if ctx.open_motion is not None and not ctx.out_of_time():
        try:
            c, page = await ctx.open_motion()
            try:
                st.screencast = await flashcap.screencast(page)
            finally:
                await c.close()
        except Exception:
            st.screencast = None
        if st.screencast is not None and st.screencast.flashing:
            st.triggers.append(
                Trigger(
                    kind="screencast",
                    detail=f"{st.screencast.flashes_per_s:g} flashes a second seen while watching",
                )
            )
    if not st.triggers:
        return st  # A4 at no further cost
    if ctx.open_flash is None:
        st.unmeasured.append(
            flashcap.Unmeasured(
                what="the flashing we suspected",
                why="the capture is not available in this run",
            )
        )
        return st
    har = ctx.rel / "evidence" / "page.har.zip"
    kinds = {t.kind for t in st.triggers}
    images = [t.src for t in st.triggers if t.kind == "image"]
    page_clock = bool(kinds & {"animation", "timer", "raf", "screencast"})
    if ctx.out_of_time():
        st.unmeasured.append(
            flashcap.Unmeasured(
                what="the flashing we suspected", why="the run reached its time limit"
            )
        )
        return st
    try:
        context, page = await ctx.open_flash()
    except Exception as exc:
        st.unmeasured.append(
            flashcap.Unmeasured(
                what="the page's own animation",
                why=f"the page could not be loaded for the capture: {safe_error(exc)}",
            )
        )
        return st
    try:
        await _measure(ctx, st, mp, page, har, page_clock, images)
    finally:
        await context.close()
    return st


async def _measure(
    ctx, st: State3A, mp, page, har: Path, page_clock: bool, images: list[str]
) -> None:
    fast = [f["t"] for f in mp.fast_callbacks]
    lead = flashcap.LEAD_MS
    if fast and not any(t.kind in ("animation", "screencast") for t in st.triggers):
        lead = int(
            min(flashcap.LEAD_MAX_MS, max(flashcap.LEAD_MS, min(fast) * 1000 - 200))
        )
    if page_clock:
        try:
            info, pngs, mask = await flashcap.stepped(
                page, images, lead, ctx.out_of_time
            )
            st.stepped = info
            st.window = [info.window.get("width", 0), info.window.get("height", 0)]
            a = flashcap.analyze_stepped(pngs, mask)
            src = flashcap.Source(
                kind="page", analysis=a, analyzed_s=round(info.page_ms / 1000, 2)
            )
            src.box = a.boxes[0] if a.boxes else []
            st.sources.append(src)
            for m in info.masked:
                if m["what"] == "marquee" and not any(
                    "marquee" in u.what for u in st.unmeasured
                ):
                    st.unmeasured.append(
                        flashcap.Unmeasured(
                            what="scrolling text (a marquee)",
                            why="it moves by the clock on the wall, which our frame-by-frame capture cannot step",
                        )
                    )
            if info.cut:
                st.unmeasured.append(
                    flashcap.Unmeasured(
                        what="part of the page's own animation",
                        why="the run reached its time limit during the capture",
                    )
                )
            if a.flashing:
                pts = [[b[0] + b[2] / 2, b[1] + b[3] / 2] for b in a.boxes[:5]]
                try:
                    got = await page.evaluate(PLACE_JS, pts)
                    for k, g in enumerate(got):
                        if g:
                            st.places[f"0.{k}"] = Place(**g)
                except Exception:
                    pass
                t0 = int((a.general.at_ms or a.red.at_ms or 0) * flashcap.FPS / 1000)
                idx = list(range(t0, min(len(pngs), t0 + flashcap.FPS), 2))
                _pictures(ctx, src, 1, flashcap.decode(pngs, idx))
        except Exception as exc:
            st.unmeasured.append(
                flashcap.Unmeasured(
                    what="the page's own animation",
                    why=f"the capture failed: {safe_error(exc)}",
                )
            )
    tool_ctx = tool = None
    try:
        for src_url in images:
            if ctx.out_of_time():
                st.unmeasured.append(
                    flashcap.Unmeasured(
                        what="an animated image",
                        why="the run reached its time limit",
                        src=src_url[:200],
                    )
                )
                continue
            body = capture.media_body(har, src_url) if har.exists() else None
            kind = motion._image_type(body) if body else None
            if not body or not kind or len(body) > flashcap.IMAGE_MAX_BYTES:
                st.unmeasured.append(
                    flashcap.Unmeasured(
                        what="an animated image",
                        why="its file was not recorded or is too large to decode",
                        src=src_url[:200],
                    )
                )
                continue
            boxes = await flashcap._frame_boxes(page, flashcap.IMAGE_BOX_JS, src_url)
            if not boxes:
                continue  # not shown at this window size: nothing to see
            b = max(boxes, key=lambda x: x["w"] * x["h"])
            w = max(1, min(flashcap.VIEWPORT[0], round(b["w"])))
            h = max(1, min(flashcap.VIEWPORT[1], round(b["h"])))
            if tool is None:
                tool_ctx, tool = await motion._secure_tool_page(page)
            try:
                frames, durations, reps = await flashcap.image_frames(
                    tool, body, kind, w, h
                )
                a, span, total = flashcap.analyze_image(
                    frames, durations, reps, (b["x"], b["y"])
                )
            except Exception as exc:
                st.unmeasured.append(
                    flashcap.Unmeasured(
                        what="an animated image",
                        why=f"it could not be decoded: {safe_error(exc)}",
                        src=src_url[:200],
                    )
                )
                continue
            src = flashcap.Source(
                kind="image",
                css=b.get("css", ""),
                src=src_url[:500],
                box=[round(b["x"]), round(b["y"]), w, h],
                analysis=a,
                analyzed_s=span,
                length_s=total,
            )
            st.sources.append(src)
            if a.flashing:
                idx, _ = flash.resample(durations, 1, flashcap.FPS)
                _pictures(
                    ctx,
                    src,
                    len(st.sources),
                    [frames[i] for i in idx[: flashcap.FPS : 2]],
                )
        for t in [t for t in st.triggers if t.kind == "video"]:
            await _video(ctx, st, mp, page, har, t, tool)
            if tool is None and st.sources and st.sources[-1].kind == "video":
                pass
    finally:
        if tool_ctx is not None:
            await tool_ctx.close()


async def _video(ctx, st: State3A, mp, page, har: Path, t: Trigger, tool) -> None:
    gone = flashcap.Unmeasured(what="a video", why="", css=t.css, src=t.src[:200])
    if ctx.out_of_time():
        gone.why = "the run reached its time limit"
        st.unmeasured.append(gone)
        return
    if t.src.startswith("blob:") or not t.src.startswith(("http:", "https:")):
        gone.why = "it streams its video, which we cannot play from our recording"
        st.unmeasured.append(gone)
        return
    body = capture.media_body(har, t.src) if har.exists() else None
    over = {m["url"] for m in mp.media_store if m.get("over_cap")}
    if body is None:
        gone.why = (
            "its file is larger than we record"
            if t.src.split("#")[0] in over
            else "its file was not recorded"
        )
        st.unmeasured.append(gone)
        return
    if len(body) > flashcap.VIDEO_MAX_BYTES:
        gone.why = "its file is too large to decode"
        st.unmeasured.append(gone)
        return
    own_ctx = None
    if tool is None:
        own_ctx, tool = await motion._secure_tool_page(page)
    try:
        frames, times, length, err = await flashcap.video_frames(
            tool, body, flashcap.video_type(body, t.src)
        )
    except Exception as exc:
        frames, times, length, err = (
            [],
            [],
            None,
            f"it could not be decoded ({safe_error(exc)})",
        )
    finally:
        if own_ctx is not None:
            await own_ctx.close()
    if err or len(frames) < 2:
        gone.why = err or "it showed too few frames to analyze"
        st.unmeasured.append(gone)
        return
    box = []
    try:
        got = await page.evaluate(
            "(css) => { const e = document.querySelector(css); if (!e) return null; const r = e.getBoundingClientRect(); return [r.left + scrollX, r.top + scrollY, r.width, r.height]; }",
            t.css,
        )
        box = [round(v) for v in got] if got else []
    except Exception:
        pass
    a = flashcap.analyze_video(frames, times)
    src = flashcap.Source(
        kind="video",
        css=t.css,
        src=t.src[:500],
        frame_url=t.frame_url,
        box=box,
        analysis=a,
        analyzed_s=round((times[-1] - times[0]) / 1000, 2),
        length_s=length,
    )
    st.sources.append(src)
    if a.flashing:
        t0 = int(
            np.searchsorted(
                np.array(times), times[0] + (a.general.at_ms or a.red.at_ms or 0)
            )
        )
        _pictures(
            ctx,
            src,
            len(st.sources),
            frames[t0 : t0 + 30 : 2],
            scale=flashcap.VIEWPORT[0] / flashcap.VIDEO_GRID[0],
        )


# ── Rows (spec section 1) ─────────────────────────────────────────────────


def partial(s: flashcap.Source) -> bool:
    """A video analyzed in part (spec O4)."""
    return s.kind == "video" and (s.length_s is None or s.length_s > s.analyzed_s + 0.1)


@dataclass
class Page:
    st: State3A
    flashing: list[flashcap.Source] = field(default_factory=list)

    @property
    def unmeasured(self) -> list[str]:
        out = [f"{u.what}: {u.why}" for u in self.st.unmeasured]
        out += [
            f"a video after its first {round(s.analyzed_s):g} seconds"
            for s in self.st.sources
            if partial(s)
        ]
        if unexplained(self.st) and not out:  # else what was not measured explains it
            out.append(
                "something that flashed while we watched, which our frame-by-frame capture did not show"
            )
        return out


def unexplained(st: State3A) -> bool:
    """The screencast saw flashing the exact measurements do not account for:
    more transitions in a second than any measured source shows, by more
    than one (its real-time frames jitter by about one: a steady 3 a second
    can read 7). Something flashed that we could not step or decode."""
    sc = st.screencast
    if sc is None or not sc.flashing:
        return False
    seen = max(
        (max(s.analysis.general.peak, s.analysis.red.peak) for s in st.sources),
        default=0,
    )
    return max(sc.general.peak, sc.red.peak) > seen + 1


APPLICABILITY = [
    Row("A1", lambda p: not p.st.motion_ok, Outcome.NEEDS_REVIEW, "p. 5"),
    Row("A2", lambda p: bool(p.flashing), Outcome.NOT_TESTED, "p. 18; research O1, O2"),
    Row(
        "A3",
        lambda p: bool(p.unmeasured),
        Outcome.NEEDS_REVIEW,
        "p. 5; research section 4",
    ),
    Row("A4", lambda p: True, Outcome.DNA, "p. 18 test condition"),
]


# ── The assessment (spec section 3) ───────────────────────────────────────


def _fits(a: list[int], b: list[int]) -> bool:
    x0, y0 = min(a[0], b[0]), min(a[1], b[1])
    x1, y1 = max(a[0] + a[2], b[0] + b[2]), max(a[1] + a[3], b[1] + b[3])
    return x1 - x0 <= flash.RECT[0] and y1 - y0 <= flash.RECT[1]


def _area(s: flashcap.Source) -> int:
    return max(s.analysis.general.area, s.analysis.red.area)


def together(sources: list[flashcap.Source]) -> set[int]:
    """F4: sources on the page (not videos, analyzed full screen) each under
    the area, whose flashing places fit in one 341 x 256 rectangle and whose
    areas add up over it. Their times cannot be aligned frame by frame."""
    out: set[int] = set()
    placed = [
        (i, s) for i, s in enumerate(sources) if s.kind != "video" and s.analysis.boxes
    ]
    for n, (i, a) in enumerate(placed):
        for j, b in placed[n + 1 :]:
            if _area(a) + _area(b) <= flash.AREA_LIMIT:
                continue
            if any(_fits(x, y) for x in a.analysis.boxes for y in b.analysis.boxes):
                out |= {i, j}
    return out


def assess(s: flashcap.Source, i: int, joint: set[int]) -> str:
    """The row for one flashing source: F2 or F3 (fails), F1 or F4 (could
    not assess), F5 (does not fail). A failing part decides first: a fine
    pattern elsewhere in the same source does not undo it."""
    a = s.analysis
    if a.general.flashing and a.general.over:
        return "F2"
    if a.red.flashing and a.red.over:
        return "F3"
    if a.fine:
        return "F1"
    if i in joint:
        return "F4"
    return "F5"


VERDICT = {"F1": "cannot", "F2": "fails", "F3": "fails", "F4": "cannot", "F5": "passes"}


def assess22(s: flashcap.Source, row: str) -> str | None:
    """WCAG 2.2's red rule, when it would change the result (spec O3)."""
    a = s.analysis
    if row in ("F1", "F4", "F2"):
        return None
    fails22 = a.red22.flashing and a.red22.over
    if row == "F3" and not fails22:
        return "would not fail"
    if row == "F5" and fails22:
        return "would fail"
    return None


# ── Sentences (spec section 3) ────────────────────────────────────────────


def _position(box: list[int]) -> str:
    if len(box) < 4:
        return "on the page"
    cx, cy = box[0] + box[2] / 2, box[1] + box[3] / 2
    w, h = flashcap.VIEWPORT
    if cy > h:
        return "below the first screen"
    v = "top" if cy < h / 3 else ("middle" if cy < 2 * h / 3 else "bottom")
    hz = "left" if cx < w / 3 else ("centre" if cx < 2 * w / 3 else "right")
    return (
        "in the middle of the screen"
        if (v, hz) == ("middle", "centre")
        else f"at the {v} {hz} of the screen"
    )


def where(st: State3A, i: int, s: flashcap.Source) -> str:
    box = s.analysis.boxes[0] if s.analysis.boxes else s.box
    if s.kind == "video":
        return "a video (analyzed at full screen)"
    if s.kind == "image":
        return f"an animated image {_position(s.box)}"
    size = f"{box[2]} by {box[3]} pixels" if len(box) == 4 else ""
    place = st.places.get(f"{i}.0") if i == 0 else None
    text = f' ("{place.text}")' if place and place.text else ""
    return f"an area of {size}{text} {_position(box)}".replace("  ", " ")


def facts(s: flashcap.Source) -> str:
    a = s.analysis
    red = a.red.flashing and (a.red.over or not a.general.flashing)
    k = a.red if red else a.general
    kind = "red flashing" if red else "light and dark flashing"
    rate = f"{k.peak / 2:g} flashes per second"
    if a.fine and not k.flashing:
        return f"a fine pattern that flickers, {a.fine_pixels} sampled pixels"
    area = (
        f"{k.area:,} square pixels flashing at once (the limit is "
        f"{flash.AREA_LIMIT:,} in any {flash.RECT[0]} by {flash.RECT[1]} pixel area)"
    )
    return f"{rate}, {area}, {kind}"


def _span(s: flashcap.Source) -> str:
    if s.kind != "video":
        return ""
    total = "its whole length" if s.length_s is None else f"{s.length_s:g} s"
    return (
        f" We analyzed the first {round(s.analyzed_s):g} s of {total}."
        if partial(s)
        else ""
    )


HEAD = "The Trusted Tester process records flashing content as Not Tested."


def assessment_sentence(st: State3A, rows: dict[int, str]) -> str:
    srcs = st.sources
    verdicts = {VERDICT[r] for r in rows.values()}
    page = (
        "fails"
        if "fails" in verdicts
        else ("cannot" if "cannot" in verdicts else "passes")
    )
    parts = []
    for i, r in rows.items():
        s = srcs[i]
        w, f = where(st, i, s), facts(s)
        note22 = assess22(s, r)
        n22 = (
            f" Under WCAG 2.2's definition of a red flash it {note22}."
            if note22
            else ""
        )
        if VERDICT[r] == "fails":
            parts.append(f"{w}: {f}.{n22}")
        elif VERDICT[r] == "passes":
            parts.append(f"{w}: {f}.{_span(s)}{n22}")
        elif r == "F1":
            parts.append(
                f"{w}: this may be a fine pattern, which WCAG allows; a person should check."
            )
        else:
            parts.append(
                f"{w}: flashing in several places at once may add up; a person should check."
            )
    body = " ".join(p[0].upper() + p[1:] for p in parts)
    if page == "fails":
        return (
            f"{HEAD} According to our experimental flash analysis, this flashing fails WCAG 2.3.1. {body} "
            "Flashing like this can cause seizures; fix it so it flashes no more than three times a second, or keep the flashing area small."
        )
    if page == "passes":
        return f"{HEAD} According to our experimental flash analysis, this flashing does not fail WCAG 2.3.1. {body}"
    return (
        f"{HEAD} Our experimental flash analysis could not decide whether it fails WCAG 2.3.1. {body} "
        "A person should check it with a flash analysis tool."
    )


ONE_D = (
    "Because flashing was found, the page cannot meet the non-interference test (1.D)."
)


def _finding(
    outcome: Outcome, summary: str, rows: list[str], refs, inst=None, why=""
) -> Finding:
    f = Finding(
        test_id=TestId.T3A,
        test_name=TestId.T3A.tt_name,
        outcome=outcome,
        summary=summary,
        rationale=why or f"Spec {rows[0]}.",
        decided_by=DecidedBy.RULE,
        rows=rows,
        instances=inst or [],
        evidence_refs=refs,
    )
    return f


def evaluate(st: State3A, evidence_refs: list[str]) -> Finding:
    p = Page(st, [s for s in st.sources if s.analysis.flashing])
    row = next(r for r in APPLICABILITY if r.when(p))
    measured = f"Measured at {st.window[0]} by {st.window[1]} pixels, WCAG 2.0's reference screen."
    refs = list(evidence_refs) + [x for s in st.sources for x in (s.strip, s.plot) if x]
    if row.id == "A1":
        f = Finding.not_performed(TestId.T3A, st.error)
        f.rows, f.decided_by, f.evidence_refs = ["A1"], DecidedBy.RULE, refs
        return f
    inst = [
        Instance(
            selector=s.css or None,
            description=(
                f"s{i + 1} {s.kind} [{'flashing' if s.analysis.flashing else 'not flashing'}]"
                f" general peak {s.analysis.general.peak}/s-window area {s.analysis.general.area}"
                f", red peak {s.analysis.red.peak} area {s.analysis.red.area}"
                f", WCAG 2.2 red peak {s.analysis.red22.peak} area {s.analysis.red22.area}"
                f", fine {s.analysis.fine}, analyzed {s.analyzed_s:g} s"
                + (f" of {s.length_s:g} s" if s.length_s else "")
                + (f", {s.src[:120]}" if s.src else "")
            ),
        )
        for i, s in enumerate(st.sources)
    ]
    trig = "; ".join(f"{t.kind}: {t.detail}" for t in st.triggers) or "none"
    if row.id == "A2":
        joint = together(st.sources)
        rows = {
            i: assess(s, i, joint)
            for i, s in enumerate(st.sources)
            if s.analysis.flashing
        }
        trace = ["A2", *[f"s{i + 1}:{r}" for i, r in rows.items()]]
        summary = f"{assessment_sentence(st, rows)} {ONE_D}"
        return _finding(
            Outcome.NOT_TESTED,
            summary,
            trace,
            refs,
            inst,
            f"Spec A2. Triggers: {trig}. {measured}",
        )
    if row.id == "A3":
        what = "; ".join(p.unmeasured)
        f = Finding.not_performed(
            TestId.T3A,
            f"We could not check all of this page for flashing ({what}). A person should watch it.",
        )
        f.rows, f.decided_by, f.evidence_refs, f.instances = (
            ["A3"],
            DecidedBy.RULE,
            refs,
            inst,
        )
        f.rationale = f"Spec A3. Triggers: {trig}. {measured}"
        return f
    looked = "Nothing on this page flashes more than three times a second, so this test does not apply."
    return _finding(
        Outcome.DNA,
        looked,
        ["A4"],
        refs,
        inst,
        f"Spec A4. Triggers: {trig}. {measured if st.sources else 'No trigger fired, so no capture ran.'}",
    )


class Check3A:
    """3.A as a check (checks/base.py); a draft until its spec is 1.0.0."""

    test_id = TestId.T3A
    state_type = State3A
    uses_walk = False
    uses_motion = True
    about = (
        "It watches the page for things that change quickly, and if any do, "
        "it records them frame by frame at 1024 by 768 pixels (stepping the "
        "page's own clock, and decoding animated images and the first 10 "
        "seconds of each video) and counts flashes. If anything flashes more "
        "than three times a second, the Trusted Tester process records this "
        "test as Not Tested; the tool also gives its own experimental "
        "reading of WCAG 2.3.1, as a note."
    )

    def walk_extras(self) -> list:
        return []

    async def collect(self, ctx: RunContext, walk: KeyboardWalk | None) -> State3A:
        return await collect(ctx, walk)

    def evaluate(self, state: State3A, evidence_refs: list[str]) -> Finding:
        return evaluate(state, evidence_refs)

    def questions(self, state: State3A, evidence_refs: list[str]) -> list[OpenQuestion]:
        return []  # spec section 4: every step is a measurement

    async def resume(self, ctx: RunContext, state: State3A, report: Any) -> list[str]:
        return []


__all__ = ["Check3A", "State3A", "evaluate", "triggers"]
