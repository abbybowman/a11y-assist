"""A whole sign-in through GatedOIDCProxy against a local stand-in for
Keycloak (no network): an MCP client registers, signs in, swaps its code for
a token and calls tools. Checks that the person who signed in is the caller
the tools see (run ownership and the audit line depend on it), and that a
second person cannot open the first person's run."""

from __future__ import annotations

import base64
import hashlib
import http.client
import http.server
import json
import secrets
import socket
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
import uvicorn
from fastmcp import Client, FastMCP
from fastmcp.server.auth.providers.jwt import RSAKeyPair
from joserfc import jwk

from a11y_assist import access
from a11y_assist.runlog import RunRecorder

KEYS = RSAKeyPair.generate()
CLIENT_CB = "http://localhost:9/cb"  # never contacted: the test reads the redirect


class _Keycloak(http.server.BaseHTTPRequestHandler):
    """Discovery, JWKS, an /auth that signs in whoever `login_as` names, and
    a /token that issues an RS256 access token for them."""

    base = ""
    login_as = "alice"
    groups = ["VAST--tobi--scan"]

    def _json(self, doc):
        body = json.dumps(doc).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        b, path = self.base, urlsplit(self.path)
        if path.path.endswith("openid-configuration"):
            return self._json(
                {
                    "issuer": b,
                    "authorization_endpoint": b + "/auth",
                    "token_endpoint": b + "/token",
                    "jwks_uri": b + "/certs",
                    "response_types_supported": ["code"],
                    "subject_types_supported": ["public"],
                    "id_token_signing_alg_values_supported": ["RS256"],
                }
            )
        if path.path == "/certs":
            key = jwk.RSAKey.import_key(KEYS.public_key).as_dict()
            return self._json({"keys": [{**key, "kid": "k1", "use": "sig"}]})
        if path.path == "/auth":  # the person signs in at Launchpad
            q = parse_qs(path.query)
            back = (
                q["redirect_uri"][0]
                + "?"
                + urlencode(
                    {"code": "up-" + _Keycloak.login_as, "state": q["state"][0]}
                )
            )
            self.send_response(302)
            self.send_header("location", back)
            self.end_headers()
            return None
        self.send_response(404)
        self.end_headers()

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("content-length", 0))
        form = parse_qs(self.rfile.read(length).decode())
        who = form["code"][0].removeprefix("up-")
        token = KEYS.create_token(
            subject=who,
            issuer=self.base,
            kid="k1",
            scopes=["openid"],
            additional_claims={
                "claim_groups": _Keycloak.groups,
                "nasaPrimaryEmail": f"{who}@nasa.gov",
            },
        )
        self._json({"access_token": token, "token_type": "Bearer", "expires_in": 300})

    def log_message(self, *a):
        pass


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    runs_dir: Path = tmp_path_factory.mktemp("runs")
    kc = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Keycloak)
    _Keycloak.base = f"http://127.0.0.1:{kc.server_address[1]}"
    threading.Thread(target=kc.serve_forever, daemon=True).start()
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    auth = access.GatedOIDCProxy(
        required_groups=["VAST--tobi--scan"],
        group_claim="claim_groups",
        config_url=_Keycloak.base + "/.well-known/openid-configuration",
        client_id="tobi",
        client_secret="s3cret-value",
        base_url=base,
        jwt_signing_key="a-long-stable-signing-key",
        allowed_client_redirect_uris=["http://localhost:*"],
        require_authorization_consent=False,  # the consent page is FastMCP's
    )
    mcp = FastMCP("t", auth=auth)

    @mcp.tool
    def whoami() -> str | None:  # sync: runs in a worker thread
        return access.caller()

    @mcp.tool
    async def new_run() -> str:
        return RunRecorder(runs_dir).run_id

    @mcp.tool
    def open_run(run_id: str) -> bool:
        try:
            RunRecorder.open(runs_dir, run_id)
        except FileNotFoundError:
            return False
        return True

    mcp.add_middleware(access.AuditMiddleware())
    app = mcp.http_app(transport="streamable-http", host_origin_protection=True)
    srv = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    )
    threading.Thread(target=srv.run, daemon=True).start()
    deadline = time.monotonic() + 10
    while not srv.started and time.monotonic() < deadline:
        time.sleep(0.05)
    yield base
    srv.should_exit = True
    kc.shutdown()


class _Http:
    """Just enough of an HTTP client: no redirects followed, JSON or form."""

    def request(self, method, url, params=None, json_body=None, form=None):
        u = urlsplit(url)
        path = u.path + ("?" + urlencode(params) if params else "")
        if u.query:
            path += ("&" if params else "?") + u.query
        headers, body = {}, None
        if json_body is not None:
            body, headers["content-type"] = json.dumps(json_body), "application/json"
        if form is not None:
            body = urlencode(form)
            headers["content-type"] = "application/x-www-form-urlencoded"
        conn = http.client.HTTPConnection(u.hostname, u.port, timeout=10)
        conn.request(method, path, body=body, headers=headers)
        r = conn.getresponse()
        r.text = r.read().decode()
        r.status_code = r.status
        r.location = r.getheader("location") or ""
        conn.close()
        return r


def _sign_in(base: str, who: str) -> str:
    """The MCP authorization flow a client such as Claude Code runs."""
    _Keycloak.login_as = who
    h = _Http()
    reg = h.request(
        "POST",
        base + "/register",
        json_body={
            "redirect_uris": [CLIENT_CB],
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "client_name": "test",
        },
    )
    assert reg.status_code == 201, reg.text
    client_id = json.loads(reg.text)["client_id"]
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    r = h.request(
        "GET",
        base + "/authorize",
        params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": CLIENT_CB,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "s1",
            "resource": base + "/mcp",
        },
    )
    while not r.location.startswith(CLIENT_CB):
        assert r.status_code in (302, 303, 307), r.text
        r = h.request("GET", r.location)  # Keycloak, then /auth/callback
    back = parse_qs(urlsplit(r.location).query)
    assert back["state"] == ["s1"]
    tok = h.request(
        "POST",
        base + "/token",
        form={
            "grant_type": "authorization_code",
            "code": back["code"][0],
            "client_id": client_id,
            "redirect_uri": CLIENT_CB,
            "code_verifier": verifier,
        },
    )
    assert tok.status_code == 200, tok.text
    return json.loads(tok.text)["access_token"]


async def _call(base, token, tool, args=None):
    async with Client(base + "/mcp", auth=token) as c:
        return (await c.call_tool(tool, args or {})).data


async def test_the_signed_in_person_is_the_caller(server, caplog):
    import logging

    token = _sign_in(server, "alice")
    with caplog.at_level(logging.INFO, logger="a11y_assist.audit"):
        assert await _call(server, token, "whoami") == "alice"
    [line] = [
        json.loads(r.message) for r in caplog.records if r.name == "a11y_assist.audit"
    ]
    assert line["sub"] == "alice" and line["who"] == "alice@nasa.gov"


async def test_a_run_is_private_to_its_maker(server):
    alice, bob = _sign_in(server, "alice"), _sign_in(server, "bob")
    run_id = await _call(server, alice, "new_run")
    assert await _call(server, alice, "open_run", {"run_id": run_id}) is True
    assert await _call(server, bob, "open_run", {"run_id": run_id}) is False


async def test_a_person_outside_the_groups_cannot_call(server, monkeypatch):
    monkeypatch.setattr(_Keycloak, "groups", ["VAST--other--scan"])
    token = _sign_in(server, "carol")  # Keycloak signs carol in; the gate refuses
    u = urlsplit(server)
    conn = http.client.HTTPConnection(u.hostname, u.port, timeout=10)
    conn.request(
        "POST",
        "/mcp",
        body="{}",
        headers={
            "authorization": "Bearer " + token,
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
        },
    )
    assert conn.getresponse().status == 401
    conn.close()
