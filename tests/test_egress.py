"""Outbound address checks (GSA template: "Outbound SSRF Prevention").

Every browser connection goes through egress.EgressProxy. These tests use a
fake resolver to point .gov names at private addresses, and a sentinel
server on 127.0.0.2 (loopback, but not on the dev allowlist): any request
that reaches it is a bypass. Nothing here uses the network.
"""

from __future__ import annotations

import asyncio
import http.server
import ipaddress
import json
import threading
from collections import Counter

import pytest
from fastmcp import Client

from a11y_assist import config, egress
from a11y_assist.app import mcp
from a11y_assist.egress import EgressProxy, address_problem

# ── The address rules (pure) ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "address, problem",
    [
        ("10.1.2.3", "private"),
        ("172.16.0.1", "private"),
        ("192.168.0.1", "private"),
        ("127.0.0.1", "loopback"),
        ("127.255.255.254", "loopback"),
        ("169.254.169.254", "cloud metadata"),
        ("169.254.1.1", "link-local"),
        ("100.100.100.200", "cloud metadata"),
        ("168.63.129.16", "cloud metadata"),
        ("fd00:ec2::254", "cloud metadata"),
        ("100.64.0.1", "non-public"),  # carrier-grade NAT
        ("0.0.0.0", "unspecified"),
        ("224.0.0.1", "multicast"),
        ("240.0.0.1", "reserved"),
        ("255.255.255.255", "reserved"),
        ("192.0.2.1", "private"),  # documentation range
        ("198.18.0.1", "private"),  # benchmarking range
        ("::", "unspecified"),
        ("::1", "loopback"),
        ("fe80::1", "link-local"),
        ("fc00::1", "private"),
        ("ff02::1", "multicast"),
        ("ff0e::1", "multicast"),  # Python calls this global
        ("::ffff:127.0.0.1", "IPv4-mapped"),
        ("::ffff:8.8.8.8", "IPv4-mapped"),  # never from public DNS: refuse all
        ("::127.0.0.1", "IPv4-compatible"),  # Python calls this global
        ("2002:a00:1::1", "6to4"),  # embeds 10.0.0.1
        ("2001::1", "Teredo"),
        ("64:ff9b::a00:1", "reserved"),  # NAT64 of 10.0.0.1
        ("2001:db8::1", "private"),
    ],
)
def test_non_public_addresses_are_refused(address, problem):
    found = address_problem(ipaddress.ip_address(address))
    assert found is not None and problem in found, found


@pytest.mark.parametrize("address", ["8.8.8.8", "152.216.7.110", "2606:4700::1111"])
def test_public_addresses_pass(address):
    assert address_problem(ipaddress.ip_address(address)) is None


# ── Servers: fixture on 127.0.0.1:P, sentinel on 127.0.0.2:P ─────────────────


class _Handler(http.server.BaseHTTPRequestHandler):
    hits: Counter
    pages: dict[str, str]

    def log_message(self, *args) -> None:
        pass

    def do_GET(self) -> None:
        self.hits[self.path] += 1
        port = self.server.server_address[1]
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", f"http://inside.gov:{port}/landed")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = self.pages.get(self.path, "<!doctype html><title>x</title><p>x")
        data = body.replace("{port}", str(port)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)


PAGES = {
    "/frames.html": (
        "<!doctype html><html lang=en><title>frames</title><button>Go</button>"
        "<iframe title=f src='http://inside.gov:{port}/frame.html'></iframe>"
        "<img alt='' src='http://meta.gov:{port}/x.png'>"
        "<script src='http://inside.gov:{port}/s.js'></script>"
    ),
    "/rebind.html": (
        "<!doctype html><html lang=en><title>rebind</title><button>Go</button>"
        "<script>setTimeout(() => fetch('/later.json').catch(() => {}), 200)"
        "</script>"
    ),
}


def _serve(host: str, port: int):
    handler = type("H", (_Handler,), {"hits": Counter(), "pages": PAGES})
    httpd = http.server.ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, handler.hits


@pytest.fixture
def servers():
    """(port, fixture hits, sentinel hits) on the same port number."""
    fixture, hits = _serve("127.0.0.1", 0)
    port = fixture.server_address[1]
    sentinel, sentinel_hits = _serve("127.0.0.2", port)
    yield port, hits, sentinel_hits
    for s in (fixture, sentinel):
        s.shutdown()
        s.server_close()


class FakeDNS:
    """A resolver with fixed answers; a list of answers is used in turn (the
    last repeats), to model a name whose answer changes mid-run."""

    def __init__(self, answers: dict[str, list[list[str]]]):
        self.answers = answers
        self.calls: Counter = Counter()

    async def __call__(self, host: str, port: int) -> list[str]:
        if host not in self.answers:
            raise OSError("NXDOMAIN")
        seq = self.answers[host]
        i = min(self.calls[host], len(seq) - 1)
        self.calls[host] += 1
        return seq[i]


@pytest.fixture
def gov_settings(settings, monkeypatch):
    s = settings.model_copy(update={"allowed_domains": [".gov"]})
    monkeypatch.setattr(config, "settings", s)
    return s


def _dns(monkeypatch, answers):
    dns = FakeDNS(answers)
    monkeypatch.setattr(egress, "RESOLVER", dns)
    return dns


async def _run(url: str):
    async with Client(mcp) as client:
        return await client.call_tool(
            "a11y_run_tt_tests", {"url": url, "tests": ["4.C"]}, raise_on_error=False
        )


def _steps(settings) -> str:
    if not settings.runs_dir.exists():
        return ""
    return "".join(p.read_text("utf-8") for p in settings.runs_dir.rglob("*.jsonl"))


# ── A .gov name pointing inside ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "answer, reason",
    [
        ("10.0.0.7", "private"),
        ("127.0.0.2", "loopback"),
        ("169.254.169.254", "cloud metadata"),
        # 127.0.0.1 is on the test's dev allowlist, but its mapped form is not.
        ("::ffff:127.0.0.1", "IPv4-mapped"),
    ],
)
async def test_gov_name_resolving_inside_is_never_tested(
    gov_settings, servers, monkeypatch, answer, reason
):
    port, hits, sentinel = servers
    _dns(monkeypatch, {"inside.gov": [[answer]]})
    result = await _run(f"http://inside.gov:{port}/page.html")
    assert result.is_error
    msg = result.content[0].text
    assert "inside.gov" in msg and reason in msg
    assert not hits and not sentinel  # nothing reached either server
    assert not gov_settings.runs_dir.exists() or not any(
        gov_settings.runs_dir.iterdir()
    )


async def test_any_bad_answer_refuses_the_name(gov_settings, servers, monkeypatch):
    port, hits, _ = servers
    _dns(monkeypatch, {"mixed.gov": [["127.0.0.1", "10.0.0.1"]]})
    result = await _run(f"http://mixed.gov:{port}/page.html")
    assert result.is_error and "private" in result.content[0].text
    assert not hits


async def test_allowed_name_is_tested(gov_settings, servers, monkeypatch):
    port, hits, sentinel = servers
    _dns(monkeypatch, {"good.gov": [["127.0.0.1"]]})
    result = await _run(f"http://good.gov:{port}/page.html")
    assert not result.is_error, result.content[0].text
    assert hits["/page.html"] >= 1 and not sentinel


# ── Redirects, iframes and subresources ──────────────────────────────────────


async def test_redirect_to_a_private_address_is_refused(
    gov_settings, servers, monkeypatch
):
    # inside.gov passes the hostname allowlist; only its address is wrong.
    port, hits, sentinel = servers
    _dns(monkeypatch, {"good.gov": [["127.0.0.1"]], "inside.gov": [["127.0.0.2"]]})
    result = await _run(f"http://good.gov:{port}/redirect")
    assert result.is_error
    msg = result.content[0].text
    assert "inside.gov" in msg and "loopback" in msg
    assert hits["/redirect"] == 1 and not sentinel


async def test_iframe_and_subresources_pointing_inside_are_refused(
    gov_settings, servers, monkeypatch
):
    port, hits, sentinel = servers
    _dns(
        monkeypatch,
        {
            "good.gov": [["127.0.0.1"]],
            "inside.gov": [["127.0.0.2"]],
            "meta.gov": [["169.254.169.254"]],
        },
    )
    result = await _run(f"http://good.gov:{port}/frames.html")
    assert not result.is_error, result.content[0].text
    out = json.loads(result.content[0].text)
    [note] = [e for e in out["errors"] if "non-public" in e]
    assert f"inside.gov:{port} (resolves to a loopback address)" in note
    assert f"meta.gov:{port} (resolves to a cloud metadata address)" in note
    assert hits["/frames.html"] >= 1
    assert not sentinel  # the iframe and script never reached 127.0.0.2
    assert '"step":"egress_refused"' in _steps(gov_settings)


# ── DNS rebinding ─────────────────────────────────────────────────────────────


async def test_rebinding_mid_run_is_refused(gov_settings, servers, monkeypatch):
    # flip.gov answers 127.0.0.1 for the page, then 127.0.0.2 for everything
    # after. The page's later fetch needs a new connection (the server closes
    # each one), which is checked again and refused.
    port, hits, sentinel = servers
    dns = _dns(monkeypatch, {"flip.gov": [["127.0.0.1"], ["127.0.0.2"]]})
    result = await _run(f"http://flip.gov:{port}/rebind.html")
    assert not result.is_error, result.content[0].text
    assert hits["/rebind.html"] >= 1
    assert dns.calls["flip.gov"] >= 2
    assert not sentinel  # never connected to the rebound address
    assert "flip.gov" in json.dumps(json.loads(result.content[0].text)["errors"])


async def _connect_via(proxy: EgressProxy, target: str) -> bytes:
    reader, writer = await asyncio.open_connection(*proxy.url[7:].split(":"))
    writer.write(f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\n\r\n".encode())
    await writer.drain()
    status = await reader.readline()
    if b" 200 " in status:
        await reader.readline()  # the blank line ending the proxy's reply
        writer.write(b"GET /probe HTTP/1.0\r\nHost: x\r\n\r\n")
        await writer.drain()
        await reader.read()
    writer.close()
    return status


async def test_the_check_is_bound_to_the_connection(settings, servers):
    # A resolver that answers well once, then badly. If the proxy checked one
    # answer and then connected by name (a second lookup), the first CONNECT
    # would land on the sentinel.
    port, hits, sentinel = servers
    dns = FakeDNS({"flip.gov": [["127.0.0.1"], ["127.0.0.2"]]})
    async with EgressProxy(settings, resolver=dns) as proxy:
        first = await _connect_via(proxy, f"flip.gov:{port}")
        second = await _connect_via(proxy, f"flip.gov:{port}")
    assert b" 200 " in first and b" 403 " in second
    assert dns.calls["flip.gov"] == 2  # one lookup per connection
    assert hits["/probe"] == 1 and not sentinel
    assert proxy.connected == [
        {"host": "flip.gov", "port": port, "address": "127.0.0.1"}
    ]


@pytest.mark.parametrize(
    "target",
    [
        "127.0.0.2",
        "2130706434",  # 127.0.0.2 as one integer
        "0x7f.0.0.2",  # hex
        "0177.0.0.2",  # octal
        "127.2",  # short form
        "[::ffff:127.0.0.2]",
        "[::ffff:7f00:2]",
        "[::ffff:127.0.0.1]",  # mapped form of an allowlisted address
    ],
)
async def test_alternate_address_forms_are_refused(settings, servers, target):
    # The real system resolver: glibc turns these forms into 127.0.0.2.
    port, hits, sentinel = servers
    async with EgressProxy(settings, resolver=egress.system_resolver) as proxy:
        status = await _connect_via(proxy, f"{target}:{port}")
    assert b" 403 " in status
    assert not sentinel and not hits


async def test_dev_allowlist_is_ignored_outside_dev_mode(settings, servers):
    port, hits, _ = servers
    prod = settings.model_copy(update={"dev_mode": False})
    async with EgressProxy(prod, resolver=egress.system_resolver) as proxy:
        status = await _connect_via(proxy, f"127.0.0.1:{port}")
    assert b" 403 " in status and not hits


async def test_unlisted_port_is_refused(settings):
    dns = FakeDNS({"pub.gov": [["8.8.8.8"]]})
    async with EgressProxy(settings, resolver=dns) as proxy:
        status = await _connect_via(proxy, "pub.gov:25")
    assert b" 403 " in status
    assert proxy.refused[-1]["reason"] == "port 25 is not allowed"


async def test_unresolvable_name_fails_closed(settings):
    dns = FakeDNS({})
    async with EgressProxy(settings, resolver=dns) as proxy:
        status = await _connect_via(proxy, "nowhere.gov:443")
    assert b" 403 " in status
