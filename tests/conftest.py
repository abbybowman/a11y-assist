"""Shared fixtures: settings for tests, a browser, and a local HTTP server.

Tests use Playwright's bundled Chromium, headless, unless overridden:
  TEST_BROWSER_CHANNEL=chrome   use installed Google Chrome
  TEST_HEADED=1                 show the browser
"""

from __future__ import annotations

import http.server
import json
import os
import random
import threading
from collections import Counter
from pathlib import Path

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

from a11y_assist.browser import launch_browser
from a11y_assist.config import Settings

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        allowed_domains=["127.0.0.1"],
        dev_mode=True,
        browser_channel=os.getenv("TEST_BROWSER_CHANNEL", "chromium"),
        headless=os.getenv("TEST_HEADED") != "1",
        runs_dir=tmp_path / "runs",
    )


@pytest_asyncio.fixture
async def browser(settings: Settings):
    async with async_playwright() as pw:
        b = await launch_browser(pw, settings)
        yield b
        await b.close()


class _Handler(http.server.BaseHTTPRequestHandler):
    hits: Counter  # set per server

    def log_message(self, *args) -> None:
        pass

    def _send(self, status: int, body: bytes = b"", ctype="text/html", **headers):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        port = self.server.server_address[1]
        self.hits[(self.headers.get("Host", "").split(":")[0], self.path)] += 1
        nonce = str(random.random())
        routes = {
            "/redir-ok": (302, {"Location": "/hop"}),
            "/hop": (301, {"Location": "/dyn"}),
            "/redir-bad": (302, {"Location": f"http://localhost:{port}/landed"}),
            "/redir-bad-2": (302, {"Location": "/hop-bad"}),
            "/hop-bad": (302, {"Location": f"http://localhost:{port}/landed"}),
        }
        if self.path in routes:
            status, headers = routes[self.path]
            return self._send(status, **headers)
        if self.path == "/data.json":
            return self._send(
                200, json.dumps({"n": nonce}).encode(), "application/json"
            )
        if self.path in ("/dyn", "/landed"):
            body = (
                "<!doctype html><html lang=en><title>dyn</title>"
                f"<p id=srv>{nonce}</p><p id=xhr></p><button>Go</button>"
                "<script>fetch('/data.json').then(r=>r.json())"
                ".then(j=>{xhr.textContent=j.n})</script>"
            )
            return self._send(200, body.encode())
        fixture = FIXTURES / self.path.lstrip("/")
        if self.path.endswith(".html") and fixture.is_file():
            return self._send(200, fixture.read_bytes())
        self._send(404, b"not found")


class LocalServer:
    def __init__(self) -> None:
        handler = type("H", (_Handler,), {"hits": Counter()})
        self.hits = handler.hits
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def server():
    s = LocalServer()
    yield s
    s.stop()


def noop_log(*args, **kwargs) -> None:
    pass
