"""Connection-time address checks for every browser connection.

The allowlist (policy.py) matches hostnames by suffix (*.gov, *.mil), which
this tool needs, but a name says nothing about where it points: an agency's
internal host, a cloud metadata service or 127.0.0.1 can all sit behind a
.gov name. So Chrome is launched with this proxy as its only route out
(browser.launch_browser requires one). The page, iframes, subresources,
WebSockets, every redirect hop and the navigation guard's own route.fetch all
connect through it.

For each connection the proxy:
  1. resolves the host once (all IPv4 and IPv6 answers),
  2. refuses it if ANY answer is not a public unicast address (see
     `address_problem`), or the port is not allowed,
  3. connects to an address it just checked, never to the name, so a second
     DNS answer (rebinding) is never used.

TLS stays end to end (CONNECT tunnel): Chrome still verifies the certificate
and SNI for the real hostname. If the proxy is down, Chrome has no direct
route, so nothing gets through (fail closed). Ambiguous input (unparseable
request, failed resolution, scoped IPv6) is refused.

Dev mode only: `dev_allowed_addresses` (CIDRs) lets the local fixture server
through, by exact address match. Alternate forms of an allowed address (an
IPv4-mapped IPv6 address, for example) are never exempt.

Not covered here (defense in depth belongs to the deployment): network-level
egress rules for the host running the server.
"""

from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

from a11y_assist.config import Settings

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
Resolver = Callable[[str, int], Awaitable[list[str]]]
LogFn = Callable[..., None]

MAX_HEAD = 64 * 1024
HEAD_TIMEOUT_S = 30
CONNECT_TIMEOUT_S = 10

# Cloud metadata and host-agent endpoints. Most are already non-public by
# range; 168.63.129.16 (Azure) is in public space, so it is listed by name.
METADATA = {
    ipaddress.ip_address(a)
    for a in (
        "169.254.169.254",  # AWS, GCP, Azure, OCI, DigitalOcean
        "169.254.170.2",  # AWS ECS task metadata
        "169.254.169.123",  # AWS time sync
        "100.100.100.200",  # Alibaba Cloud
        "168.63.129.16",  # Azure WireServer
        "fd00:ec2::254",  # AWS IPv6 metadata
    )
}


def address_problem(ip: IPAddress) -> str | None:
    """Why `ip` may not be connected to, or None for a public unicast address."""
    if ip in METADATA:
        return "cloud metadata address"
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.scope_id:
            return "scoped IPv6 address"
        if ip.ipv4_mapped is not None:
            return "IPv4-mapped IPv6 address"
        if ip.teredo is not None:
            return "Teredo IPv6 address"
        if ip.sixtofour is not None:
            inner = address_problem(ip.sixtofour)
            if inner:
                return f"6to4 address embedding a {inner}"
        if int(ip) >> 32 == 0 and int(ip) > 1:
            return "IPv4-compatible IPv6 address"
    if ip.is_unspecified:
        return "unspecified address"
    if ip.is_loopback:
        return "loopback address"
    if ip.is_link_local:
        return "link-local address"
    if ip.is_multicast:
        return "multicast address"
    if ip.is_reserved:
        return "reserved address"
    if ip.is_private:
        return "private address"
    if not ip.is_global:
        return "non-public address"
    return None


async def system_resolver(host: str, port: int) -> list[str]:
    """Every address the system resolver returns (IPv4 and IPv6). glibc also
    turns alternate IPv4 forms ("2130706433", "0x7f.1") into dotted quads."""
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return list(dict.fromkeys(info[4][0] for info in infos))


# Swappable for tests (tests/conftest.py keeps them offline).
RESOLVER: Resolver = system_resolver


class Refused(Exception):
    """A connection the proxy will not make."""


@dataclass
class EgressProxy:
    """A local HTTP proxy (CONNECT and absolute-form requests) that checks the
    address of every connection it makes. Use as an async context manager."""

    settings: Settings
    log: LogFn | None = None
    resolver: Resolver | None = None
    refused: list[dict[str, Any]] = field(default_factory=list)
    connected: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._server: asyncio.base_events.Server | None = None
        self._tasks: set[asyncio.Task] = set()
        self._allow = (
            [ipaddress.ip_network(n) for n in self.settings.dev_allowed_addresses]
            if self.settings.dev_mode
            else []
        )
        self.url = ""

    async def __aenter__(self) -> EgressProxy:
        self._server = await asyncio.start_server(self._serve, "127.0.0.1", 0)
        port = self._server.sockets[0].getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        return self

    async def __aexit__(self, *exc) -> None:
        if self._server is not None:
            self._server.close()
        for t in list(self._tasks):
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        if self._server is not None:
            with contextlib.suppress(Exception):
                await self._server.wait_closed()

    def _emit(self, step: str, status: str, **detail: Any) -> None:
        if self.log is not None:
            self.log(step, status, **detail)

    # ── The check ────────────────────────────────────────────────────────────

    def _exempt(self, ip: IPAddress) -> bool:
        return any(ip.version == n.version and ip in n for n in self._allow)

    async def check(self, host: str, port: int) -> list[str]:
        """Resolve once and return the addresses to connect to, or raise
        Refused. Every answer must pass, not just the one used."""
        try:
            answers = await (self.resolver or RESOLVER)(host, port)
        except Exception:
            raise Refused("name did not resolve") from None
        if not answers:
            raise Refused("name did not resolve")
        for a in answers:
            try:
                ip = ipaddress.ip_address(a)
            except ValueError:
                raise Refused("resolver returned an unparseable address") from None
            if self._exempt(ip):
                continue
            problem = address_problem(ip)
            if problem:
                raise Refused(f"resolves to a {problem}")
            if port not in self.settings.egress_ports:
                raise Refused(f"port {port} is not allowed")
        return answers

    async def _open(self, host: str, port: int):
        try:
            addresses = await self.check(host, port)
        except Refused as exc:
            self.refused.append(
                {"host": host, "port": port, "reason": str(exc), "policy": True}
            )
            self._emit(
                "egress_refused", "blocked", host=host, port=port, reason=str(exc)
            )
            raise
        last: Exception | None = None
        for a in addresses:
            try:
                conn = await asyncio.wait_for(
                    asyncio.open_connection(a, port), CONNECT_TIMEOUT_S
                )
            except Exception as exc:  # try the next checked address
                last = exc
                continue
            self.connected.append({"host": host, "port": port, "address": a})
            return conn
        # Not a policy refusal, but recorded so a caller can tell an
        # unreachable host from a real response (a CONNECT 403 looks the same).
        reason = f"could not connect ({type(last).__name__})"
        self.refused.append(
            {"host": host, "port": port, "reason": reason, "policy": False}
        )
        raise Refused(reason)

    # ── HTTP proxy plumbing ──────────────────────────────────────────────────

    async def _serve(self, reader, writer) -> None:
        task = asyncio.current_task()
        if task is not None:  # cancelled on close
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        upstream = None
        try:
            head = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), HEAD_TIMEOUT_S)
            if len(head) > MAX_HEAD:
                return
            line, *headers = head.decode("latin-1").split("\r\n")
            method, target, version = line.split(" ", 2)
            if method == "CONNECT":
                host, port = _split_authority(target)
                try:
                    up_reader, upstream = await self._open(host, port)
                except Refused:
                    writer.write(
                        b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n"
                        b"Connection: close\r\n\r\n"
                    )
                    await writer.drain()
                    return
                writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await writer.drain()
            else:
                parts = urlsplit(target)
                if parts.scheme != "http" or not parts.hostname:
                    return  # refuse anything but absolute-form http://
                port = parts.port or 80
                try:
                    up_reader, upstream = await self._open(parts.hostname, port)
                except Refused:
                    # No response at all: a 403 body would render as the page.
                    return
                path = parts.path or "/"
                if parts.query:
                    path += "?" + parts.query
                kept = [
                    h
                    for h in headers
                    if h
                    and h.split(":", 1)[0].strip().lower()
                    not in ("proxy-connection", "proxy-authorization", "connection")
                ]
                upstream.write(
                    (
                        f"{method} {path} {version}\r\n"
                        + "".join(h + "\r\n" for h in kept)
                        + "Connection: close\r\n\r\n"
                    ).encode("latin-1")
                )
                await upstream.drain()
            await _pipe_both(reader, writer, up_reader, upstream)
        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError, ValueError):
            return  # malformed or oversized request: refuse by closing
        except (ConnectionError, asyncio.TimeoutError, OSError):
            return
        finally:
            for w in (upstream, writer):
                if w is not None:
                    with contextlib.suppress(Exception):
                        w.close()


def _split_authority(target: str) -> tuple[str, int]:
    """'host:port' or '[v6]:port' from a CONNECT line."""
    parts = urlsplit("//" + target)
    if not parts.hostname or parts.port is None:
        raise ValueError("bad CONNECT target")
    return parts.hostname, parts.port


async def _pipe(reader, writer) -> None:
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    finally:
        with contextlib.suppress(Exception):
            writer.write_eof()


async def _pipe_both(r1, w1, r2, w2) -> None:
    """Copy both ways; when one side ends, give the other a moment, then stop."""
    tasks = [asyncio.create_task(_pipe(r1, w2)), asyncio.create_task(_pipe(r2, w1))]
    try:
        _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        if pending:
            await asyncio.wait(pending, timeout=1)
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
