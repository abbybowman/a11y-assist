"""3.A's flash capture (docs/rules/3a-flashing.md, section 2). Facts only:
frames, and what flash.py counts in them; the outcome is checks/t3a.py's.

Three ways to get every frame, because real-time screenshots alias a fast
strobe down to a slow one (research section 4):
  * the stepped capture: a fresh load at 1024 x 768 with Playwright's clock
    installed and paused before the page loads (pipeline opener
    `paused_clock`); 60 steps per second of page time, each running the
    clock, setting every animation's currentTime and SMIL's time, then one
    screenshot. Real-time media (video, animated images, marquee) are masked;
  * animated images: every frame decoded with ImageDecoder from the recorded
    bytes, at the size the page shows them, over two plays;
  * video: decoded from the recorded bytes in a tool page, played at half
    speed with requestVideoFrameCallback (every frame), the first 10 s,
    scaled to full screen (1024 x 768).
And one net: a 2 s CDP screencast of an ordinary load, which only says
whether to capture (a trigger), never that nothing flashes.

Decoding happens in a tool page (motion._secure_tool_page), never the tested
page.
"""

from __future__ import annotations

import asyncio
import base64
import io
import math
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw
from playwright.async_api import BrowserContext, Page
from pydantic import BaseModel, Field

from tobi508 import flash
from tobi508.redact import safe_error
from tobi508.traverse import PATH_JS

VIEWPORT = (1024, 768)  # WCAG 2.0 Note 1's screen (spec Terms)
FPS = 60
STEP_S = 3.0  # page time stepped (spec section 2)
LEAD_MS = 100  # page time run before the first step
LEAD_MAX_MS = 6000  # fast callbacks seen later than this start no later
SCREENCAST_S = 2.0
VIDEO_CAP_S = 10.0  # spec O4
VIDEO_RATE = 0.5
VIDEO_GRID = (256, 192)  # one pixel per 4 x 4 CSS px cell at full screen
IMAGE_LOOPS = 2
IMAGE_MIN_S = 2.0
IMAGE_MAX_FRAMES = 500
IMAGE_MAX_BYTES = 5_000_000
VIDEO_MAX_BYTES = 50_000_000
CLOCK_T0 = 1_700_000_000_000  # an arbitrary fixed epoch: the same every run
CHECK_EVERY = 30  # steps between time checks
STRIP_FRAMES = 8


async def pause_clock(context: BrowserContext) -> None:
    """Install Playwright's clock in every page of `context` and pause it,
    before the page loads (timers, requestAnimationFrame and Date then move
    only when the capture runs them)."""
    await context.clock.install(time=CLOCK_T0)
    await context.clock.pause_at(CLOCK_T0 + 1000)


class Source(BaseModel):
    """One flashing source's evidence (spec section 6)."""

    kind: str  # page (the stepped capture) | image | video
    css: str = ""  # the element (image or video), or "" for the page
    src: str = ""
    frame_url: str = ""
    box: list[int] = Field(default_factory=list)  # x, y, w, h at 1024 x 768
    analysis: flash.Analysis = Field(default_factory=flash.Analysis)
    analyzed_s: float = 0.0  # time analyzed
    length_s: float | None = None  # the media's length (None: endless)
    strip: str | None = None  # run-folder path of a strip of frames
    plot: str | None = None  # run-folder path of the plot of L over time


class Unmeasured(BaseModel):
    """A trigger the capture could not measure (spec A3)."""

    what: str  # plain words: "a video's file", "a marquee"
    why: str
    css: str = ""
    src: str = ""


# ── The screencast trigger ────────────────────────────────────────────────


async def screencast(page: Page, seconds: float = SCREENCAST_S) -> flash.Analysis:
    """Frames Chrome paints for `seconds` (CDP screencast; only frames that
    changed are sent), counted like any others, at a smaller size."""
    cdp = await page.context.new_cdp_session(page)
    got: list[tuple[float, str]] = []

    def on_frame(ev: dict) -> None:
        got.append((float(ev["metadata"]["timestamp"]), ev["data"]))
        asyncio.ensure_future(
            cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        )

    cdp.on("Page.screencastFrame", on_frame)
    vw = (page.viewport_size or {}).get("width") or VIEWPORT[0]
    await cdp.send(
        "Page.startScreencast",
        {"format": "png", "maxWidth": 640, "maxHeight": 480, "everyNthFrame": 1},
    )
    await asyncio.sleep(seconds)
    try:
        await cdp.send("Page.stopScreencast")
        await cdp.detach()
    except Exception:
        pass
    if len(got) < 2:
        return flash.Analysis(frames=len(got))
    t0 = got[0][0]
    arrays = [
        np.asarray(Image.open(io.BytesIO(base64.b64decode(d))).convert("RGB"))
        for _, d in got
    ]
    if len({a.shape for a in arrays}) > 1:
        return flash.Analysis(frames=len(got))
    px = vw / arrays[0].shape[1]
    return flash.analyze(arrays, [(t - t0) * 1000 for t, _ in got], px=px, fine=False)


# ── The stepped capture ───────────────────────────────────────────────────

# Every frame, each step: animations paused once and set to their own time,
# SMIL documents paused once and set to theirs (V7: SMIL steps; a marquee
# does not, it runs in real time and is masked).
# `t`: page time since the load, in ms. What runs at the first step started
# with the load (time 0); what starts later starts at the step that first
# sees it. Never the wall clock, so every run steps alike.
STEP_JS = """(t) => {
  const first = !window.__a11yStep;
  const S = window.__a11yStep || (window.__a11yStep = { anims: new Map(), svgs: new Map() });
  for (const a of document.getAnimations()) {
    let r = S.anims.get(a);
    if (!r) { r = { base: 0, at: first ? 0 : t }; S.anims.set(a, r); try { a.pause(); } catch (e) {} }
    try { a.currentTime = r.base + (t - r.at) * Math.abs(a.playbackRate || 1); } catch (e) {}
  }
  for (const s of document.querySelectorAll('svg')) {
    if (s.ownerSVGElement || !s.querySelector('animate, set, animateTransform, animateMotion, animateColor')) continue;
    let r = S.svgs.get(s);
    if (!r) { r = { base: 0, at: first ? 0 : t }; S.svgs.set(s, r); s.pauseAnimations(); }
    s.setCurrentTime(r.base + (t - r.at) / 1000);
  }
}"""

# Real-time media in this frame, as boxes in its viewport: they play by the
# wall clock, not the paused one, so they are masked from stepped frames
# (and decoded instead). `srcs`: animated images' sources.
MASK_JS = """(srcs) => {
  const out = [];
  const add = (e, what) => { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) out.push({ what, x: r.left, y: r.top, w: r.width, h: r.height }); };
  for (const v of document.querySelectorAll('video')) add(v, 'video');
  for (const m of document.querySelectorAll('marquee')) add(m, 'marquee');
  for (const i of document.images) if (srcs.includes((i.currentSrc || '').split('#')[0])) add(i, 'image');
  return out;
}"""


class Stepped(BaseModel):
    frames: int = 0
    page_ms: float = 0.0
    wall_s: float = 0.0
    lead_ms: int = LEAD_MS
    cut: bool = False  # stopped for the run's time limit
    masked: list[dict[str, Any]] = Field(default_factory=list)
    window: dict[str, Any] = Field(default_factory=dict)  # viewport, DPR


async def _frame_boxes(page: Page, js: str, arg: Any) -> list[dict]:
    """`js` in every frame, its boxes moved into the top page's viewport."""
    out = []
    for frame in page.frames:
        try:
            got = await frame.evaluate(js, arg)
        except Exception:
            continue
        dx = dy = 0.0
        if frame != page.main_frame:
            try:
                el = await frame.frame_element()
                bb = await el.bounding_box()
                if bb is None:
                    continue
                dx, dy = bb["x"], bb["y"]
            except Exception:
                continue
        for b in got or []:
            out.append({**b, "x": b["x"] + dx, "y": b["y"] + dy})
    return out


async def stepped(
    page: Page,
    image_srcs: list[str],
    lead_ms: int,
    out_of_time: Callable[[], bool],
) -> tuple[Stepped, list[bytes], np.ndarray | None]:
    """Step the page's clock for STEP_S at FPS, one screenshot per step, on a
    load from the pipeline's flash opener (clock paused, 1024 x 768).
    Returns what ran, the PNGs and the mask (True: real-time media)."""
    info = Stepped(lead_ms=lead_ms)
    shots: list[bytes] = []
    info.window = dict(
        zip(
            ("width", "height", "device_pixel_ratio"),
            await page.evaluate("() => [innerWidth, innerHeight, devicePixelRatio]"),
        )
    )
    await page.clock.run_for(lead_ms)
    boxes = await _frame_boxes(page, MASK_JS, image_srcs)
    mask = None
    if boxes:
        mask = np.zeros((VIEWPORT[1], VIEWPORT[0]), bool)
        for b in boxes:
            x0, y0 = max(0, math.floor(b["x"])), max(0, math.floor(b["y"]))
            x1 = min(VIEWPORT[0], math.ceil(b["x"] + b["w"]))
            y1 = min(VIEWPORT[1], math.ceil(b["y"] + b["h"]))
            if x0 < x1 and y0 < y1:
                mask[y0:y1, x0:x1] = True
                info.masked.append(
                    {"what": b["what"], "box": [x0, y0, x1 - x0, y1 - y0]}
                )
    start = time.monotonic()
    t = lead_ms
    for k, ms in enumerate([0, *flash.steps_ms(STEP_S, FPS)]):
        if k and k % CHECK_EVERY == 0 and out_of_time():
            info.cut = True
            break
        if ms:
            await page.clock.run_for(ms)
            t += ms
        for frame in page.frames:
            try:
                await frame.evaluate(STEP_JS, t)
            except Exception:
                continue
        shots.append(await page.screenshot(type="png"))
    info.frames = len(shots)
    info.page_ms = float(t - lead_ms)
    info.wall_s = round(time.monotonic() - start, 2)
    return info, shots, mask


def _times(n: int) -> list[float]:
    return [round(k * 1000 / FPS) for k in range(n)]


def changed_box(pngs: list[bytes], cell: int = flash.CELL) -> list[int] | None:
    """The box (x0, y0, x1, y1) of every pixel that differs from the first
    frame in any frame, grown to whole cells; None when nothing changed."""
    if len(pngs) < 2:
        return None
    first = Image.open(io.BytesIO(pngs[0])).convert("RGB")
    box = None
    for png in pngs[1:]:
        b = ImageChops.difference(
            first, Image.open(io.BytesIO(png)).convert("RGB")
        ).getbbox()
        if b:
            box = (
                b
                if box is None
                else [
                    min(box[0], b[0]),
                    min(box[1], b[1]),
                    max(box[2], b[2]),
                    max(box[3], b[3]),
                ]
            )
    if box is None:
        return None
    w, h = first.size
    x0, y0 = (box[0] // cell) * cell, (box[1] // cell) * cell
    x1 = min(w, -(-box[2] // cell) * cell)
    y1 = min(h, -(-box[3] // cell) * cell)
    return [x0, y0, x1, y1]


def _crops(pngs: list[bytes], box: list[int]) -> Iterator[np.ndarray]:
    for png in pngs:
        yield np.asarray(Image.open(io.BytesIO(png)).convert("RGB").crop(box))


def analyze_stepped(pngs: list[bytes], mask: np.ndarray | None) -> flash.Analysis:
    """Count the stepped frames, inside the box of what changed."""
    box = changed_box(pngs)
    if box is None:
        return flash.Analysis(
            frames=len(pngs), span_ms=_times(len(pngs))[-1] if pngs else 0
        )
    m = None if mask is None else mask[box[1] : box[3], box[0] : box[2]]
    return flash.analyze(
        _crops(pngs, box), _times(len(pngs)), mask=m, origin=(box[0], box[1])
    )


# ── Animated images ───────────────────────────────────────────────────────

# Each frame drawn at the size the page shows it, as RGB bytes, with how
# long Chrome shows it (10 ms or less: 100 ms).
IMAGE_FRAMES_JS = """async ([b64, type, w, h, max]) => {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const d = new ImageDecoder({ data: bytes, type });
  await d.tracks.ready;
  const t = d.tracks.selectedTrack;
  const c = new OffscreenCanvas(w, h), x = c.getContext('2d', { willReadFrequently: true });
  const out = [];
  for (let i = 0; i < t.frameCount && i < max; i++) {
    const r = await d.decode({ frameIndex: i });
    x.clearRect(0, 0, w, h);
    x.drawImage(r.image, 0, 0, w, h);
    const ms = (r.image.duration || 0) / 1000;
    r.image.close();
    const px = x.getImageData(0, 0, w, h).data;
    const rgb = new Uint8Array(w * h * 3);
    for (let p = 0, q = 0; p < px.length; p += 4, q += 3) {
      // Transparent pixels over white (the page behind is not known here).
      const a = px[p + 3] / 255;
      rgb[q] = px[p] * a + 255 * (1 - a); rgb[q + 1] = px[p + 1] * a + 255 * (1 - a); rgb[q + 2] = px[p + 2] * a + 255 * (1 - a);
    }
    let s = ''; for (let k = 0; k < rgb.length; k += 32768) s += String.fromCharCode.apply(null, rgb.subarray(k, k + 32768));
    out.push({ ms: ms <= 10 ? 100 : ms, rgb: btoa(s) });
  }
  return { frames: out, reps: t.repetitionCount === Infinity ? -1 : t.repetitionCount };
}"""

IMAGE_BOX_JS = (
    """(src) => {"""
    + PATH_JS
    + """
  let best = null;
  for (const i of document.images) {
    if ((i.currentSrc || '').split('#')[0] !== src) continue;
    const r = i.getBoundingClientRect();
    if (r.width > 0 && r.height > 0 && (!best || r.width * r.height > best.w * best.h))
      best = { x: r.left, y: r.top, w: r.width, h: r.height, css: path(i) };
  }
  return best ? [best] : [];
}"""
)


async def image_frames(
    tool: Page, body: bytes, kind: str, w: int, h: int
) -> tuple[list[np.ndarray], list[float], int]:
    got = await tool.evaluate(
        IMAGE_FRAMES_JS,
        [base64.b64encode(body).decode(), kind, w, h, IMAGE_MAX_FRAMES],
    )
    frames = [
        np.frombuffer(base64.b64decode(f["rgb"]), np.uint8).reshape(h, w, 3)
        for f in got["frames"]
    ]
    return frames, [float(f["ms"]) for f in got["frames"]], int(got["reps"])


def analyze_image(
    frames: list[np.ndarray], durations: list[float], reps: int, origin
) -> tuple[flash.Analysis, float, float | None]:
    """Two plays, and at least IMAGE_MIN_S (a one-second window needs more
    than a short loop), or as many as it plays when fewer, at 60 frames a
    second. Returns the analysis, the time analyzed and its length in all."""
    once = sum(durations)
    want = max(IMAGE_LOOPS, math.ceil(IMAGE_MIN_S * 1000 / max(once, 1)))
    plays = want if reps < 0 else min(want, reps + 1)
    idx, ticks = flash.resample(durations, plays, FPS)
    total = None if reps < 0 else once * (reps + 1) / 1000
    a = flash.analyze((frames[i] for i in idx), ticks, origin=origin)
    return a, round(once * plays / 1000, 2), total


# ── Video ─────────────────────────────────────────────────────────────────

# Played at half speed, muted, every presented frame drawn at full screen
# (contain, black bars) on a quarter-size canvas: one pixel per 4 x 4 CSS px.
VIDEO_JS = """async ([b64, type, rate, cap, gw, gh]) => {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const v = document.createElement('video');
  v.muted = true; v.playsInline = true; v.preload = 'auto';
  v.src = URL.createObjectURL(new Blob([bytes], { type }));
  document.body.append(v);
  const ok = await new Promise((r) => { v.oncanplay = () => r(true); v.onerror = () => r(false); setTimeout(() => r(false), 10000); });
  if (!ok) return { error: 'it could not be decoded' };
  const dur = isFinite(v.duration) ? v.duration : null;
  const c = new OffscreenCanvas(gw, gh), x = c.getContext('2d', { willReadFrequently: true });
  const s = Math.min(gw / v.videoWidth, gh / v.videoHeight);
  const dw = v.videoWidth * s, dh = v.videoHeight * s;
  window.__a11yV = [];
  const times = [];
  v.playbackRate = rate;
  await new Promise((done) => {
    const cb = (now, m) => {
      x.fillStyle = '#000'; x.fillRect(0, 0, gw, gh);
      x.drawImage(v, (gw - dw) / 2, (gh - dh) / 2, dw, dh);
      const px = x.getImageData(0, 0, gw, gh).data;
      const rgb = new Uint8Array(gw * gh * 3);
      for (let p = 0, q = 0; p < px.length; p += 4, q += 3) { rgb[q] = px[p]; rgb[q + 1] = px[p + 1]; rgb[q + 2] = px[p + 2]; }
      window.__a11yV.push(rgb); times.push(m.mediaTime);
      if (m.mediaTime >= cap || v.ended) { v.pause(); done(); } else v.requestVideoFrameCallback(cb);
    };
    v.requestVideoFrameCallback(cb);
    v.onended = () => done();
    v.play().catch(() => done());
  });
  return { times, duration: dur };
}"""

VIDEO_CHUNK_JS = """([a, b]) => window.__a11yV.slice(a, b).map((rgb) => {
  let s = ''; for (let k = 0; k < rgb.length; k += 32768) s += String.fromCharCode.apply(null, rgb.subarray(k, k + 32768));
  return btoa(s);
})"""


async def video_frames(
    tool: Page, body: bytes, kind: str
) -> tuple[list[np.ndarray], list[float], float | None, str]:
    """Every frame of the first VIDEO_CAP_S s, at full screen (quarter
    size), with their media times in ms; the video's length; an error."""
    gw, gh = VIDEO_GRID
    got = await asyncio.wait_for(
        tool.evaluate(
            VIDEO_JS,
            [base64.b64encode(body).decode(), kind, VIDEO_RATE, VIDEO_CAP_S, gw, gh],
        ),
        VIDEO_CAP_S / VIDEO_RATE + 20,
    )
    if got.get("error"):
        return [], [], None, got["error"]
    frames: list[np.ndarray] = []
    n = len(got["times"])
    for a in range(0, n, 20):
        for b64 in await tool.evaluate(VIDEO_CHUNK_JS, [a, a + 20]):
            frames.append(
                np.frombuffer(base64.b64decode(b64), np.uint8).reshape(gh, gw, 3)
            )
    return frames, [t * 1000 for t in got["times"]], got.get("duration"), ""


def analyze_video(frames: list[np.ndarray], times_ms: list[float]) -> flash.Analysis:
    gw, _ = VIDEO_GRID
    return flash.analyze(frames, times_ms, cell=1, px=VIEWPORT[0] / gw, fine=False)


def video_type(body: bytes, url: str) -> str:
    if body[:4] == b"\x1a\x45\xdf\xa3":
        return "video/webm"
    if body[4:8] == b"ftyp":
        return "video/mp4"
    if body[:4] == b"OggS":
        return "video/ogg"
    return "video/" + (url.rsplit(".", 1)[-1].split("?")[0] or "mp4")


# ── Evidence pictures ─────────────────────────────────────────────────────


def strip(
    frames: list[np.ndarray], box: list[int], path: Path, scale: float = 1.0
) -> None:
    """Up to STRIP_FRAMES frames side by side, cut around `box` (x, y, w, h
    in the frames' pixels), with a 2 px dark gap."""
    if not frames:
        return
    x, y, w, h = (int(round(v / scale)) for v in box)
    H, W = frames[0].shape[:2]
    pad = 20
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(W, x + w + pad), min(H, y + h + pad)
    step = max(1, len(frames) // STRIP_FRAMES)
    picks = frames[::step][:STRIP_FRAMES]
    cw, ch = x1 - x0, y1 - y0
    if cw <= 0 or ch <= 0:
        return
    out = Image.new("RGB", (len(picks) * (cw + 2), ch), (40, 40, 40))
    for i, f in enumerate(picks):
        out.paste(Image.fromarray(f[y0:y1, x0:x1]), (i * (cw + 2), 0))
    if out.width > 1600:
        out = out.resize((1600, max(1, out.height * 1600 // out.width)))
    out.save(path)


def plot(series: list[float], span_ms: float, path: Path) -> None:
    """Relative luminance of the busiest cell over time, 0 to 1."""
    if len(series) < 2:
        return
    w, h, m = 600, 160, 10
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([m, m, w - m, h - m], outline=(180, 180, 180))
    n = len(series)
    pts = [
        (m + (w - 2 * m) * i / (n - 1), h - m - (h - 2 * m) * max(0.0, min(1.0, v)))
        for i, v in enumerate(series)
    ]
    d.line(pts, fill=(0, 0, 160), width=2)
    d.text((m + 4, m + 2), f"luminance over {span_ms / 1000:.2f} s", fill=(0, 0, 0))
    img.save(path)


def decode(pngs: list[bytes], idx: list[int]) -> list[np.ndarray]:
    return [np.asarray(Image.open(io.BytesIO(pngs[i])).convert("RGB")) for i in idx]


__all__ = [
    "PATH_JS",
    "VIEWPORT",
    "Source",
    "Stepped",
    "Unmeasured",
    "analyze_image",
    "analyze_stepped",
    "analyze_video",
    "image_frames",
    "pause_clock",
    "safe_error",
    "screencast",
    "stepped",
    "video_frames",
]
