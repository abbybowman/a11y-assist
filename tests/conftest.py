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
import time
from collections import Counter
from pathlib import Path

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

from a11y_assist import egress
from a11y_assist.browser import launch_browser
from a11y_assist.config import Settings
from a11y_assist.egress import EgressProxy

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        allowed_domains=["127.0.0.1"],
        dev_mode=True,
        browser_channel=os.getenv("TEST_BROWSER_CHANNEL", "chromium"),
        headless=os.getenv("TEST_HEADED") != "1",
        browser_args=[
            "--disable-features=LocalNetworkAccessChecks",
            # Tests never use the network: the vendored Baseline page loads
            # jQuery from cdnjs (which its own wrong SRI hash blocks anyway).
            "--host-resolver-rules=MAP cdnjs.cloudflare.com ~NOTFOUND",
        ],
        runs_dir=tmp_path / "runs",
        # The fixture servers listen on 127.0.0.1 only (any port). 127.0.0.2
        # stays refused: tests use it as a sentinel for leaks.
        dev_allowed_addresses=["127.0.0.1/32"],
    )


async def offline_resolver(host: str, port: int) -> list[str]:
    """Tests never use the network: only IP literals and localhost resolve."""
    import ipaddress

    if host == "localhost":
        return ["127.0.0.1"]
    try:
        return [str(ipaddress.ip_address(host))]
    except ValueError:
        raise OSError(f"offline: {host} not resolved") from None


@pytest.fixture(autouse=True)
def _offline_dns(monkeypatch):
    monkeypatch.setattr(egress, "RESOLVER", offline_resolver)


@pytest_asyncio.fixture
async def browser(settings: Settings):
    async with EgressProxy(settings) as proxy, async_playwright() as pw:
        b = await launch_browser(pw, settings, proxy)
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
        if self.path == "/slow.html":  # answers after the run's time limit
            time.sleep(16)
            return self._send(200, b"<!doctype html><title>slow</title><p>late")
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
        path = self.path.split("?")[0]  # fixtures may add a query (F29 paging)
        fixture = FIXTURES / path.lstrip("/")
        if path.endswith(".html") and fixture.is_file():
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


ACT_ROOT = FIXTURES / "act"


class _ActHandler(http.server.SimpleHTTPRequestHandler):
    """Serves tests/fixtures/act as the web root (ACT pages use /WAI/... paths)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ACT_ROOT), **kwargs)

    def log_message(self, *args) -> None:
        pass


@pytest.fixture(scope="session")
def act_server():
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _ActHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


BASELINE_ROOT = FIXTURES / "baseline"


class _BaselineHandler(http.server.SimpleHTTPRequestHandler):
    """Serves tests/fixtures/baseline (Section 508 Baseline Alignment pages)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASELINE_ROOT), **kwargs)

    def log_message(self, *args) -> None:
        pass


@pytest.fixture(scope="session")
def baseline_server():
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _BaselineHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def pytest_sessionstart(session):
    # Only the controller clears the scores (pytest-xdist workers have a
    # workerinput); a worker clearing them would delete the others' results.
    if not hasattr(session.config, "workerinput"):
        from .scoring import clear_scores

        clear_scores()


# Progress for long and headed runs, which print only dots under -q (Abby,
# 2026-11-02). Only the controller writes: xdist forwards every worker's reports.
PROGRESS = Path(__file__).parent.parent / "runs" / "test-progress.txt"
_progress = {"t0": time.monotonic(), "total": 0, "done": 0, "failed": []}


def pytest_collection_finish(session):
    _progress["total"] = len(session.items)  # serial runs


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node, ids):
    _progress["total"] = len(ids)


def pytest_runtest_logreport(report):
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return
    if report.failed:
        _progress["failed"].append(f"{report.nodeid} ({report.when})")
    if report.when == "call" or (report.when == "setup" and not report.passed):
        _progress["done"] += 1
    p = _progress
    took = time.monotonic() - p["t0"]
    eta = took / p["done"] * (p["total"] - p["done"]) if p["done"] else 0
    lines = [
        f"{p['done']} of {p['total']} done, {took / 60:.1f} min elapsed,"
        f" about {eta / 60:.0f} min left",
        f"last: {report.nodeid}",
        f"failed ({len(p['failed'])}):",
        *p["failed"],
    ]
    PROGRESS.parent.mkdir(exist_ok=True)
    PROGRESS.write_text("\n".join(lines) + "\n")


def pytest_terminal_summary(terminalreporter):
    from .scoring import report_lines

    for line in report_lines():
        terminalreporter.write_line(line)
