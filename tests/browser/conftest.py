"""Browser behavior checks V1-V13 (docs/rules/4c-build-tasks.md).

Each test records what Chrome does through Playwright, so a rule that depends
on it can rely on a checked fact. Run them in headed Chrome on Windows with:

    TEST_BROWSER_CHANNEL=chrome TEST_HEADED=1 uv run pytest tests/browser -v

`pages` serves in-memory pages from one local server. The same port is
reachable as 127.0.0.1 (`base`) and as localhost (`other`), which are
different sites, so `other` pages are cross-origin iframes.
"""

from __future__ import annotations

import http.server
import threading
import time

import pytest

ACTIVE_JS = """() => {
  const a = document.activeElement;
  return { id: a ? (a.id || a.tagName) : null, hasFocus: document.hasFocus() };
}"""


class _PageHandler(http.server.BaseHTTPRequestHandler):
    pages: dict[str, tuple[str, str]]

    def log_message(self, *args) -> None:
        pass

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path == "/hang.png":  # never finishes within a test
            time.sleep(5)
        entry = self.pages.get(path)
        if entry is None:
            self.send_response(404)
            self.end_headers()
            return
        body, ctype = entry
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class PageServer:
    def __init__(self) -> None:
        handler = type("H", (_PageHandler,), {"pages": {}})
        self._pages = handler.pages
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = self.httpd.server_address[1]
        self.base = f"http://127.0.0.1:{port}"
        self.other = f"http://localhost:{port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def add(self, path: str, body: str, ctype: str = "text/html") -> str:
        self._pages[path] = (body, ctype)
        return self.base + path

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def pages():
    s = PageServer()
    yield s
    s.stop()


@pytest.fixture
async def context(browser, settings):
    ctx = await browser.new_context(
        viewport={"width": settings.viewport_width, "height": settings.viewport_height}
    )
    yield ctx
    await ctx.close()


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
