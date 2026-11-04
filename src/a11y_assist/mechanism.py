"""The mechanism probe (2.C spec section 2; shared with 2.A and 2.B): for
one piece of changing content, try the controls near it and at the top of the
page, and record whether the content stopped. Facts only (motion.Probe):
what an outcome is stays in the checks' rows.

Each try is a fresh load in pass T's browser (ctx.open_motion: full Chromium,
headless, autoplay allowed), reached with the walk's Tab presses
(traverse.replay and the walk's plan), so the page is the one pass T
watched. After the key, focus moves off with Tab and the content is watched
for its confirm time. A control that stopped it gets the focus-only probe:
the same replay with no key pressed, because some carousels pause while one
of their own controls has focus (Slick, Splide; plan item 12).

The key combination a page's text names (J2) is pressed by `press_named_key`,
once per run, when the answer comes in (plan Q10, an approved exception to
principle 5).
"""

from __future__ import annotations

import asyncio
import io
import json
import re
import time
from typing import Any

from PIL import Image, ImageChops
from playwright.async_api import Page

from a11y_assist.motion import Candidate, Element, MotionPass, Probe, Region
from a11y_assist.traverse import open_session, replay

# Bounds that keep a run within its limit; reaching one is recorded (K7).
MAX_CONTROLS = 8  # control candidates tried per content
MAX_INSTANCES = 3  # contents probed per page
WINDOW = 3  # TT: "three elements"
SETTLE_S = 0.6  # after focus leaves, before the first look (transitions end)
LOOK_S = 0.5
CONFIRM_MIN_S = 5.5
CONFIRM_MAX_S = 15.0
SLOWED = 1.5  # the period grew by at least half

FIELD_ROLES = {"textbox", "searchbox", "combobox", "spinbutton", "listbox"}
SPACE_ROLES = {"checkbox", "switch", "radio"}

# Plan Q10: modifiers plus one key, never one the browser itself uses.
MODIFIERS = {
    "ctrl": "Control",
    "control": "Control",
    "alt": "Alt",
    "option": "Alt",
    "shift": "Shift",
    "meta": "Meta",
    "cmd": "Meta",
    "command": "Meta",
}
BROWSER_KEYS = {
    "Control+W",
    "Control+T",
    "Control+N",
    "Control+L",
    "Control+Q",
    "Alt+F4",
    "Alt+Home",
    "Meta+W",
    "Meta+T",
    "Meta+N",
    "Meta+L",
    "Meta+Q",
}
_NAMED = re.compile(r"^(F([1-9]|1[0-2])|Escape|Esc|Space|Enter|Home|End)$", re.I)


def parse_key(text: str | None) -> str | None:
    """A Playwright key combination from page text such as "Ctrl+Shift+P",
    or None when it is not modifiers plus one key."""
    if not text:
        return None
    parts = [p.strip() for p in re.split(r"\s*\+\s*", text.strip()) if p.strip()]
    if len(parts) < 2:
        return None
    mods = []
    for p in parts[:-1]:
        m = MODIFIERS.get(p.lower())
        if m is None or m in mods:
            return None
        mods.append(m)
    key = parts[-1]
    if len(key) == 1 and key.isalnum():
        key = key.upper()
    elif _NAMED.match(key):
        key = {"esc": "Escape", "space": "Space"}.get(key.lower(), key.capitalize())
        key = key.upper() if key.lower().startswith("f") and key[1:].isdigit() else key
    else:
        return None
    order = ["Control", "Alt", "Shift", "Meta"]
    return "+".join(sorted(mods, key=order.index) + [key])


def browser_key(combo: str) -> bool:
    return combo in BROWSER_KEYS


# ── Candidates ────────────────────────────────────────────────────────────


def windows(
    mp: MotionPass, r: Region, which: tuple[str, ...]
) -> tuple[list[tuple[int, str]], bool]:
    """(element index, window), nearest the content first, then the top of
    the page; and whether the content could be placed among the elements."""
    n = len(mp.elements)
    inside = sorted(r.elements)
    out: list[tuple[int, str]] = []
    placed = bool(inside) or r.next_element is not None
    if placed:
        if inside:
            first, last = inside[0], inside[-1]
        else:  # empty content: between the element before it and the next
            first, last = r.next_element, r.next_element - 1
        if "inside" in which:
            out += [(i, "inside") for i in inside]
        if "before" in which:
            out += [
                (i, "before") for i in range(first - 1, max(-1, first - 1 - WINDOW), -1)
            ]
        if "after" in which:
            out += [(i, "after") for i in range(last + 1, min(n, last + 1 + WINDOW))]
    if "top" in which:
        out += [(i, "top") for i in range(min(n, WINDOW))]
    seen, uniq = set(), []
    for i, w in out:
        if i not in seen:
            seen.add(i)
            uniq.append((i, w))
    return uniq, placed


def kind_of(el: Element) -> str:
    return "control" if el.kind == "control" else "text"


def activation(el: Element) -> list[str] | str:
    """The keys that operate a control (spec section 2, step 1), or why it
    is not pressed: "field" (needs a value), "not_operable" (a link that
    goes somewhere: following it is not pausing)."""
    if el.role in FIELD_ROLES:
        return "field"
    if (
        el.role == "link"
        and el.href not in (None, "", "#")
        and not (el.href or "").startswith(("#", "javascript:"))
    ):
        return "not_operable"
    if el.role == "slider":
        return ["Home"]
    if el.role in SPACE_ROLES:
        return [" "]
    return ["Enter"]


def reach(walk: Any) -> dict[tuple[str, str], int]:
    """(frame URL or "", CSS path) -> P1 presses that reach it."""
    out: dict[tuple[str, str], int] = {}
    if walk is None:
        return out
    for st in walk.p1.steps:
        s = st.stop
        if s.kind != "element" or not s.css_path:
            continue
        key = ((s.frame_url or "") if s.frame_chain else "", s.css_path)
        out.setdefault(key, st.n)
    return out


# ── Watching the content ──────────────────────────────────────────────────


def _frame(page: Page, r: Region):
    if r.frame == 0:
        return page.main_frame
    return next((f for f in page.frames if f.url == r.frame_url), None)


async def _place(page: Page, r: Region) -> dict | None:
    """Scroll the content into view once and return a fixed clip around it
    (its box grown by half its size: a rotating square reaches past its own
    box), in the page's viewport. None when it cannot be found."""
    frame = _frame(page, r)
    if frame is None:
        return None
    loc = frame.locator(r.content_css).first
    try:
        await loc.evaluate("(e) => e.scrollIntoView({ block: 'center' })")
        box = await loc.bounding_box()
    except Exception:
        return None
    if not box or box["width"] <= 0 or box["height"] <= 0:
        return None
    vp = page.viewport_size or {"width": 1280, "height": 720}
    g = max(box["width"], box["height"]) / 2
    x0, y0 = max(0, box["x"] - g), max(0, box["y"] - g)
    x1 = min(vp["width"], box["x"] + box["width"] + g)
    y1 = min(vp["height"], box["y"] + box["height"] + g)
    if x1 <= x0 or y1 <= y0:
        return None
    return {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}


async def _look(page: Page, r: Region, clip: dict) -> Image.Image | None | str:
    """The content's area now; "gone" when the content is no longer rendered.
    A page screenshot of a fixed clip: an element screenshot waits for the
    element to stop moving, which a spinning badge never does."""
    frame = _frame(page, r)
    if frame is None:
        return None
    try:
        if not await frame.locator(r.content_css).first.is_visible():
            return "gone"
        png = await page.screenshot(clip=clip, timeout=3000)
    except Exception:
        return None
    return Image.open(io.BytesIO(png)).convert("RGB")


def _differs(a: Image.Image, b: Image.Image) -> bool:
    if a.size != b.size:
        return True
    return ImageChops.difference(a, b).getbbox() is not None


def confirm_s(r: Region) -> float:
    p = r.period_s or 0
    return min(CONFIRM_MAX_S, max(CONFIRM_MIN_S, SLOWED * p))


async def watch(page: Page, r: Region) -> str:
    """stopped | slowed | no_effect | unreliable, over the confirm time.

    Slowed is judged on the time between two changes, never on the first
    change alone: where a watch starts in the content's cycle is chance, so
    a 1 s ticker's first change can come 1.6 s in (a false "slowed" once).
    """
    await asyncio.sleep(SETTLE_S)
    clip = await _place(page, r)
    if clip is None:
        gone = await _look(page, r, {"x": 0, "y": 0, "width": 1, "height": 1})
        return "stopped" if gone == "gone" else "unreliable"
    prev = await _look(page, r, clip)
    if prev == "gone":
        return "stopped"  # hidden
    if prev is None:
        return "unreliable"
    p = r.period_s or 0
    start = time.monotonic()
    limit = confirm_s(r)
    changes: list[float] = []
    while time.monotonic() - start < limit:
        await asyncio.sleep(LOOK_S)
        img = await _look(page, r, clip)
        if img == "gone":
            return "stopped"
        if img is None:
            return "unreliable"
        if _differs(prev, img):
            changes.append(time.monotonic() - start)
            if not p:
                return "no_effect"
            if len(changes) >= 2:
                gap = changes[-1] - changes[-2]
                if gap < SLOWED * p:
                    return "no_effect"  # still changing at its own pace
        prev = img
    if not changes:
        return "stopped"
    gaps = [b - a for a, b in zip(changes, changes[1:])]
    quiet = (time.monotonic() - start) - changes[-1]
    # Every gap, and the quiet after the last change, at least half again
    # its period: it changes more slowly (a frequency control).
    if all(g >= SLOWED * p for g in gaps) and quiet >= SLOWED * p:
        return "slowed"
    return "no_effect"


async def _try(ctx: Any, el: Element, presses: int, keys: list[str], r: Region) -> str:
    """One fresh load: Tab to the control, press `keys`, Tab off, watch."""
    s = await replay(ctx.open_motion, ctx.quiet_ms, ["Tab"] * presses, ctx.plan)
    try:
        last = s.traversal.steps[-1].stop if s.traversal.steps else None
        if last is None or last.css_path != el.css:
            return "unreachable"
        url0 = s.page.url
        for k in keys:
            await s.traversal.press(k)
        if s.page.url.split("#")[0] != url0.split("#")[0]:
            return "unreliable"  # it navigated away
        await s.traversal.press("Tab")
        return await watch(s.page, r)
    except Exception:
        return "unreliable"
    finally:
        await s.close()


async def probe(
    ctx: Any,
    mp: MotionPass,
    walk: Any,
    r: Region,
    which: tuple[str, ...] = ("inside", "before", "after", "top"),
) -> Probe:
    """The mechanism probe for one content (2.C spec section 2). It stops
    early only on a control that stopped the content and whose focus-only
    probe saw no effect: a slowed result (2.C) does not end it, so 2.B,
    which needs a stop, sharing the same probe never loses candidates."""
    pr = Probe(probed=True)
    cands, placed = windows(mp, r, which)
    if not placed:
        pr.cannot_place = True
    stops = reach(walk)
    held = ("stopped", "slowed")  # these get the focus-only probe
    tried = 0
    done = False
    for i, w in cands:
        el = mp.elements[i]
        c = Candidate(element=i, window=w, kind=kind_of(el))
        pr.candidates.append(c)
        if c.kind != "control":
            continue  # text and images go to J2
        how = activation(el)
        if how == "field":
            c.result = "field"
            pr.cannot_try = pr.cannot_try or f'the field "{el.name}" (it needs a value)'
            continue
        if how == "not_operable":
            c.result = "not_operable"
            continue
        if done:
            continue  # stopped early: one held, not by focus alone
        if tried >= MAX_CONTROLS or ctx.out_of_time():
            pr.untried += 1
            continue
        presses = stops.get((el.frame_url if el.frame else "", el.css))
        if presses is None:
            c.result = "unreachable"  # the walk never focused it
            continue
        tried += 1
        times = "time" if presses == 1 else "times"
        c.keys = f"press Tab {presses} {times}, then {_name(how)}"
        c.result = await _try(ctx, el, presses, how, r)
        if c.result in held and not ctx.out_of_time():
            c.focus_only = await _try(ctx, el, presses, [], r)
            if c.result == "stopped" and c.focus_only == "no_effect":
                done = True  # it stopped, and not by focus alone
    return pr


def _name(keys: list[str]) -> str:
    return " then ".join({" ": "Space"}.get(k, k) for k in keys)


async def press_named_key(ctx: Any, r: Region, combo: str) -> str:
    """Q10: the combination J2 found in the page's text, pressed once on a
    fresh load (no live network), then the same watch."""
    s = await open_session(ctx.open_motion, ctx.quiet_ms)
    try:
        await s.traversal.press(combo)
        return await watch(s.page, r)
    except Exception:
        return "unreliable"
    finally:
        await s.close()


async def probe_shared(ctx: Any, mp: MotionPass, walk: Any, r: Region) -> Probe:
    """One probe per content per call, shared by 2.A-2.C (a carousel that is
    both moving and auto-updating is probed once). A copy: each check may
    add its own key press results."""
    cache = ctx.cache.setdefault("probes", {})
    if r.key not in cache:
        cache[r.key] = await probe(ctx, mp, walk, r)
    return cache[r.key].model_copy(deep=True)


# Q10: one key combination per run, whichever test's J2 found it. The record
# is evidence (evidence/keys.json): combination -> region key -> result.
KEYS_FILE = "evidence/keys.json"


def _keys(ctx: Any) -> dict[str, dict[str, str]]:
    path = ctx.rel / KEYS_FILE
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


async def press_answered(
    ctx: Any,
    mp: MotionPass,
    j2: dict[str, dict[str, Any]],
    probes: dict[str, Probe],
    regions: dict[str, Region],
) -> None:
    """K4: a key combination a J2 answer gives (instance id "r1-e3" ->
    answer), pressed on a fresh load and watched. Not pressed (K5): one that
    is not modifiers plus one key, one the browser uses, or a second,
    different combination in the same run."""
    for qid, a in sorted(j2.items()):
        if a.get("choice") != "describes":
            continue
        iid, e = qid.split("-e")
        pr, r = probes.get(iid), regions.get(iid)
        if pr is None or r is None:
            continue
        c = next((c for c in pr.candidates if c.element == int(e)), None)
        if c is None or c.key:
            continue  # already pressed for this content
        text = mp.elements[c.element].name
        combo = parse_key(a.get("key"))
        if combo is None:
            pr.cannot_try = pr.cannot_try or f'what "{text[:80]}" describes'
            continue
        if browser_key(combo):
            pr.cannot_try = pr.cannot_try or f"{combo}, which the browser itself uses"
            continue
        rec = _keys(ctx)
        if (rec and combo not in rec) or ctx.open_motion is None:
            pr.cannot_try = pr.cannot_try or f"{combo} (one combination per run)"
            continue
        got = rec.get(combo, {}).get(r.key)
        if got is None:
            got = await press_named_key(ctx, r, combo)
            rec.setdefault(combo, {})[r.key] = got
            path = ctx.rel / KEYS_FILE
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(rec, indent=1), "utf-8")
        c.key, c.result = combo, got


__all__ = [
    "parse_key",
    "browser_key",
    "probe",
    "probe_shared",
    "press_answered",
    "press_named_key",
    "windows",
]
