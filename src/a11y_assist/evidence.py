"""Keyboard evidence: Tab and Shift+Tab walks that record every focus stop.

Records what happened only. Nothing here decides an outcome.

Focus is followed into same- and cross-origin iframes (via Playwright frames)
and open shadow roots. Role and accessible name come from Playwright's ARIA
snapshot of the focused element, not from Chrome's accessibility tree or ANDI.
"""

from __future__ import annotations

import json
from pathlib import Path

from playwright.async_api import ElementHandle, Frame, Page

from a11y_assist.browser import LogFn
from a11y_assist.models import BoundingBox, FocusStop, FocusWalk

# The focused element in this frame's document, descending open shadow roots.
_DEEP_ACTIVE_JS = """() => {
  let el = document.activeElement;
  while (el && el.shadowRoot && el.shadowRoot.activeElement) {
    el = el.shadowRoot.activeElement;
  }
  return el;
}"""

# A Playwright CSS selector for an element. A space between the shadow host's
# path and the inner path means "descend into the open shadow root".
_DESCRIBE_JS = """(el) => {
  const seg = (n) => {
    const root = n.getRootNode();
    if (n.id && root.querySelectorAll('#' + CSS.escape(n.id)).length === 1) {
      return { s: '#' + CSS.escape(n.id), unique: true };
    }
    const tag = n.tagName.toLowerCase();
    const p = n.parentElement;
    if (!p) return { s: tag, unique: false };
    const same = Array.from(p.children).filter((c) => c.tagName === n.tagName);
    const s = same.length > 1 ? `${tag}:nth-of-type(${same.indexOf(n) + 1})` : tag;
    return { s, unique: false };
  };
  const path = (n) => {
    const parts = [];
    let cur = n;
    while (cur && cur.nodeType === 1) {
      const { s, unique } = seg(cur);
      parts.unshift(s);
      if (unique || !cur.parentElement) break;
      cur = cur.parentElement;
    }
    const root = n.getRootNode();
    const local = parts.join(' > ');
    return root.host ? path(root.host) + ' ' + local : local;
  };
  const tag = el.tagName.toLowerCase();
  return {
    selector: path(el),
    tag,
    tabindex: el.getAttribute('tabindex'),
    isBody: el === document.body || el === document.documentElement,
    isFrame: tag === 'iframe' || tag === 'frame',
    pageHasFocus: document.hasFocus(),
  };
}"""

MAX_FRAME_DEPTH = 10

# Tab press cap per pass, from the 4.C spec (section 2, P1): 3 x inventory + 50,
# at most 3,000.
CAP_PER_CANDIDATE = 3
CAP_BASE = 50
CAP_MAX = 3000

# Tabbable candidates in one frame's document and its open shadow roots: every
# element that is natively focusable or has tabindex >= 0, not disabled, not
# inert and rendered (4.C spec section 2, Setup). Used for the press cap, DNA
# cross-checks and coverage notes only; it never decides an outcome.
_INVENTORY_JS = """() => {
  const NATIVE = 'a[href], area[href], button, input:not([type="hidden"]), ' +
    'select, textarea, iframe, frame, summary, audio[controls], ' +
    'video[controls], [contenteditable]:not([contenteditable="false"])';
  const inert = (el) => {
    for (let n = el; n; ) {
      if (n.nodeType === 1 && n.hasAttribute('inert')) return true;
      n = n.parentNode || (n.host ? n.host : null);
    }
    return false;
  };
  const rendered = (el) => el.checkVisibility
    ? el.checkVisibility({ visibilityProperty: true })
    : el.getClientRects().length > 0;
  const candidate = (el) => {
    const ti = el.getAttribute('tabindex');
    if (ti !== null && ti.trim() !== '' && !isNaN(ti) && parseInt(ti, 10) < 0) {
      return false;
    }
    const focusable = el.matches(NATIVE) ||
      (ti !== null && ti.trim() !== '' && !isNaN(ti));
    if (!focusable) return false;
    if (el.tagName === 'SUMMARY' &&
        !(el.parentElement && el.parentElement.tagName === 'DETAILS' &&
          el.parentElement.querySelector(':scope > summary') === el)) {
      return false;
    }
    return !el.matches(':disabled') && !inert(el) && rendered(el);
  };
  let count = 0;
  const walk = (root) => {
    for (const el of root.querySelectorAll('*')) {
      if (candidate(el)) count += 1;
      if (el.shadowRoot) walk(el.shadowRoot);
    }
  };
  walk(document);
  return count;
}"""


def tab_press_cap(inventory_size: int) -> int:
    return min(CAP_PER_CANDIDATE * inventory_size + CAP_BASE, CAP_MAX)


async def dom_inventory(page: Page) -> tuple[int, int]:
    """Count tabbable candidates in every frame Playwright can reach.

    Returns (candidates, unreachable frames). Closed shadow roots cannot be
    read from page script and are not counted.
    """
    count, unreachable = 0, 0
    for frame in page.frames:
        try:
            count += await frame.evaluate(_INVENTORY_JS)
        except Exception:
            unreachable += 1
    return count, unreachable


def parse_aria_line(snapshot: str) -> tuple[str | None, str | None]:
    """Role and name from the first line of a Playwright ARIA snapshot,
    e.g. '- button "Save"' -> ("button", "Save")."""
    line = snapshot.splitlines()[0] if snapshot else ""
    if not line.startswith("- "):
        return None, None
    rest = line[2:]
    role = rest.split(" ", 1)[0].rstrip(":")
    after = rest[len(role) :].lstrip()
    name = None
    if after.startswith('"'):
        try:
            name, _ = json.JSONDecoder().raw_decode(after)
        except json.JSONDecodeError:
            name = None
    return role or None, name


async def _focused(page: Page) -> tuple[Frame, ElementHandle | None, dict, list[str]]:
    frame, frame_path = page.main_frame, []
    for _ in range(MAX_FRAME_DEPTH):
        el = (await frame.evaluate_handle(_DEEP_ACTIVE_JS)).as_element()
        if el is None:
            return frame, None, {}, frame_path
        info = await el.evaluate(_DESCRIBE_JS)
        child = await el.content_frame() if info["isFrame"] else None
        if child is None:
            return frame, el, info, frame_path
        frame_path.append(info["selector"])
        frame = child
    return frame, None, {}, frame_path


async def _role_and_name(frame: Frame, selector: str) -> tuple[str | None, str | None]:
    locator = frame.locator(selector)
    if await locator.count() != 1:
        return None, None
    return parse_aria_line(await locator.aria_snapshot(timeout=2000))


async def describe_focus(
    page: Page, index: int, key: str, screenshot: Path | None, rel_base: Path
) -> FocusStop:
    frame, el, info, frame_path = await _focused(page)
    role = name = None
    box = None
    if el is not None and not info.get("isBody"):
        role, name = await _role_and_name(frame, info["selector"])
        bb = await el.bounding_box()
        box = BoundingBox(**bb) if bb else None
    shot_rel = None
    if screenshot is not None:
        await page.screenshot(path=str(screenshot), animations="disabled")
        shot_rel = screenshot.resolve().relative_to(rel_base.resolve()).as_posix()
    return FocusStop(
        index=index,
        key=key,
        selector=info.get("selector"),
        tag=info.get("tag"),
        role=role,
        accessible_name=name,
        tabindex=info.get("tabindex"),
        bounding_box=box,
        frame_path=frame_path,
        url=frame.url,
        screenshot=shot_rel,
        is_body=bool(info.get("isBody", el is None)),
        page_has_focus=bool(info.get("pageHasFocus", False)),
    )


def _same_stop(a: FocusStop, b: FocusStop) -> bool:
    return (a.selector, a.frame_path, a.is_body) == (
        b.selector,
        b.frame_path,
        b.is_body,
    )


async def focus_walk(
    page: Page,
    forward: bool,
    max_presses: int,
    inventory_size: int,
    out_dir: Path,
    rel_base: Path,
    log: LogFn,
    settle_ms: int = 50,
) -> FocusWalk:
    """Press Tab (or Shift+Tab) up to max_presses times, recording each stop.

    The caller sets max_presses; the pipeline uses tab_press_cap().

    Ends early when focus returns to the first recorded stop (one full cycle)
    or the top-level page navigates. Either way it is evidence, not a verdict.
    """
    key = "Tab" if forward else "Shift+Tab"
    direction = "forward" if forward else "backward"
    out_dir.mkdir(parents=True, exist_ok=True)
    navigations: list[str] = []
    page.on(
        "framenavigated",
        lambda f: navigations.append(f.url) if f == page.main_frame else None,
    )

    stops: list[FocusStop] = []
    stopped_because = "cap"
    presses = 0
    for i in range(max_presses):
        try:
            await page.keyboard.press(key)
            presses += 1
            await page.wait_for_timeout(settle_ms)
            if navigations:
                stopped_because = "navigation"
                log(
                    "focus_walk_navigation",
                    "info",
                    direction=direction,
                    url=navigations[0],
                )
                break
            stop = await describe_focus(
                page, i, key, out_dir / f"{i:03d}.png", rel_base
            )
        except Exception as exc:  # record and stop; never guess
            stopped_because = "error"
            log(
                "focus_walk_error",
                "error",
                direction=direction,
                press=i,
                error=repr(exc),
            )
            break
        stops.append(stop)
        if i > 0 and _same_stop(stop, stops[0]):
            stopped_because = "returned_to_start"
            break

    log(
        "focus_walk",
        "ok",
        direction=direction,
        presses=presses,
        stops=len(stops),
        stopped_because=stopped_because,
    )
    return FocusWalk(
        direction=direction,
        max_presses=max_presses,
        inventory_size=inventory_size,
        presses=presses,
        stops=stops,
        stopped_because=stopped_because,
    )
