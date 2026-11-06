"""Data leakage (GSA template: "Error Handling", "Testing Requirements").

Seed secrets in a URL query string and in page errors, then check they appear
in neither the tool error, the result's `errors`, the run log (steps.jsonl),
Python logging nor the process's stdout/stderr. The saved report and the
recorded evidence may keep the full URL (the user's own record).
"""

from __future__ import annotations

import http.server
import json
import logging
import socket
import threading

import pytest
from fastmcp import Client

from tobi508 import config
from tobi508.app import mcp
from tobi508.redact import safe_error, safe_url, scrub

QUERY_SECRET = "QSECRET-7f3a91"
PAGE_SECRET = "PSECRET-c04e22"
HEADER_SECRET = "HSECRET-5b1d80"


class _Leaky(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass

    def _send(self, status: int, body: bytes = b"", **headers) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        port = self.server.server_address[1]
        path = self.path.split("?")[0]
        if path == "/page.html":
            body = (
                "<!doctype html><html lang=en><title>t</title><button>Go</button>"
                f"<script>console.error('{PAGE_SECRET}');"
                f"fetch('/api?token={QUERY_SECRET}');"
                f"throw new Error('{PAGE_SECRET}');</script>"
            )
            return self._send(200, body.encode(), **{"Set-Cookie": HEADER_SECRET})
        if path == "/api":
            return self._send(500, PAGE_SECRET.encode())
        if path == "/redir":
            to = f"http://localhost:{port}/x?token={QUERY_SECRET}"
            return self._send(302, Location=to)
        self._send(404)


@pytest.fixture
def leaky():
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Leaky)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture(autouse=True)
def _use_test_settings(settings, monkeypatch):
    monkeypatch.setattr(config, "settings", settings)


SECRETS = (QUERY_SECRET, PAGE_SECRET, HEADER_SECRET)


def _assert_clean(where: str, text: str) -> None:
    for s in SECRETS:
        assert s not in text, f"{s} leaked into {where}"


def _logs(settings) -> str:
    if not settings.runs_dir.exists():
        return ""
    return "".join(p.read_text("utf-8") for p in settings.runs_dir.rglob("*.jsonl"))


async def _call(name: str, args: dict):
    async with Client(mcp) as client:
        return await client.call_tool(name, args, raise_on_error=False)


def _check_process_output(capfd, caplog) -> None:
    out, err = capfd.readouterr()
    _assert_clean("stdout", out)
    _assert_clean("stderr", err)
    _assert_clean("python logging", caplog.text)


async def test_secrets_stay_out_of_logs_on_a_tested_page(
    settings, leaky, capfd, caplog
):
    caplog.set_level(logging.DEBUG)
    url = f"{leaky}/page.html?token={QUERY_SECRET}"
    result = await _call("tobi_run_tt_tests", {"url": url, "tests": ["4.C"]})
    assert not result.is_error
    out = json.loads(result.content[0].text)
    _assert_clean("result errors", json.dumps(out["errors"]))
    log = _logs(settings)
    assert '"step":"run_start"' in log  # the log exists and was written
    _assert_clean("steps.jsonl", log)
    _check_process_output(capfd, caplog)
    # The saved report keeps the full URL: it is the user's record.
    report = next(settings.runs_dir.rglob("report.json")).read_text("utf-8")
    assert QUERY_SECRET in report


async def test_secrets_stay_out_of_a_redirect_refusal(settings, leaky, capfd, caplog):
    caplog.set_level(logging.DEBUG)
    url = f"{leaky}/redir?token={QUERY_SECRET}"
    result = await _call("tobi_run_tt_tests", {"url": url, "tests": ["4.C"]})
    assert result.is_error
    msg = result.content[0].text
    assert "blocked" in msg.lower()
    _assert_clean("tool error", msg)
    _assert_clean("steps.jsonl", _logs(settings))
    _check_process_output(capfd, caplog)


async def test_secrets_stay_out_of_a_load_failure(settings, capfd, caplog):
    caplog.set_level(logging.DEBUG)
    with socket.socket() as s:  # a port with nothing listening
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    url = f"http://127.0.0.1:{port}/p?token={QUERY_SECRET}"
    result = await _call("tobi_run_tt_tests", {"url": url, "tests": ["4.C"]})
    assert result.is_error
    msg = result.content[0].text
    assert "could not be loaded" in msg
    _assert_clean("tool error", msg)
    assert "Call log" not in msg and "Traceback" not in msg
    _check_process_output(capfd, caplog)


async def test_unexpected_exception_is_one_redacted_line(settings, monkeypatch):
    from tobi508.tools import run_tt_tests as tool

    async def boom(*args, **kwargs):
        raise RuntimeError(
            f"failed at https://x.gov/a?token={QUERY_SECRET}\n"
            f"Call log:\n  - cookie: {HEADER_SECRET}\nTraceback (most recent call last)"
        )

    monkeypatch.setattr(tool, "run_pipeline", boom)
    result = await _call(
        "tobi_run_tt_tests", {"url": "https://x.gov/a", "tests": ["4.C"]}
    )
    assert result.is_error
    msg = result.content[0].text
    assert msg == "RuntimeError: failed at https://x.gov/a"
    _assert_clean("tool error", msg)


def test_redaction_rules():
    assert safe_url("https://u:p@x.gov:8443/a/b?q=1#f") == "https://x.gov:8443/a/b"
    assert safe_url("http://[::1]:80/a?b") == "http://[::1]:80/a"
    assert scrub("go to https://x.gov/p?t=1 now") == "go to https://x.gov/p now"
    err = safe_error(ValueError("x" * 500))
    assert len(err) <= 200 and err.startswith("ValueError: ")
