"""V1-V13: browser behavior the 4.C spec depends on.

Each test asserts what was observed, so a different result on another browser
or OS fails loudly. Results that contradict a spec assumption are marked
CONTRADICTS in the docstring; those need a spec decision before rules use them.
"""

from __future__ import annotations

import json
from pathlib import Path

from .conftest import active, deep_active, press_and_read

THREE_LINKS = """<!doctype html><html lang=en><title>three</title><p>Text</p>
<a id=a1 href=#>one</a> <a id=a2 href=#>two</a> <a id=a3 href=#>three</a>"""

INNER = """<!doctype html><html lang=en><title>inner</title>
<button id=ib1>in 1</button><button id=ib2>in 2</button>"""


def _ids(seq: list) -> list:
    return [s["id"] for s in seq]


# ── V1 ────────────────────────────────────────────────────────────────────────


async def test_v1_first_tab_lands_on_first_element_without_focusing(context, pages):
    """V1: after load, the page already has focus and the first Tab lands on
    the first tabbable element. No click or bring_to_front is needed."""
    page = await context.new_page()
    await page.goto(pages.add("/three.html", THREE_LINKS))
    assert await active(page) == {"id": "BODY", "hasFocus": True}
    await page.keyboard.press("Tab")
    assert await active(page) == {"id": "a1", "hasFocus": True}


async def test_v1_second_page_in_context_gets_focus_after_bring_to_front(
    context, pages
):
    """V1: with two pages open, the one brought to front takes the keys."""
    url = pages.add("/three.html", THREE_LINKS)
    p1 = await context.new_page()
    await p1.goto(url)
    p2 = await context.new_page()
    await p2.goto(url)
    await p1.bring_to_front()
    await p1.keyboard.press("Tab")
    assert await active(p1) == {"id": "a1", "hasFocus": True}


# ── V2, V3 ───────────────────────────────────────────────────────────────────


async def test_v2_tab_past_last_element_leaves_page_then_wraps(context, pages):
    """V2: Tab past the last element moves focus out of the page (OUT):
    activeElement is BODY and document.hasFocus() is false. The next Tab
    returns to the first element. Supports the spec's OUT detection and wrap."""
    page = await context.new_page()
    await page.goto(pages.add("/three.html", THREE_LINKS))
    seq = await press_and_read(page, "Tab", 6)
    assert seq == [
        {"id": "a1", "hasFocus": True},
        {"id": "a2", "hasFocus": True},
        {"id": "a3", "hasFocus": True},
        {"id": "BODY", "hasFocus": False},
        {"id": "a1", "hasFocus": True},
        {"id": "a2", "hasFocus": True},
    ]


async def test_v3_shift_tab_before_first_element_leaves_page_then_wraps(context, pages):
    """V3: from a fresh load Shift+Tab starts at the last element; past the
    first it goes OUT (BODY, hasFocus false); the next one wraps to the last."""
    page = await context.new_page()
    await page.goto(pages.add("/three.html", THREE_LINKS))
    seq = await press_and_read(page, "Shift+Tab", 5)
    assert seq == [
        {"id": "a3", "hasFocus": True},
        {"id": "a2", "hasFocus": True},
        {"id": "a1", "hasFocus": True},
        {"id": "BODY", "hasFocus": False},
        {"id": "a3", "hasFocus": True},
    ]


# ── V4 ────────────────────────────────────────────────────────────────────────


async def test_v4_ctrl_tab_reaches_the_page_and_does_not_switch_tabs(context, pages):
    """V4: Playwright's Ctrl+Tab is delivered to the page as a keydown and is
    not handled as the browser's next-tab shortcut. The other page sees nothing
    and focus in the page does not move."""
    url = pages.add(
        "/keys.html",
        "<!doctype html><html lang=en><title>k</title><a id=a1 href=#>x</a>"
        "<script>window.keys=[];addEventListener('keydown',"
        "e=>keys.push((e.ctrlKey?'Ctrl+':'')+e.key),true)</script>",
    )
    p1 = await context.new_page()
    await p1.goto(url)
    p2 = await context.new_page()
    await p2.goto(url)
    await p1.bring_to_front()
    await p1.keyboard.press("Tab")
    await p1.keyboard.press("Control+Tab")
    assert "Ctrl+Tab" in await p1.evaluate("keys")
    assert await p2.evaluate("keys") == []
    assert await active(p1) == {"id": "a1", "hasFocus": True}


# ── V5 ────────────────────────────────────────────────────────────────────────


async def _cdp_active_in_frame(context, page, frame) -> dict:
    """(frame ID, backend node ID) of a frame's activeElement through CDP.

    A cross-origin frame is out of process in headed Chrome (its own CDP
    target) but in process in Playwright's headless shell, so both are handled.
    """
    try:
        session = await context.new_cdp_session(frame)
        oopif = True
    except Exception:
        session = await context.new_cdp_session(page)
        oopif = False
    contexts: list[dict] = []
    session.on("Runtime.executionContextCreated", lambda e: contexts.append(e))
    await session.send("Runtime.enable")
    tree = await session.send("Page.getFrameTree")

    def find(node):
        if node["frame"]["url"] == frame.url:
            return node["frame"]["id"]
        for child in node.get("childFrames", []):
            hit = find(child)
            if hit:
                return hit
        return None

    frame_id = find(tree["frameTree"])
    ctx_id = next(
        c["context"]["id"]
        for c in contexts
        if c["context"]["auxData"].get("frameId") == frame_id
        and c["context"]["auxData"].get("isDefault")
    )
    res = await session.send(
        "Runtime.evaluate",
        {"expression": "document.activeElement", "contextId": ctx_id},
    )
    node = await session.send(
        "DOM.describeNode", {"objectId": res["result"]["objectId"]}
    )
    return {
        "oopif": oopif,
        "frame_id": frame_id,
        "backend_node_id": node["node"]["backendNodeId"],
        "attributes": node["node"].get("attributes", []),
    }


async def test_v5_tab_enters_and_leaves_cross_origin_iframe(context, pages):
    """V5: Tab moves into a cross-origin iframe, through its controls and out
    again. Playwright frames read the focused element inside it, and CDP gives
    its (frame ID, backend node ID), whether or not the frame is out of process.
    The iframe element itself is not a separate stop here."""
    pages.add("/inner.html", INNER)
    url = pages.add(
        "/outer.html",
        "<!doctype html><html lang=en><title>o</title><a id=before href=#>b</a>"
        f"<iframe id=xo title=x src='{pages.other}/inner.html'></iframe>"
        "<a id=after href=#>a</a>",
    )
    page = await context.new_page()
    await page.goto(url)
    seq = await press_and_read(page, "Tab", 5, deep=True)
    assert [(s["path"], s["id"], s["topHasFocus"]) for s in seq] == [
        ([], "before", True),
        (["xo"], "ib1", True),
        (["xo"], "ib2", True),
        ([], "after", True),
        ([], "BODY", False),
    ]

    await page.goto(url)
    await page.keyboard.press("Tab")
    await page.keyboard.press("Tab")
    await page.keyboard.press("Tab")
    frame = next(f for f in page.frames if f.url.startswith(pages.other))
    ident = await _cdp_active_in_frame(context, page, frame)
    assert ident["attributes"] == ["id", "ib2"]
    assert ident["frame_id"] and ident["backend_node_id"] > 0


# ── V6 ────────────────────────────────────────────────────────────────────────


async def test_v6_closed_shadow_root_focus_resolves_through_cdp(context, pages):
    """V6: page script sees only the shadow host as activeElement, but CDP
    (DOM.getDocument pierce + shadowRoot.activeElement) resolves the focused
    element inside a closed shadow root to a backend node ID."""
    url = pages.add(
        "/closed.html",
        "<!doctype html><html lang=en><title>c</title><a id=before href=#>b</a>"
        "<div id=host></div><script>const r=document.getElementById('host')"
        ".attachShadow({mode:'closed'});r.innerHTML="
        "'<button id=sb1>s1</button><button id=sb2>s2</button>';</script>",
    )
    page = await context.new_page()
    await page.goto(url)
    await press_and_read(page, "Tab", 3)
    assert (await active(page))["id"] == "host"

    session = await context.new_cdp_session(page)
    await session.send("DOM.enable")
    doc = await session.send("DOM.getDocument", {"depth": -1, "pierce": True})

    def roots(node, acc):
        acc.extend(node.get("shadowRoots", []))
        for child in node.get("children", []):
            roots(child, acc)
        return acc

    [root] = roots(doc["root"], [])
    assert root["shadowRootType"] == "closed"
    obj = await session.send(
        "DOM.resolveNode", {"backendNodeId": root["backendNodeId"]}
    )
    res = await session.send(
        "Runtime.callFunctionOn",
        {
            "objectId": obj["object"]["objectId"],
            "functionDeclaration": "function () { return this.activeElement; }",
        },
    )
    node = await session.send(
        "DOM.describeNode", {"objectId": res["result"]["objectId"]}
    )
    assert node["node"]["attributes"] == ["id", "sb2"]
    assert node["node"]["backendNodeId"] > 0


# ── V7 ────────────────────────────────────────────────────────────────────────

REMOVE = """<!doctype html><html lang=en><title>r</title><a id=a1 href=#>1</a>
<button id=gone>gone</button><a id=a3 href=#>3</a><a id=a4 href=#>4</a>
<script>document.getElementById('gone').addEventListener('focus',
  e => setTimeout(() => e.target.remove(), 50));</script>"""


async def test_v7_tab_after_focused_element_is_removed_continues_after_it(
    context, pages
):
    """V7: when the focused element removes itself, focus falls to BODY while
    the page keeps focus (hasFocus true, unlike OUT). The next Tab continues
    with the element after the removed one; Shift+Tab goes to the one before.
    Supports the BODY rule: resuming after the lost element is no event."""
    url = pages.add("/remove.html", REMOVE)
    page = await context.new_page()
    await page.goto(url)
    seq = []
    for _ in range(4):
        await page.keyboard.press("Tab")
        await page.wait_for_timeout(150)
        seq.append(await active(page))
    assert seq == [
        {"id": "a1", "hasFocus": True},
        {"id": "BODY", "hasFocus": True},
        {"id": "a3", "hasFocus": True},
        {"id": "a4", "hasFocus": True},
    ]

    await page.goto(url)
    await page.keyboard.press("Tab")
    await page.keyboard.press("Tab")
    await page.wait_for_timeout(150)
    await page.keyboard.press("Shift+Tab")
    assert await active(page) == {"id": "a1", "hasFocus": True}


# ── V8 ────────────────────────────────────────────────────────────────────────


async def test_v8_click_on_text_sets_the_tab_starting_point(context, pages):
    """V8: clicking non-interactive text leaves focus on BODY but sets the
    sequential focus starting point: Tab goes to the next element after the
    text, Shift+Tab to the one before. Supports the P6 mouse bypass."""
    url = pages.add(
        "/click.html",
        "<!doctype html><html lang=en><title>c</title>"
        "<a id=a1 href=#>1</a> <a id=a2 href=#>2</a>"
        "<p id=mid style='height:40px'>Plain text in the middle</p>"
        "<a id=a3 href=#>3</a> <a id=a4 href=#>4</a>",
    )
    page = await context.new_page()
    await page.goto(url)
    await page.click("#mid")
    assert (await active(page))["id"] == "BODY"
    await page.keyboard.press("Tab")
    assert (await active(page))["id"] == "a3"
    await page.click("#mid")
    await page.keyboard.press("Shift+Tab")
    assert (await active(page))["id"] == "a2"


# ── V9 ────────────────────────────────────────────────────────────────────────


async def test_v9_tabindex_minus_one_iframe_content_is_not_in_tab_sequence(
    context, pages
):
    """V9: Tab skips a tabindex=-1 iframe AND everything inside it, for both
    same- and cross-origin frames.

    CONTRADICTS the spec's assumption for F33 ("tabindex=-1 iframe containing a
    loop" expected FAIL): Tab never reaches the loop, so no trap is observable
    by keyboard. Needs a spec decision before F33 is built.
    """
    pages.add("/inner.html", INNER)
    for src in (
        "srcdoc='<button id=ib1>n1</button><button id=ib2>n2</button>'",
        f"src='{pages.other}/inner.html'",
    ):
        url = pages.add(
            "/neg.html",
            "<!doctype html><html lang=en><title>n</title><a id=before href=#>b</a>"
            f"<iframe id=neg title=n tabindex=-1 {src}></iframe>"
            "<a id=after href=#>a</a>",
        )
        page = await context.new_page()
        await page.goto(url)
        seq = await press_and_read(page, "Tab", 4, deep=True)
        assert [(s["path"], s["id"]) for s in seq] == [
            ([], "before"),
            ([], "after"),
            ([], "BODY"),
            ([], "before"),
        ], src
        # The content is focusable by script, just not by Tab.
        frame = page.frames[1]
        await frame.focus("#ib1")
        assert (await deep_active(page))["path"] == ["neg"]
        await page.close()


# ── V10 ───────────────────────────────────────────────────────────────────────

FEED = """<!doctype html><html lang=en><title>f</title>
<div id=feed><a href=#>item 0</a></div><p id=status></p>
<div style='height:5000px'></div>
<script>
let n = 0;
async function more() {
  const out = document.getElementById('status');
  try {
    const r = await fetch('/more.json?page=' + (++n));
    const j = await r.json();
    document.getElementById('feed')
      .insertAdjacentHTML('beforeend', '<a href=#>' + j.item + '</a>');
    out.textContent = 'ok ' + n;
  } catch (e) { out.textContent = 'error ' + e.name; }
}
window.addEventListener('scroll', more);
</script>"""


async def test_v10_replay_aborts_requests_it_never_recorded(
    browser, context, pages, tmp_path: Path
):
    """V10: in the frozen-page replay (route_from_har, not_found='abort'), a
    request that was recorded is answered again, and a scroll-triggered request
    that was never recorded fails (fetch rejects with TypeError). The feed
    stops at what the recording loaded.

    CONTRADICTS the spec's infinite-scroll signs: the inventory cannot grow
    past what was recorded, so "inventory grows past 2x" and "page height
    grows every 10 presses" only fire if the recording itself scrolled far
    enough. Needs a spec decision before F29 is built.
    """
    url = pages.add("/feed.html", FEED)
    pages.add("/more.json", json.dumps({"item": "more"}), "application/json")
    har = tmp_path / "feed.har.zip"
    rec = await browser.new_context(record_har_path=str(har), record_har_mode="full")
    page = await rec.new_page()
    await page.goto(url)
    await page.evaluate("more()")  # recorded: page=1
    await page.wait_for_function("document.getElementById('status').textContent")
    await rec.close()

    await context.route_from_har(str(har), not_found="abort")
    page = await context.new_page()
    await page.goto(url)
    status = "document.getElementById('status').textContent"
    await page.evaluate("more()")  # page=1: in the HAR
    await page.wait_for_function(f"{status} === 'ok 1'")
    await page.mouse.wheel(0, 2000)  # page=2: never recorded
    await page.wait_for_function(f"{status} !== 'ok 1'")
    assert await page.evaluate(status) == "error TypeError"
    assert await page.locator("#feed a").count() == 2


# ── V11 ───────────────────────────────────────────────────────────────────────

ESC = """<!doctype html><html lang=en><title>e</title><button id=b>b</button>
<script>window.keys=[];addEventListener('keydown',e=>keys.push(e.key),true)</script>"""


async def test_v11_page_receives_escape_and_chrome_does_not_act_on_it(context, pages):
    """V11: Escape sent by Playwright reaches the page's keydown listener. Chrome
    does not consume it: it does not exit fullscreen and does not stop a load
    in progress. Supports M4 (Escape then Tab)."""
    page = await context.new_page()
    await page.goto(pages.add("/esc.html", ESC))
    await page.click("#b")  # user activation for requestFullscreen
    await page.evaluate("document.documentElement.requestFullscreen()")
    await page.wait_for_function("!!document.fullscreenElement")
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    assert await page.evaluate("keys") == ["Escape"]
    assert await page.evaluate("!!document.fullscreenElement")

    pages.add("/hang.png", "", "image/png")
    url = pages.add("/loading.html", ESC + "<img alt='' src='/hang.png'>")
    await page.goto(url, wait_until="domcontentloaded")
    assert await page.evaluate("document.readyState") != "complete"
    await page.focus("#b")
    await page.keyboard.press("Escape")
    assert await page.evaluate("keys") == ["Escape"]
    # Loading was not stopped: the load event still fires when the image ends.
    await page.wait_for_load_state("load", timeout=10_000)


# ── V12 ───────────────────────────────────────────────────────────────────────


async def test_v12_tab_order_matches_dom_order_across_control_types(context, pages):
    """V12: Tab visits links, buttons, inputs, tabindex=0, select and textarea
    in DOM order, goes OUT after the last, and wraps. Run this file headless and
    headed (TEST_HEADED=1); the expected sequence is the same in both."""
    url = pages.add(
        "/walk.html",
        "<!doctype html><html lang=en><title>w</title><a id=w1 href=#>1</a>"
        "<button id=w2>2</button><input id=w3 aria-label=w3>"
        "<div id=w4 tabindex=0>4</div><select id=w5 aria-label=w5>"
        "<option>x</option></select><textarea id=w6 aria-label=w6></textarea>"
        "<a id=w7 href=#>7</a>",
    )
    page = await context.new_page()
    await page.goto(url)
    seq = await press_and_read(page, "Tab", 9)
    assert _ids(seq) == ["w1", "w2", "w3", "w4", "w5", "w6", "w7", "BODY", "w1"]
    assert seq[7]["hasFocus"] is False


# ── V13 ───────────────────────────────────────────────────────────────────────


async def test_v13_arrow_keys_change_a_closed_select_and_fire_change(context, pages):
    """V13: ArrowDown on a focused, closed native select changes its value
    without opening it, fires input and change each time, and keeps focus on
    the select. Checked on Linux here; Windows behavior must be run there."""
    url = pages.add(
        "/sel.html",
        "<!doctype html><html lang=en><title>s</title>"
        "<select id=s aria-label=s><option>a</option><option>b</option>"
        "<option>c</option></select><a id=after href=#>after</a>"
        "<script>window.ev=[];const s=document.getElementById('s');"
        "s.addEventListener('change',()=>ev.push('change:'+s.value));"
        "s.addEventListener('input',()=>ev.push('input:'+s.value));</script>",
    )
    page = await context.new_page()
    await page.goto(url)
    await page.keyboard.press("Tab")
    await page.keyboard.press("ArrowDown")
    await page.keyboard.press("ArrowDown")
    assert await page.evaluate("document.getElementById('s').value") == "c"
    assert await page.evaluate("ev") == ["input:b", "change:b", "input:c", "change:c"]
    assert await active(page) == {"id": "s", "hasFocus": True}
    await page.keyboard.press("Tab")
    assert (await active(page))["id"] == "after"
