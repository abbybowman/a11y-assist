"""Inbound transport: stdio by default, HTTP only on loopback, and the
Host/Origin guard on every HTTP request (DNS-rebinding protection)."""

from __future__ import annotations

import http.client
import json
import socket
import threading
import time

import pytest
import uvicorn

from tobi508 import app
from tobi508.config import Settings


@pytest.fixture
def runs(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(app.mcp, "run", lambda **kw: calls.append(kw))
    return calls


def _use(monkeypatch, **fields):
    monkeypatch.setattr(app, "settings", Settings(_env_file=None, **fields))


@pytest.mark.parametrize("var", ["PORT", "DATABRICKS_APP_PORT"])
def test_platform_port_no_longer_opens_http(monkeypatch, runs, var):
    # The template bound unauthenticated HTTP to 0.0.0.0 when these were set.
    monkeypatch.setenv(var, "8080")
    _use(monkeypatch)
    app.main()
    assert runs == [{"transport": "stdio"}]


def test_http_binds_loopback_with_host_origin_guard(monkeypatch, runs):
    _use(monkeypatch, mcp_transport="streamable-http", mcp_port=8123)
    app.main()
    [call] = runs
    assert call["host"] == "127.0.0.1" and call["port"] == 8123
    assert call["host_origin_protection"] is True


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.5", "example.gov"])
def test_http_refuses_non_loopback_host(monkeypatch, runs, host):
    _use(monkeypatch, mcp_transport="streamable-http", mcp_host=host)
    with pytest.raises(SystemExit, match="loopback"):
        app.main()
    assert runs == []


def test_unknown_transport_is_refused(monkeypatch, runs):
    _use(monkeypatch, mcp_transport="sse")
    with pytest.raises(SystemExit):
        app.main()
    assert runs == []


INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "t", "version": "0"},
    },
}


@pytest.fixture(scope="module")
def http_server():
    """The real HTTP app (with HTTP_SECURITY) under uvicorn on 127.0.0.1."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    http_app = app.mcp.http_app(transport="streamable-http", **app.HTTP_SECURITY)
    server = uvicorn.Server(
        uvicorn.Config(http_app, host="127.0.0.1", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    yield port
    server.should_exit = True
    thread.join(5)


def _post(port: int, headers: dict[str, str]) -> int:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request(
        "POST",
        "/mcp",
        body=json.dumps(INIT),
        headers={
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
            **headers,
        },
    )
    status = conn.getresponse().status
    conn.close()
    return status


def test_local_request_is_served(http_server):
    assert _post(http_server, {}) == 200
    assert _post(http_server, {"origin": f"http://localhost:{http_server}"}) == 200


def test_rebinding_host_header_is_refused(http_server):
    # A page on evil.example rebinds its name to 127.0.0.1: the browser sends
    # Host: evil.example, which the guard refuses before any MCP handling.
    assert _post(http_server, {"host": "evil.example"}) == 421


def test_foreign_origin_is_refused(http_server):
    assert _post(http_server, {"origin": "https://evil.example"}) == 403
