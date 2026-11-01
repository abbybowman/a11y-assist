"""Read where keyboard focus is, for browser checks and fixture tests.

Records facts only (element id, page focus). Never decides an outcome.
"""

from __future__ import annotations

# id of the focused element, descending open shadow roots (a closed root shows
# its host), plus document.hasFocus().
ACTIVE_JS = """() => {
  let a = document.activeElement;
  while (a && a.shadowRoot && a.shadowRoot.activeElement) {
    a = a.shadowRoot.activeElement;
  }
  return { id: a ? (a.id || a.tagName) : null, hasFocus: document.hasFocus() };
}"""


async def active(page_or_frame) -> dict:
    return await page_or_frame.evaluate(ACTIVE_JS)


async def deep_active(page) -> dict:
    """Focused element followed into iframes, plus the top document's focus."""
    top = await active(page)
    frame, path = page.main_frame, []
    for _ in range(5):
        el = (await frame.evaluate_handle("() => document.activeElement")).as_element()
        if el is None:
            break
        child = await el.content_frame()
        if child is None:
            break
        path.append(await el.evaluate("e => e.id"))
        frame = child
    return {"path": path, **(await active(frame)), "topHasFocus": top["hasFocus"]}


async def press_and_read(page, key: str, n: int, deep: bool = False) -> list:
    out = []
    for _ in range(n):
        await page.keyboard.press(key)
        out.append(await (deep_active(page) if deep else active(page)))
    return out
