"""What an action changes: a snapshot of the page before and after it, and
the effect between them (4.A spec, Terms: effect). Shared by 4.A (click,
Enter and Space on controls), 4.B (key-press proof) and 5.D (completing a
field and tabbing away). Records facts only; what an effect means for an
outcome is each check's rules.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field

from a11y_assist.traverse import PATH_JS, Session, _read_logs, settle, submissions

# Paths of every element rendered in the top document, shadow roots included,
# with 4.A's own path builder and visibility test, so 4.A can match its keys
# (4.F's Enter presses: what they show, for 4.A's hover check).
SHOWN_JS = (
    "(() => {"
    + PATH_JS
    + """
  const out = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
    const v = el.checkVisibility
      ? el.checkVisibility({ visibilityProperty: true })
      : el.getClientRects().length > 0;
    if (v) out.push(path(el));
    if (el.shadowRoot) walk(el.shadowRoot); } };
  walk(document);
  return out;
})()"""
)


async def shown(s: Session) -> set[str] | None:
    """SHOWN_JS in the top frame's isolated world; None when it fails."""
    try:
        got = await s.traversal.reader.evaluate_top(SHOWN_JS)
    except Exception:
        return None
    return set(got) if isinstance(got, list) else None


# Open dialogs (4.E's walk extra; 2.D's pass T). The path is the dialog's
# identity across steps: a path cut short let two
# dialogs share one, so the second never counted as new (f09).
DIALOGS_JS = (
    "() => {"
    + PATH_JS
    + """
  const vis = (el) => el.checkVisibility
    ? el.checkVisibility({ visibilityProperty: true })
    : el.getClientRects().length > 0;
  const sel = 'dialog[open], [role=dialog], [role=alertdialog]';
  return Array.from(document.querySelectorAll(sel)).filter(vis)
    .map((el) => ({ css: path(el), name: el.getAttribute('aria-label') || '' }));
}"""
)

# Before the action, the page is watched this long; DOM changes in it are
# page noise (animation), so an effect of only DOM changes is unreliable.
NOISE_MS = 300

# A browser call that has not answered by then is abandoned (headed Chrome can
# leave one waiting when the action navigates the page); the page count then
# decides alone, as before.
CDP_TIMEOUT_S = 2.0


class Effect(BaseModel):
    kinds: list[str] = Field(default_factory=list)
    mutations: int = 0
    noise: int = 0
    url: str | None = None  # where a navigation went

    @property
    def any(self) -> bool:
        return bool(self.kinds)

    @property
    def unreliable(self) -> bool:
        return self.noise > 0 and self.kinds == ["dom"]


async def snapshot(s: Session) -> dict[str, Any]:
    page = s.page
    focus = None
    try:
        st, _ = await s.traversal.reader.read()
        focus = st.path_key
    except Exception:
        pass
    try:
        dialogs = await page.evaluate(
            "() => Array.from(document.querySelectorAll("
            "'dialog[open],[role=dialog],[role=alertdialog]'))"
            ".filter((e) => e.checkVisibility()).length"
        )
    except Exception:
        dialogs = None
    return {
        "url": page.url,
        "frames": sorted(f.url for f in page.frames),
        "pages": len(s.traversal.context.pages),
        "focus": focus,
        "dialogs": dialogs,
    }


class _Opened:
    """Pages the tested page opens, as the browser creates them. Counting
    context.pages after the settle can miss one on Windows, where a new page
    joins the list later or not at all; page script cannot spoof the
    browser's own event. `ok` is False when discovery did not start, and
    then only the page count decides."""

    def __init__(self, s: Session):
        self._s = s
        self._cdp: Any = None
        self.ids: set[str] = set()
        self.ok = False

    async def __aenter__(self) -> _Opened:
        def wait(call: Awaitable[Any]) -> Awaitable[Any]:
            return asyncio.wait_for(call, CDP_TIMEOUT_S)

        try:
            cdp = await wait(self._s.traversal.context.new_cdp_session(self._s.page))
            self._cdp = cdp
            info = await wait(cdp.send("Target.getTargetInfo"))
            own = info["targetInfo"]["targetId"]

            def created(ev: dict) -> None:
                info = ev.get("targetInfo", {})
                if info.get("type") == "page" and info.get("openerId") == own:
                    self.ids.add(info["targetId"])

            cdp.on("Target.targetCreated", created)
            await wait(cdp.send("Target.setDiscoverTargets", {"discover": True}))
            # Pages that already exist are reported before this answer; after
            # a timeout they could arrive late and read as new.
            self.ok = True
        except Exception:
            pass  # the page count below still applies
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._cdp is not None:
            try:
                await asyncio.wait_for(self._cdp.detach(), CDP_TIMEOUT_S)
            except Exception:
                pass


async def observe(
    s: Session,
    quiet_ms: int,
    act: Callable[[], Awaitable[None]],
    own: str | None,
    submits: bool = False,
    noise_ms: int = NOISE_MS,
) -> Effect:
    """What an action changes (spec: Terms, effect). `own` is the path key of
    the element acted on: focus moving onto it (a click) is not an effect.
    `submits` (5.D) also records form submissions as the effect "submit";
    off for 4.A and 4.B, whose specs do not read it. `noise_ms` 0 skips the
    noise window (5.D's leave step reuses the one its completion measured)."""
    page = s.page
    await settle(page, quiet_ms)
    before = await snapshot(s)
    sub0 = len(await submissions(page)) if submits else 0
    m0, *_ = await _read_logs(page)
    if noise_ms:
        await page.wait_for_timeout(noise_ms)
    m1, *_ = await _read_logs(page)
    async with _Opened(s) as opened:
        # Enabling discovery reports pages that already exist; only pages
        # created after this point are the action's.
        earlier = set(opened.ids)
        await act()
        await settle(page, quiet_ms)
        after = await snapshot(s)
        sub1 = len(await submissions(page)) if submits else 0
        m2, *_ = await _read_logs(page)
        new_windows = opened.ids - earlier if opened.ok else set()
    e = Effect(mutations=max(0, m2 - m1), noise=max(0, m1 - m0))
    if after["url"] != before["url"]:
        e.kinds.append("navigation")
        e.url = after["url"]
    elif after["frames"] != before["frames"]:
        e.kinds.append("frame_navigation")
    if sub1 > sub0:
        e.kinds.append("submit")
    if new_windows or after["pages"] > before["pages"]:
        e.kinds.append("new_page")
    if after["dialogs"] != before["dialogs"]:
        e.kinds.append("dialog")
    f = after["focus"]
    if f != before["focus"] and not (own and f and f.startswith(own)):
        e.kinds.append("focus")
    if e.mutations > 0:
        e.kinds.append("dom")
    return e
