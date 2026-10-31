"""Keyboard traversal: press keys on a fresh page load and record every step.

Records facts only. Trap *events* (stuck, loop, wrap) are detected here because
the spec defines a pass's end by them (4.C section 2); what an event means for
an outcome is decided only by the rules module of a test (e.g. t4c.py).

Where focus is, is read through CDP in an isolated JavaScript world, so page
script cannot spoof document.activeElement. Focus is followed into iframes
(in-process or out-of-process) and into open and closed shadow roots (V5, V6).
Role and name come from Chrome's accessibility tree.

The settle rule (4.C spec section 2) uses a log of DOM mutations and focus
events that an init script installs in every frame before page scripts run
(V14). That log only decides how long to wait and when to flag a step
unsettled; it never decides where focus is.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext, CDPSession, Page

from a11y_assist.models import BoundingBox, PassResult, Step, Stop

# Tab press cap per pass (4.C spec section 2, P1): 3 x inventory + 50, max 3,000.
CAP_PER_CANDIDATE = 3
CAP_BASE = 50
CAP_MAX = 3000

# Settle rule (4.C spec section 2).
MUTATION_QUIET_MS = 300
SETTLE_MAX_MS = 1500
RERUN_WINDOW_MS = 1000
POLL_MS = 50

WORLD = "a11y-assist"

# Runs in every frame before page scripts (main world, so it sees page events).
INIT_JS = """(() => {
  if (window.__a11yLog) return;
  const log = { m: 0, lastM: 0, f: [], lastF: 0 };
  Object.defineProperty(window, "__a11yLog", { value: log });
  const obs = new MutationObserver((r) => { log.m += r.length; log.lastM = performance.now(); });
  obs.observe(document, { subtree: true, childList: true, attributes: true, characterData: true });
  const watchRoot = (root) => obs.observe(root, { subtree: true, childList: true, attributes: true, characterData: true });
  const attach = Element.prototype.attachShadow;
  Element.prototype.attachShadow = function (init) { const r = attach.call(this, init); watchRoot(r); return r; };
  for (const type of ["focusin", "focusout"]) {
    addEventListener(type, (e) => {
      const el = e.composedPath()[0];
      log.f.push({ type, t: Math.round(performance.now()), tag: el && el.tagName || null, id: el && el.id || null });
      log.lastF = performance.now();
    }, true);
  }
})();"""

_LOG_JS = """() => {
  const l = window.__a11yLog;
  if (!l) return null;
  const now = performance.now();
  return { m: l.m, f: l.f.length, sinceM: l.lastM ? now - l.lastM : 1e9, sinceF: l.lastF ? now - l.lastF : 1e9 };
}"""

_EVENTS_JS = "(from) => (window.__a11yLog ? window.__a11yLog.f.slice(from) : [])"

# A11y-world helpers. `this` is the element.
_DESCRIBE_FN = """function () {
  const seg = (n) => {
    const root = n.getRootNode();
    if (n.id && root.querySelectorAll('#' + CSS.escape(n.id)).length === 1) return { s: '#' + CSS.escape(n.id), unique: true };
    const tag = n.tagName.toLowerCase();
    const p = n.parentElement;
    if (!p) return { s: tag, unique: false };
    const same = Array.from(p.children).filter((c) => c.tagName === n.tagName);
    return { s: same.length > 1 ? `${tag}:nth-of-type(${same.indexOf(n) + 1})` : tag, unique: false };
  };
  const path = (n) => {
    const parts = [];
    for (let cur = n; cur && cur.nodeType === 1; cur = cur.parentElement) {
      const { s, unique } = seg(cur);
      parts.unshift(s);
      if (unique || !cur.parentElement) break;
    }
    const root = n.getRootNode();
    return (root.host ? path(root.host) + ' ' : '') + parts.join(' > ');
  };
  const r = this.getBoundingClientRect();
  return { css: path(this), tag: this.tagName.toLowerCase(), x: r.x, y: r.y, w: r.width, h: r.height,
           isBody: this === document.body || this === document.documentElement };
}"""

_ACTIVE_FN = "function () { return this.activeElement; }"

# Tabbable candidates in one frame's document and its open shadow roots
# (4.C spec section 2, Setup): natively focusable or tabindex >= 0, not
# disabled, not inert, rendered (not display:none or visibility:hidden).
_INVENTORY_JS = """() => {
  const NATIVE = 'a[href], area[href], button, input:not([type="hidden"]), select, textarea, ' +
    'iframe, frame, summary, audio[controls], video[controls], [contenteditable]:not([contenteditable="false"])';
  const inert = (el) => {
    for (let n = el; n; n = n.parentNode || n.host || null) if (n.nodeType === 1 && n.hasAttribute('inert')) return true;
    return false;
  };
  const rendered = (el) => el.checkVisibility
    ? el.checkVisibility({ visibilityProperty: true }) : el.getClientRects().length > 0;
  const tabindex = (el) => {
    const v = el.getAttribute('tabindex');
    return v !== null && v.trim() !== '' && !isNaN(v) ? parseInt(v, 10) : null;
  };
  const candidate = (el) => {
    const ti = tabindex(el);
    if (ti !== null && ti < 0) return false;
    if (!(el.matches(NATIVE) || ti !== null)) return false;
    if (el.tagName === 'SUMMARY' && !(el.parentElement && el.parentElement.tagName === 'DETAILS' &&
        el.parentElement.querySelector(':scope > summary') === el)) return false;
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

_NEG_TABINDEX_FRAME_JS = """(el) => {
  const v = el.getAttribute('tabindex');
  return v !== null && v.trim() !== '' && !isNaN(v) && parseInt(v, 10) < 0;
}"""


def tab_press_cap(inventory_size: int) -> int:
    return min(CAP_PER_CANDIDATE * inventory_size + CAP_BASE, CAP_MAX)


@dataclass
class Inventory:
    candidates: int
    unreachable_frames: int = 0
    # Focusable elements inside tabindex=-1 iframes: left out of `candidates`
    # because Tab cannot reach them (V9); reported for 4.A.
    keyboard_unreachable: int = 0


async def dom_inventory(page: Page) -> Inventory:
    inv = Inventory(0)
    for frame in page.frames:
        try:
            n = await frame.evaluate(_INVENTORY_JS)
        except Exception:
            inv.unreachable_frames += 1
            continue
        skipped = False
        f = frame
        while f.parent_frame is not None:
            owner = await f.frame_element()
            if await owner.evaluate(_NEG_TABINDEX_FRAME_JS):
                skipped = True
                break
            f = f.parent_frame
        if skipped:
            inv.keyboard_unreachable += n
        else:
            inv.candidates += n
    return inv


class FocusReader:
    """Reads the focused element through CDP, one instance per page load."""

    def __init__(self, context: BrowserContext, page: Page):
        self.context, self.page = context, page
        self._top: CDPSession | None = None
        self._worlds: dict[str, tuple[CDPSession, int]] = {}

    async def _session_for(self, frame_id: str) -> tuple[CDPSession, int]:
        if frame_id in self._worlds:
            return self._worlds[frame_id]
        if self._top is None:
            self._top = await self.context.new_cdp_session(self.page)
        candidates = [self._top]
        for f in self.page.frames[1:]:  # out-of-process frames have own sessions
            try:
                candidates.append(await self.context.new_cdp_session(f))
            except Exception:
                pass
        for s in candidates:
            try:
                w = await s.send(
                    "Page.createIsolatedWorld",
                    {"frameId": frame_id, "worldName": WORLD},
                )
            except Exception:
                continue
            self._worlds[frame_id] = (s, w["executionContextId"])
            return self._worlds[frame_id]
        raise LookupError(f"no CDP session reaches frame {frame_id}")

    async def _top_frame_id(self) -> str:
        if self._top is None:
            self._top = await self.context.new_cdp_session(self.page)
        tree = await self._top.send("Page.getFrameTree")
        return tree["frameTree"]["frame"]["id"]

    async def read(self) -> tuple[Stop, bool]:
        """(stop, top document hasFocus)."""
        frame_id = await self._top_frame_id()
        session, ctx = await self._session_for(frame_id)
        has_focus = (
            await session.send(
                "Runtime.evaluate",
                {
                    "expression": "document.hasFocus()",
                    "contextId": ctx,
                    "returnByValue": True,
                },
            )
        )["result"]["value"]
        chain: list[str] = []
        offset_x = offset_y = 0.0
        res = await session.send(
            "Runtime.evaluate",
            {"expression": "document.activeElement", "contextId": ctx},
        )
        for _ in range(20):  # frames and shadow roots, deepest first
            obj = res["result"].get("objectId")
            if obj is None:
                break
            node = (
                await session.send(
                    "DOM.describeNode", {"objectId": obj, "depth": 1, "pierce": True}
                )
            )["node"]
            info = (
                await session.send(
                    "Runtime.callFunctionOn",
                    {
                        "objectId": obj,
                        "functionDeclaration": _DESCRIBE_FN,
                        "returnByValue": True,
                    },
                )
            )["result"]["value"]
            roots = node.get("shadowRoots", [])
            if roots:  # open or closed: CDP can read either
                root = await session.send(
                    "DOM.resolveNode",
                    {
                        "backendNodeId": roots[0]["backendNodeId"],
                        "executionContextId": ctx,
                    },
                )
                inner = await session.send(
                    "Runtime.callFunctionOn",
                    {
                        "objectId": root["object"]["objectId"],
                        "functionDeclaration": _ACTIVE_FN,
                    },
                )
                if inner["result"].get("objectId"):
                    res = inner
                    continue
            if node.get("frameId") and node["nodeName"] in ("IFRAME", "FRAME"):
                try:
                    child_session, child_ctx = await self._session_for(node["frameId"])
                except LookupError:
                    return self._unresolved(chain, info), has_focus
                child = await child_session.send(
                    "Runtime.evaluate",
                    {"expression": "document.activeElement", "contextId": child_ctx},
                )
                child_obj = child["result"].get("objectId")
                child_node = (
                    (
                        await child_session.send(
                            "DOM.describeNode", {"objectId": child_obj}
                        )
                    )["node"]
                    if child_obj
                    else None
                )
                child_focus = (
                    await child_session.send(
                        "Runtime.evaluate",
                        {
                            "expression": "document.hasFocus()",
                            "contextId": child_ctx,
                            "returnByValue": True,
                        },
                    )
                )["result"]["value"]
                if child_node is None or (
                    child_node["nodeName"] in ("BODY", "HTML") and not child_focus
                ):
                    # The iframe element itself holds focus (a valid stop).
                    return await self._element(
                        session, ctx, node, info, chain, offset_x, offset_y, frame_id
                    ), has_focus
                chain.append(info["css"])
                offset_x += info["x"]
                offset_y += info["y"]
                session, ctx, frame_id, res = (
                    child_session,
                    child_ctx,
                    node["frameId"],
                    child,
                )
                continue
            if info["isBody"]:
                if not chain and not has_focus:
                    return Stop(kind="OUT", key="OUT"), has_focus
                return Stop(kind="BODY", key="BODY", frame_chain=chain), has_focus
            return await self._element(
                session, ctx, node, info, chain, offset_x, offset_y, frame_id
            ), has_focus
        if not has_focus:
            return Stop(kind="OUT", key="OUT"), has_focus
        return Stop(kind="BODY", key="BODY", frame_chain=chain), has_focus

    def _unresolved(self, chain: list[str], info: dict) -> Stop:
        return Stop(
            kind="element",
            key=f"unresolved:{' >> '.join([*chain, info['css']])}",
            frame_chain=chain,
            css_path=info["css"],
            tag=info["tag"],
            unresolved=True,
        )

    async def _element(self, session, ctx, node, info, chain, ox, oy, frame_id) -> Stop:
        role = name = None
        try:
            ax = await session.send(
                "Accessibility.getPartialAXTree",
                {"backendNodeId": node["backendNodeId"], "fetchRelatives": False},
            )
            first = ax["nodes"][0]
            role = first.get("role", {}).get("value")
            name = first.get("name", {}).get("value")
        except Exception:
            pass
        box = BoundingBox(
            x=info["x"] + ox, y=info["y"] + oy, width=info["w"], height=info["h"]
        )
        vp = self.page.viewport_size or {"width": 0, "height": 0}
        in_vp = (
            box.width > 0
            and box.x < vp["width"]
            and box.y < vp["height"]
            and (box.x + box.width > 0 and box.y + box.height > 0)
        )
        frame_url = (
            await session.send(
                "Runtime.evaluate",
                {
                    "expression": "location.href",
                    "contextId": ctx,
                    "returnByValue": True,
                },
            )
        )["result"]["value"]
        return Stop(
            kind="element",
            key=f"{frame_id}:{node['backendNodeId']}",
            frame_chain=chain,
            css_path=info["css"],
            tag=info["tag"],
            role=role,
            name=name,
            bounding_box=box,
            in_viewport=in_vp,
            frame_url=frame_url,
        )


async def _read_logs(page: Page) -> tuple[int, int, float, float]:
    """Total mutations and focus events, and ms since the latest of each."""
    m = f = 0
    since_m = since_f = 1e9
    for frame in page.frames:
        try:
            v = await frame.evaluate(_LOG_JS)
        except Exception:
            continue
        if v:
            m += v["m"]
            f += v["f"]
            since_m = min(since_m, v["sinceM"])
            since_f = min(since_f, v["sinceF"])
    return m, f, since_m, since_f


async def _focus_events(page: Page, before: dict[str, int]) -> list[dict[str, Any]]:
    out = []
    for frame in page.frames:
        try:
            events = await frame.evaluate(_EVENTS_JS, before.get(frame.url, 0))
        except Exception:
            continue
        before[frame.url] = before.get(frame.url, 0) + len(events)
        out.extend({**e, "frame": frame.url} for e in events)
    return sorted(out, key=lambda e: e["t"])


async def settle(
    page: Page, focus_stable_ms: int, window_ms: int = SETTLE_MAX_MS
) -> bool:
    """Wait per the settle rule. Returns False if the limit was hit (unsettled)."""
    try:
        await page.evaluate(
            "() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
        )
    except Exception:
        pass
    waited = 0
    while waited < window_ms:
        _, _, since_m, since_f = await _read_logs(page)
        if since_m >= MUTATION_QUIET_MS and since_f >= focus_stable_ms:
            return True
        await page.wait_for_timeout(POLL_MS)
        waited += POLL_MS
    return False


def detect_p1_end(
    steps: list[Step], first_key: str | None
) -> tuple[str, list[str]] | None:
    """P1 end conditions (4.C spec section 2): wrap, stuck or loop."""
    keys = [s.stop.key for s in steps]
    if first_key and "OUT" in keys[:-1] and keys[-1] == first_key:
        return "wrap", []
    if len(keys) >= 3 and keys[-1] == keys[-2] == keys[-3] and keys[-1] != "OUT":
        return "stuck", [keys[-1]]
    for p in range(2, len(keys) // 2 + 1):
        cycle = keys[-p:]
        if keys[-2 * p : -p] == cycle and "OUT" not in cycle and len(set(cycle)) > 1:
            return "loop", sorted(set(cycle))
    return None


@dataclass
class Traversal:
    """One pass from a fresh load: replay `prefix`, then press `key` repeatedly."""

    context: BrowserContext
    page: Page
    focus_stable_ms: int
    shots_dir: Path | None = None
    rel_base: Path | None = None
    reader: FocusReader = field(init=False)
    steps: list[Step] = field(default_factory=list)
    _seen_focus: dict[str, int] = field(default_factory=dict)
    _last_focus_total: int = 0
    _last_mutations: int = 0

    def __post_init__(self) -> None:
        self.reader = FocusReader(self.context, self.page)

    async def start(self) -> None:
        await settle(self.page, self.focus_stable_ms)
        m, f, _, _ = await _read_logs(self.page)
        self._last_mutations, self._last_focus_total = m, f
        await _focus_events(self.page, self._seen_focus)

    async def press(self, key: str, label: str) -> Step:
        # A focus change after the last step's window: re-read that step (rule:
        # rerun with the 1,000 ms window).
        _, f, _, _ = await _read_logs(self.page)
        if self.steps and f != self._last_focus_total:
            prev = self.steps[-1]
            ok = await settle(
                self.page, RERUN_WINDOW_MS, RERUN_WINDOW_MS + SETTLE_MAX_MS
            )
            stop, has_focus = await self.reader.read()
            self.steps[-1] = prev.model_copy(
                update={
                    "stop": stop,
                    "top_has_focus": has_focus,
                    "rerun": True,
                    "unsettled": prev.unsettled or not ok,
                }
            )
            _, self._last_focus_total, _, _ = await _read_logs(self.page)
        await self.page.keyboard.press(key)
        settled = await settle(self.page, self.focus_stable_ms)
        stop, has_focus = await self.reader.read()
        m, f, _, _ = await _read_logs(self.page)
        shot = None
        if self.shots_dir is not None:
            self.shots_dir.mkdir(parents=True, exist_ok=True)
            path = self.shots_dir / f"{label}-{len(self.steps) + 1:04d}.png"
            await self.page.screenshot(path=str(path), animations="disabled")
            shot = path.resolve().relative_to(self.rel_base.resolve()).as_posix()
        step = Step(
            n=len(self.steps) + 1,
            key=key,
            stop=stop,
            top_url=self.page.url,
            top_has_focus=has_focus,
            open_pages=len(self.context.pages),
            mutations=m - self._last_mutations,
            focus_events=await _focus_events(self.page, self._seen_focus),
            screenshot=shot,
            unsettled=not settled,
        )
        self._last_mutations, self._last_focus_total = m, f
        self.steps.append(step)
        return step


def navigated(step: Step, start_url: str, start_pages: int) -> bool:
    """Top-level navigation, reload or a new page during a pass."""
    return (
        step.top_url.split("#")[0] != start_url.split("#")[0]
        or step.open_pages > start_pages
    )


async def run_pass(
    name: str,
    new_page: Callable[[], Awaitable[tuple[BrowserContext, Page]]],
    key: str,
    focus_stable_ms: int,
    prefix: list[str] | None = None,
    detector: Callable[
        [list[Step], str | None], tuple[str, list[str]] | None
    ] = detect_p1_end,
    cap: int | None = None,
    shots_dir: Path | None = None,
    rel_base: Path | None = None,
) -> PassResult:
    """Fresh load, replay `prefix` keys, then press `key` until the detector ends
    the pass or the cap is reached."""
    context, page = await new_page()
    inv = await dom_inventory(page)
    cap = cap if cap is not None else tab_press_cap(inv.candidates)
    t = Traversal(context, page, focus_stable_ms, shots_dir, rel_base)
    start_url, start_pages = page.url, len(context.pages)
    try:
        await t.start()
        for k in prefix or []:
            await t.press(k, name)
        replayed = len(t.steps)
        first_key = None
        for _ in range(cap):
            step = await t.press(key, name)
            if navigated(step, start_url, start_pages):
                return PassResult(
                    name=name,
                    keys=prefix or [],
                    steps=t.steps,
                    end="navigation",
                    cap=cap,
                    inventory=inv.candidates,
                )
            own = t.steps[replayed:]
            if first_key is None and step.stop.kind == "element":
                first_key = step.stop.key
            hit = detector(own, first_key)
            if hit:
                end, trap = hit
                return PassResult(
                    name=name,
                    keys=prefix or [],
                    steps=t.steps,
                    end=end,
                    trap=trap,
                    cap=cap,
                    inventory=inv.candidates,
                )
        return PassResult(
            name=name,
            keys=prefix or [],
            steps=t.steps,
            end="cap",
            cap=cap,
            inventory=inv.candidates,
        )
    except Exception as exc:  # record and stop; never guess
        return PassResult(
            name=name,
            keys=prefix or [],
            steps=t.steps,
            end="error",
            cap=cap,
            inventory=inv.candidates,
            error=repr(exc),
        )
    finally:
        await context.close()
