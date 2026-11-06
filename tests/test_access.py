"""Sign-in for hosted HTTP (access.py): settings that would serve without it
are refused, the group gate, run ownership, the audit line, and the OIDC
proxy's endpoints against a local stand-in provider (no network)."""

from __future__ import annotations

import http.client
import http.server
import json
import logging
import socket
import threading
import time

import pytest
import uvicorn
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import RSAKeyPair

from tobi508 import access, app
from tobi508.config import Settings
from tobi508.resources import runs
from tobi508.runlog import RunRecorder

AUDIT = "tobi508.audit"
OIDC = dict(
    auth="oidc",
    mcp_transport="streamable-http",
    mcp_host="0.0.0.0",
    public_base_url="https://tobi.example.gov",
    oidc_config_url=(
        "https://sso.example.gov/realms/tobi/.well-known/openid-configuration"
    ),
    oidc_client_id="tobi",
    oidc_client_secret="s3cret-value",
    oidc_jwt_signing_key="a-long-stable-signing-key",
)


def _settings(**fields) -> Settings:
    return Settings(_env_file=None, **fields)


# ── Settings that must not serve ─────────────────────────────────────────────


def test_public_host_without_sign_in_is_refused():
    with pytest.raises(SystemExit, match="AUTH=oidc"):
        app.http_options(_settings(mcp_transport="streamable-http", mcp_host="::"))


@pytest.mark.parametrize("missing", ["public_base_url", "oidc_client_secret"])
def test_sign_in_with_missing_settings_is_refused(missing):
    s = _settings(**{**OIDC, missing: None})
    with pytest.raises(SystemExit, match=missing.upper()):
        app.http_options(s)


def test_sign_in_needs_https_urls():
    s = _settings(**{**OIDC, "public_base_url": "http://508-tobi.example.gov"})
    with pytest.raises(SystemExit, match="PUBLIC_BASE_URL must be an https"):
        app.http_options(s)


def test_sign_in_serves_publicly_with_audit_and_public_host(monkeypatch):
    built, added = [], []
    monkeypatch.setattr(access, "build_auth", lambda s: built.append(s) or "AUTH")
    monkeypatch.setattr(app.mcp, "auth", None)
    monkeypatch.setattr(app.mcp, "add_middleware", added.append)
    opts = app.http_options(_settings(**OIDC))
    assert app.mcp.auth == "AUTH" and len(built) == 1
    assert [type(m) for m in added] == [access.AuditMiddleware]
    assert opts["host"] == "0.0.0.0"
    assert opts["host_origin_protection"] is True
    assert opts["allowed_hosts"] == ["tobi.example.gov"]


def test_secrets_never_print():
    s = _settings(**OIDC)
    assert "s3cret-value" not in repr(s) and "signing-key" not in repr(s)


# ── Group gate ───────────────────────────────────────────────────────────────

KEYS = RSAKeyPair.generate()
ISSUER = "https://keycloak.example.gov/realms/tobi"


def _verifier(groups: list[str]) -> access.GroupGatedVerifier:
    return access.GroupGatedVerifier(
        required_groups=groups,
        group_claim="claim_groups",
        public_key=KEYS.public_key,
        issuer=ISSUER,
    )


def _token(**claims) -> str:
    return KEYS.create_token(subject="u1", issuer=ISSUER, additional_claims=claims)


async def test_group_gate_admits_a_listed_group():
    v = _verifier(["VAST--tobi--scan"])
    ok = await v.verify_token(_token(claim_groups=["other", "VAST--tobi--scan"]))
    assert ok is not None and ok.claims["sub"] == "u1"


async def test_group_gate_refuses_and_audits_others(caplog):
    v = _verifier(["VAST--tobi--scan"])
    with caplog.at_level(logging.INFO, logger="tobi508.audit"):
        assert await v.verify_token(_token(claim_groups=["VAST--x--scan"])) is None
        assert await v.verify_token(_token()) is None
    denied = [json.loads(r.message) for r in caplog.records if r.name == AUDIT]
    assert [d["action"] for d in denied] == ["authz.denied"] * 2
    assert denied[0]["sub"] == "u1"


async def test_no_required_groups_admits_any_valid_token():
    assert await _verifier([]).verify_token(_token()) is not None


async def test_group_gate_still_refuses_a_bad_signature():
    other = RSAKeyPair.generate().create_token(subject="u1", issuer=ISSUER)
    assert await _verifier([]).verify_token(other) is None


# ── Run ownership ────────────────────────────────────────────────────────────


@pytest.fixture
def as_caller(monkeypatch, settings):
    who = {"sub": None}
    monkeypatch.setattr(access, "caller", lambda: who["sub"])
    monkeypatch.setattr(runs.config, "settings", settings)

    def set_caller(sub):
        who["sub"] = sub

    return set_caller


def test_runs_belong_to_their_maker(as_caller, settings):
    as_caller("alice")
    run = RunRecorder(settings.runs_dir)
    run.write_json(run.report_path, {"ok": True})
    assert RunRecorder.open(settings.runs_dir, run.run_id).run_id == run.run_id
    assert runs.run_file(run.run_id, "report.json").is_file()

    as_caller("bob")  # same message as an expired run: the id reveals nothing
    with pytest.raises(FileNotFoundError, match="may have expired"):
        RunRecorder.open(settings.runs_dir, run.run_id)
    with pytest.raises(ValueError, match="may have expired"):
        runs.run_file(run.run_id, "report.json")


def test_without_sign_in_runs_are_open_and_unowned(as_caller, settings):
    run = RunRecorder(settings.runs_dir)
    assert not (run.dir / access.OWNER_FILE).exists()
    assert RunRecorder.open(settings.runs_dir, run.run_id)
    as_caller("alice")  # an unowned run is closed to signed-in callers
    with pytest.raises(FileNotFoundError):
        RunRecorder.open(settings.runs_dir, run.run_id)


# ── Audit line ───────────────────────────────────────────────────────────────


def test_audit_fields_keep_identifiers_only():
    fields = access._tool_fields(
        {
            "url": "https://www.nasa.gov/a?token=abc#x",
            "other_pages": ["https://www.nasa.gov/b?q=1"],
            "run_id": "20261106T120000Z-abcdef",
            "answers": [{"id": "q1", "answer": "pass", "note": "secret words"}],
        }
    )
    assert fields == {
        "url": "https://www.nasa.gov/a",
        "other_pages": ["https://www.nasa.gov/b"],
        "run_id": "20261106T120000Z-abcdef",
        "answers": 1,
    }


async def test_audit_middleware_logs_each_call(caplog):
    server = FastMCP("t")

    @server.tool
    def echo(url: str) -> str:
        return "ok"

    @server.tool
    def boom() -> str:
        raise ValueError("no")

    server.add_middleware(access.AuditMiddleware())
    from fastmcp import Client

    with caplog.at_level(logging.INFO, logger="tobi508.audit"):
        async with Client(server) as c:
            await c.call_tool("echo", {"url": "https://x.gov/p?q=1"})
            await c.call_tool("boom", {}, raise_on_error=False)
    lines = [json.loads(r.message) for r in caplog.records if r.name == AUDIT]
    assert [(e["tool"], e["outcome"]) for e in lines] == [
        ("echo", "ok"),
        ("boom", "error"),
    ]
    assert lines[0]["url"] == "https://x.gov/p" and lines[0]["sub"] is None


# ── The proxy's endpoints, against a local stand-in provider ─────────────────


class _Provider(http.server.BaseHTTPRequestHandler):
    base = ""

    def do_GET(self):  # noqa: N802
        b = self.base
        doc = {
            "issuer": b,
            "authorization_endpoint": b + "/auth",
            "token_endpoint": b + "/token",
            "jwks_uri": b + "/certs",
            "response_types_supported": ["code"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
        }
        body = json.dumps(doc if "openid" in self.path else {"keys": []}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def signed_in_server():
    """The real app with GatedOIDCProxy, provider and server on 127.0.0.1."""
    provider = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Provider)
    _Provider.base = f"http://127.0.0.1:{provider.server_address[1]}"
    threading.Thread(target=provider.serve_forever, daemon=True).start()
    port = _free_port()
    auth = access.GatedOIDCProxy(
        required_groups=[],
        group_claim="claim_groups",
        config_url=_Provider.base + "/.well-known/openid-configuration",
        client_id="tobi",
        client_secret="s3cret-value",
        base_url=f"http://127.0.0.1:{port}",
        jwt_signing_key="a-long-stable-signing-key",
        allowed_client_redirect_uris=["http://localhost:*"],
    )
    server_app = FastMCP("t", auth=auth).http_app(
        transport="streamable-http", **app.HTTP_SECURITY
    )
    server = uvicorn.Server(
        uvicorn.Config(server_app, host="127.0.0.1", port=port, log_level="error")
    )
    threading.Thread(target=server.run, daemon=True).start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    yield port
    server.should_exit = True
    provider.shutdown()


def _request(port, method, path, body=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request(method, path, body=body, headers=headers or {})
    resp = conn.getresponse()
    out = (resp.status, dict(resp.getheaders()), resp.read())
    conn.close()
    return out


def test_mcp_without_a_token_is_refused_with_the_metadata_link(signed_in_server):
    status, headers, _ = _request(
        signed_in_server,
        "POST",
        "/mcp",
        body="{}",
        headers={
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
        },
    )
    assert status == 401
    challenge = {k.lower(): v for k, v in headers.items()}["www-authenticate"]
    assert "resource_metadata=" in challenge


def test_mcp_with_a_forged_token_is_refused(signed_in_server):
    status, _, _ = _request(
        signed_in_server,
        "POST",
        "/mcp",
        body="{}",
        headers={
            "authorization": "Bearer " + _token(),
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
        },
    )
    assert status == 401


def test_sign_in_metadata_points_clients_to_this_server(signed_in_server):
    status, _, body = _request(
        signed_in_server, "GET", "/.well-known/oauth-protected-resource/mcp"
    )
    assert status == 200
    meta = json.loads(body)
    assert meta["authorization_servers"] == [f"http://127.0.0.1:{signed_in_server}/"]
    status, _, body = _request(
        signed_in_server, "GET", "/.well-known/oauth-authorization-server"
    )
    assert status == 200
    assert "registration_endpoint" in json.loads(body)
