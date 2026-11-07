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
import re
import threading
import time
from collections import Counter
from pathlib import Path

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

from tobi508 import egress
from tobi508.browser import launch_browser
from tobi508.config import Settings
from tobi508.egress import EgressProxy

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
        # Tool tests read a finished result from one call, even on a loaded
        # machine; the job tests in test_tools.py lower it on purpose.
        call_wait_s=600,
        # The rule tests were built on the 120 s limit (a page refused early,
        # a walk cut short): keep it for them; the server's default is 600 s.
        run_limit_s=120,
        # Each test records its pages afresh; test_pagecache.py turns the
        # cache on for itself.
        page_cache_s=0,
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


def _gif(forever: bool) -> bytes:
    """An animated GIF: 20 frames of 100 ms (2 s), looping forever or once."""
    import io

    from PIL import Image

    frames = [Image.new("RGB", (40, 40), (12 * i, 0, 255 - 12 * i)) for i in range(20)]
    out = io.BytesIO()
    extra = {"loop": 0} if forever else {}
    frames[0].save(
        out, "GIF", save_all=True, append_images=frames[1:], duration=100, **extra
    )
    return out.getvalue()


def _tone(seconds: int = 4, rate: int = 8000, loud: bool = True) -> bytes:
    import io
    import math
    import struct
    import wave

    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(
            b"".join(
                struct.pack(
                    "<h", int(12000 * loud * math.sin(2 * math.pi * 440 * i / rate))
                )
                for i in range(seconds * rate)
            )
        )
    return out.getvalue()


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
        if self.path == "/framed":  # a cross-site iframe (localhost vs 127.0.0.1)
            body = (
                "<!doctype html><html lang=en><title>framed</title>"
                "<a href='#top'>Top link</a>"
                f"<iframe title=inner src='http://localhost:{port}/inner'></iframe>"
            )
            return self._send(200, body.encode())
        if self.path == "/csp.html":  # a policy that forbids inline scripts
            body = "<!doctype html><html lang=en><title>csp</title><p>Policy</p>"
            return self._send(
                200, body.encode(), **{"Content-Security-Policy": "script-src 'self'"}
            )
        if self.path == "/inner":
            body = "<!doctype html><title>inner</title><button>Inner</button>"
            return self._send(200, body.encode())
        if self.path == "/tone.wav":  # 4 s, 440 Hz (2.A-2.D fixtures; no files)
            return self._send(200, _tone(), "audio/wav")
        if self.path in ("/anim-forever.gif", "/anim-once.gif"):  # 2.B, G152
            return self._send(
                200, _gif(forever=self.path == "/anim-forever.gif"), "image/gif"
            )
        tone = re.fullmatch(r"/(tone|silence)(\d+)\.wav", self.path)
        if tone:  # /tone20.wav: 20 s; /silence20.wav: 20 s of silence
            secs = int(tone.group(2))
            return self._send(
                200, _tone(secs, loud=tone.group(1) == "tone"), "audio/wav"
            )
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


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_auto_num_workers(config):
    """-n auto: one worker per CPU this container may use, not per CPU it sees.

    xdist counts the CPUs the scheduler shows (sched_getaffinity), which in a
    Kubernetes pod is every core of the node; the pod's CPU limit lives in the
    cgroup. On VAST (4-CPU limit) that started a Chromium per node core and the
    run stalled with no output. PYTEST_XDIST_AUTO_NUM_WORKERS still wins."""
    if os.environ.get("PYTEST_XDIST_AUTO_NUM_WORKERS"):
        return None  # xdist's own hook reads it
    seen = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else 0
    seen = seen or os.cpu_count() or 1
    try:  # cgroup v2: "max 100000" or "<quota> <period>"
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        limit = int(quota) // int(period) if quota != "max" else seen
    except (OSError, ValueError):
        try:  # cgroup v1
            cg = Path("/sys/fs/cgroup/cpu")
            quota = int((cg / "cpu.cfs_quota_us").read_text())
            period = int((cg / "cpu.cfs_period_us").read_text())
            limit = quota // period if quota > 0 else seen
        except (OSError, ValueError):
            limit = seen
    return max(1, min(seen, limit))


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
