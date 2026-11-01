"""What an action changes: a snapshot of the page before and after it, and
the effect between them (4.A spec, Terms: effect). Shared by 4.A (click,
Enter and Space on controls), 4.B (key-press proof) and 5.D (completing a
field and tabbing away). Records facts only; what an effect means for an
outcome is each check's rules.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field

from a11y_assist.traverse import Session, _read_logs, settle, submissions

# Before the action, the page is watched this long; DOM changes in it are
# page noise (animation), so an effect of only DOM changes is unreliable.
NOISE_MS = 300


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


async def observe(
    s: Session,
    quiet_ms: int,
    act: Callable[[], Awaitable[None]],
    own: str | None,
    submits: bool = False,
) -> Effect:
    """What an action changes (spec: Terms, effect). `own` is the path key of
    the element acted on: focus moving onto it (a click) is not an effect.
    `submits` (5.D) also records form submissions as the effect "submit";
    off for 4.A and 4.B, whose specs do not read it."""
    page = s.page
    await settle(page, quiet_ms)
    before = await snapshot(s)
    sub0 = len(await submissions(page)) if submits else 0
    m0, *_ = await _read_logs(page)
    await page.wait_for_timeout(NOISE_MS)
    m1, *_ = await _read_logs(page)
    await act()
    await settle(page, quiet_ms)
    after = await snapshot(s)
    sub1 = len(await submissions(page)) if submits else 0
    m2, *_ = await _read_logs(page)
    e = Effect(mutations=max(0, m2 - m1), noise=max(0, m1 - m0))
    if after["url"] != before["url"]:
        e.kinds.append("navigation")
        e.url = after["url"]
    elif after["frames"] != before["frames"]:
        e.kinds.append("frame_navigation")
    if sub1 > sub0:
        e.kinds.append("submit")
    if after["pages"] > before["pages"]:
        e.kinds.append("new_page")
    if after["dialogs"] != before["dialogs"]:
        e.kinds.append("dialog")
    f = after["focus"]
    if f != before["focus"] and not (own and f and f.startswith(own)):
        e.kinds.append("focus")
    if e.mutations > 0:
        e.kinds.append("dom")
    return e
