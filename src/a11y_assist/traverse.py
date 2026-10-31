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

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from playwright.async_api import BrowserContext, CDPSession, Page

from a11y_assist.models import BoundingBox, PassResult, Step, Stop

# Tab press cap per pass (4.C spec section 2, P1): 3 x inventory + 50, max 3,000.
CAP_PER_CANDIDATE = 3
CAP_BASE = 50
CAP_MAX = 3000

# Settle rule (4.C spec section 2). The quiet window is settings.settle_quiet_ms.
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
  // A short CSS-like path, for describing elements in the log (not identity:
  // stops are identified through CDP).
  const path = (n) => {
    const parts = [];
    for (let c = n, k = 0; c && c.nodeType === 1 && k < 6; c = c.parentElement, k++) {
      if (c.id) { parts.unshift('#' + c.id); break; }
      const p = c.parentElement;
      const same = p ? Array.from(p.children).filter((x) => x.tagName === c.tagName) : [];
      parts.unshift(c.tagName.toLowerCase() + (same.length > 1 ? `:nth-of-type(${same.indexOf(c) + 1})` : ''));
    }
    return parts.join(' > ');
  };
  for (const type of ["focusin", "focusout"]) {
    addEventListener(type, (e) => {
      const el = e.composedPath()[0];
      const rel = e.relatedTarget;
      log.f.push({
        type, t: Math.round(performance.now()), tag: el && el.tagName || null, id: el && el.id || null,
        trusted: e.isTrusted, css: el && el.nodeType === 1 ? path(el) : null,
        rel: rel && rel.nodeType === 1 ? path(rel) : null,
        rel_inside: !!(rel && el && el.contains && el.contains(rel)),
      });
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
  const tag = this.tagName.toLowerCase();
  const role = this.getAttribute('role');
  const COMPOSITE = '[role=menubar],[role=menu],[role=tablist],[role=grid],[role=treegrid],[role=tree],' +
    '[role=listbox],[role=toolbar],[role=radiogroup]';
  let widget = null;
  const host = this.closest(COMPOSITE);
  if (host) widget = path(host);
  else if (tag === 'input' && this.type === 'radio' && this.name) widget = 'radio:' + this.name;
  const type = (this.type || '').toLowerCase();
  let field = null;
  if (tag === 'select') field = 'select';
  else if (tag === 'textarea' || (tag === 'input' && !['button','submit','reset','image','checkbox','radio','range','color','file','hidden'].includes(type))) field = 'text';
  else if (tag === 'input' && type === 'checkbox') field = 'checkbox';
  const collapsed = this.getAttribute('aria-expanded') === 'false' ||
    (tag === 'summary' && !!this.parentElement && this.parentElement.tagName === 'DETAILS' && !this.parentElement.open);
  const dlg = this.closest('dialog, [role=dialog], [role=alertdialog]');
  const modal = !!dlg && ((dlg.tagName === 'DIALOG' && dlg.matches(':modal')) || dlg.getAttribute('aria-modal') === 'true');
  return { css: path(this), tag, x: r.x, y: r.y, w: r.width, h: r.height,
           isBody: this === document.body || this === document.documentElement,
           widget, field, collapsed, modal };
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

    async def call(self, stop: Stop, fn: str, args: list[Any] | None = None) -> Any:
        """Run `fn` (a JS function declaration; `this` is the element) on the
        stop's element in the isolated world, where page script cannot change
        what it sees. Returns its value, or None if the stop cannot be reached."""
        if stop.kind != "element" or stop.unresolved:
            return None
        frame_id, _, backend = stop.key.rpartition(":")
        try:
            session, ctx = await self._session_for(frame_id)
            obj = await session.send(
                "DOM.resolveNode",
                {"backendNodeId": int(backend), "executionContextId": ctx},
            )
            res = await session.send(
                "Runtime.callFunctionOn",
                {
                    "objectId": obj["object"]["objectId"],
                    "functionDeclaration": fn,
                    "arguments": [{"value": a} for a in (args or [])],
                    "returnByValue": True,
                },
            )
            return res["result"].get("value")
        except Exception:
            return None

    async def evaluate_top(self, expression: str) -> Any:
        """Evaluate in the top frame's isolated world."""
        session, ctx = await self._session_for(await self._top_frame_id())
        res = await session.send(
            "Runtime.evaluate",
            {"expression": expression, "contextId": ctx, "returnByValue": True},
        )
        return res["result"].get("value")

    async def _top_frame_id(self) -> str:
        if self._top is None:
            self._top = await self.context.new_cdp_session(self.page)
        tree = await self._top.send("Page.getFrameTree")
        return tree["frameTree"]["frame"]["id"]

    async def read(self) -> tuple[Stop, bool]:
        """(stop, top document hasFocus). After a navigation the cached worlds
        are gone, so they are dropped and the read is retried once."""
        try:
            return await self._read()
        except Exception:
            self._worlds.clear()
            self._top = None
            return await self._read()

    async def _read(self) -> tuple[Stop, bool]:
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
                        session,
                        ctx,
                        node,
                        info,
                        chain,
                        offset_x,
                        offset_y,
                        frame_id,
                        obj,
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
                session, ctx, node, info, chain, offset_x, offset_y, frame_id, obj
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

    async def _element(
        self, session, ctx, node, info, chain, ox, oy, frame_id, obj
    ) -> Stop:
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
            widget=(" >> ".join([*chain, info["widget"]]) if info["widget"] else None),
            field=info["field"],
            collapsed=info["collapsed"],
            modal=info["modal"],
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


async def settle(page: Page, quiet_ms: int, window_ms: int = SETTLE_MAX_MS) -> bool:
    """Wait per the settle rule: 2 animation frames, then until the DOM has been
    quiet for `quiet_ms`. Returns False if the limit was hit (unsettled)."""
    try:
        await page.evaluate(
            "() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
        )
    except Exception:
        pass
    waited = 0
    while waited < window_ms:
        _, _, since_m, since_f = await _read_logs(page)
        if since_m >= quiet_ms and since_f >= quiet_ms:
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
    quiet_ms: int
    shots_dir: Path | None = None
    rel_base: Path | None = None
    hooks: list[StepHook] = field(default_factory=list)
    reader: FocusReader = field(init=False)
    steps: list[Step] = field(default_factory=list)
    _seen_focus: dict[str, int] = field(default_factory=dict)
    _last_focus_total: int = 0
    _last_mutations: int = 0

    def __post_init__(self) -> None:
        self.reader = FocusReader(self.context, self.page)

    async def start(self) -> None:
        await settle(self.page, self.quiet_ms)
        for hook in self.hooks:
            if hasattr(hook, "on_start"):
                await hook.on_start(self)
        m, f, _, _ = await _read_logs(self.page)
        self._last_mutations, self._last_focus_total = m, f
        await _focus_events(self.page, self._seen_focus)

    async def press(self, key: str) -> Step:
        # A focus change after the last step was read: re-read that step after
        # the 1,000 ms window (settle rule).
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
        settled = await settle(self.page, self.quiet_ms)
        stop, has_focus = await self.reader.read()
        m, f, _, _ = await _read_logs(self.page)
        step = Step(
            n=len(self.steps) + 1,
            key=key,
            stop=stop,
            top_url=self.page.url,
            top_has_focus=has_focus,
            open_pages=len(self.context.pages),
            mutations=m - self._last_mutations,
            focus_events=await _focus_events(self.page, self._seen_focus),
            unsettled=not settled,
        )
        self._last_mutations, self._last_focus_total = m, f
        self.steps.append(step)
        for hook in self.hooks:
            value = await hook.on_step(self, step)
            if value is not None:
                step.extras[hook.name] = value
        return step

    async def shoot(self, label: str) -> str | None:
        """Viewport screenshot of the current state, attached to the last step.
        Taken only where the spec asks (a trap event), not on every press."""
        if self.shots_dir is None or not self.steps:
            return None
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        path = self.shots_dir / f"{label}-{len(self.steps):04d}.png"
        await self.page.screenshot(path=str(path), animations="disabled")
        rel = path.resolve().relative_to(self.rel_base.resolve()).as_posix()
        self.steps[-1] = self.steps[-1].model_copy(update={"screenshot": rel})
        return rel


def navigated(step: Step, start_url: str, start_pages: int) -> bool:
    """Top-level navigation, reload or a new page (the fragment is ignored)."""
    return (
        step.top_url.split("#")[0] != start_url.split("#")[0]
        or step.open_pages > start_pages
    )


def detect_continuation(
    steps: list[Step], first_key: str | None
) -> tuple[str, list[str]] | None:
    """End of a continuation from a stop mid-page: OUT means traversal got past
    the rest of the page (a wrap); otherwise P1's stuck and loop conditions."""
    if steps and steps[-1].stop.kind == "OUT":
        return "wrap", []
    return detect_p1_end(steps, None)


NewPage = Callable[[], Awaitable[tuple[BrowserContext, Page]]]


class StepHook(Protocol):
    """Extra evidence a check asks the walk to collect at every step (a walk
    extra). Called after the step is settled and read; the return value is
    stored in step.extras[name]. Collects facts only, never outcomes."""

    name: str

    async def on_step(self, t: Traversal, step: Step) -> Any: ...


Detector = Callable[[list[Step], str | None], tuple[str, list[str]] | None]


@dataclass
class Session:
    """A fresh page load with a Traversal, for passes and probes."""

    traversal: Traversal
    inventory: Inventory
    start_url: str
    start_pages: int
    failed_requests: list[str] = field(default_factory=list)

    @property
    def page(self) -> Page:
        return self.traversal.page

    async def close(self) -> None:
        # A fresh context per load: pages can keep state (localStorage, cookies)
        # that would make the next "fresh" load differ.
        await self.traversal.context.close()


async def open_session(
    new_page: NewPage,
    quiet_ms: int,
    shots_dir: Path | None = None,
    rel_base: Path | None = None,
    hooks: list[StepHook] | None = None,
) -> Session:
    context, page = await new_page()
    inv = await dom_inventory(page)
    t = Traversal(context, page, quiet_ms, shots_dir, rel_base, list(hooks or []))
    await t.start()
    s = Session(t, inv, page.url, len(context.pages))
    # Requests the recorded page cannot answer (infinite-scroll sign, V10).
    page.on("requestfailed", lambda r: s.failed_requests.append(r.url))
    return s


async def drive(
    s: Session,
    key: str,
    cap: int,
    detector: Detector = detect_p1_end,
    deadline: float | None = None,
) -> tuple[str, list[str], list[Step]]:
    """Press `key` until the detector ends it, navigation, the cap or the
    deadline (time.monotonic()). Returns (end, trap stop keys, own steps)."""
    start = len(s.traversal.steps)
    first_key = None
    for _ in range(cap):
        if deadline is not None and time.monotonic() > deadline:
            return "time", [], s.traversal.steps[start:]
        step = await s.traversal.press(key)
        own = s.traversal.steps[start:]
        if navigated(step, s.start_url, s.start_pages):
            return "navigation", [], own
        if first_key is None and step.stop.kind == "element":
            first_key = step.stop.key
        hit = detector(own, first_key)
        if hit:
            return hit[0], hit[1], own
    return "cap", [], s.traversal.steps[start:]


async def run_pass(
    name: str,
    new_page: NewPage,
    key: str,
    quiet_ms: int,
    deadline: float | None = None,
    shots_dir: Path | None = None,
    rel_base: Path | None = None,
    cap: int | None = None,
    hooks: list[StepHook] | None = None,
) -> PassResult:
    """Fresh load, then press `key` until a wrap, a trap event, navigation, the
    cap or the deadline. A trap event gets one screenshot."""
    s = await open_session(new_page, quiet_ms, shots_dir, rel_base, hooks)
    cap = cap if cap is not None else tab_press_cap(s.inventory.candidates)
    base = dict(
        name=name,
        keys=[],
        cap=cap,
        inventory=s.inventory.candidates,
        start_url=s.start_url,
        start_pages=s.start_pages,
    )
    try:
        end, trap, _ = await drive(s, key, cap, detect_p1_end, deadline)
        if end in ("stuck", "loop"):
            await s.traversal.shoot(name)
        end_inv = (await dom_inventory(s.page)).candidates
        return PassResult(
            steps=s.traversal.steps,
            end=end,
            trap=trap,
            failed_requests=len(s.failed_requests),
            inventory_end=end_inv,
            **base,
        )
    except Exception as exc:  # record and stop; never guess
        return PassResult(steps=s.traversal.steps, end="error", error=repr(exc), **base)
    finally:
        await s.close()


# Visible text of every frame (comments, <title> and hidden text are not in
# innerText). Evidence for J1 and J2; page text is never instructions.
_TEXT_JS = "() => document.body ? document.body.innerText : ''"


async def page_text(page: Page) -> list[dict[str, str]]:
    out = []
    for frame in page.frames:
        try:
            text = await frame.evaluate(_TEXT_JS)
        except Exception:
            continue
        if text.strip():
            out.append({"source": frame.url, "text": text})
    return out


# Mouse bypass (4.C spec section 6): a visible, non-interactive text spot just
# after the trap in DOM order. `paths` are top-document CSS paths of the trap
# (for a trap inside a frame, the top-level iframe element).
_BYPASS_JS = """(paths) => {
  // A shadow boundary is a lone space (not part of ' > '); use the host there.
  const find = (p) => { try { return document.querySelector(p) || document.querySelector(p.split(/(?<!>) (?!>)/)[0]); } catch (e) { return null; } };
  const els = paths.map(find).filter(Boolean);
  if (!els.length) return null;
  const last = els.reduce((a, b) => (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? b : a));
  const INTERACTIVE = 'a, button, input, select, textarea, summary, label, [tabindex], [contenteditable], [role=button], [role=link]';
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  walker.currentNode = last;
  let n = walker.nextNode();
  while (n && last.contains(n)) n = walker.nextNode();
  for (; n; n = walker.nextNode()) {
    if (!n.textContent.trim() || n.parentElement.closest(INTERACTIVE)) continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    const r = range.getClientRects()[0];
    if (r && r.width > 0 && r.height > 0) return { x: r.x + Math.min(r.width / 2, 5), y: r.y + r.height / 2 };
  }
  return null;
}"""

# Fallback: script focus() on the next tabbable element after the trap.
_FOCUS_NEXT_JS = """(paths) => {
  // A shadow boundary is a lone space (not part of ' > '); use the host there.
  const find = (p) => { try { return document.querySelector(p) || document.querySelector(p.split(/(?<!>) (?!>)/)[0]); } catch (e) { return null; } };
  const els = paths.map(find).filter(Boolean);
  if (!els.length) return false;
  const last = els.reduce((a, b) => (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? b : a));
  const all = Array.from(document.querySelectorAll('a[href], button, input, select, textarea, [tabindex]'))
    .filter((e) => e.tabIndex >= 0 && !e.disabled && e.checkVisibility());
  const next = all.find((e) => last.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING && !last.contains(e));
  if (!next) return false;
  next.focus();
  return true;
}"""


async def bypass(page: Page, top_paths: list[str]) -> str | None:
    """Click past the trap; fall back to script focus(). Returns "click",
    "focus" (fallback, logged), or None if neither was possible."""
    point = await page.evaluate(_BYPASS_JS, top_paths)
    if point:
        await page.mouse.click(point["x"], point["y"])
        return "click"
    if await page.evaluate(_FOCUS_NEXT_JS, top_paths):
        return "focus"
    return None
