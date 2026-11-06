"""Who is calling, and what they may reach (hosted HTTP only).

With AUTH=oidc, FastMCP's OIDC proxy signs MCP clients in through the OIDC
provider (VAST's Keycloak app realm, brokered to NASA Launchpad with NAMS
enforced) and checks a token on every MCP request. This module adds three
things on top (docs/plans/2026-11-06-hosted-auth.md):

  * an optional group gate on the upstream token (REQUIRED_GROUPS),
  * run ownership: a run made by one person is invisible to another,
  * an audit line per tool call, resource read and prompt.

With AUTH=none (stdio, or HTTP on loopback) there is no caller: runs have no
owner and nothing is audited, as before.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from fastmcp.server.auth import TokenVerifier
from fastmcp.server.auth.oidc_proxy import OIDCProxy
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware

from tobi508.config import Settings
from tobi508.redact import safe_url

AUDIT = logging.getLogger("tobi508.audit")
OWNER_FILE = "owner"
# Claims that name a person, in the order used for the audit line. Launchpad's
# claim names (VAST) first, then standard OIDC.
NAME_CLAIMS = ("nasaPrimaryEmail", "email", "preferred_username", "AgencyUID")


# ── The caller ────────────────────────────────────────────────────────────────


def caller() -> str | None:
    """The signed-in caller's stable subject (`sub`), or None without
    sign-in (stdio, loopback HTTP, or outside a request)."""
    try:
        token = get_access_token()
    except RuntimeError:
        return None
    if token is None:
        return None
    sub = (token.claims or {}).get("sub")
    return str(sub) if sub else None


def _caller_fields() -> dict[str, Any]:
    try:
        token = get_access_token()
    except RuntimeError:
        token = None
    claims = (token.claims if token else None) or {}
    who = next((str(claims[c]) for c in NAME_CLAIMS if claims.get(c)), None)
    return {"sub": claims.get("sub"), "who": who}


# ── Run ownership ─────────────────────────────────────────────────────────────


def claim_run(run_dir: Path) -> None:
    """Record the caller as the run's owner (nothing without sign-in)."""
    sub = caller()
    if sub:
        (run_dir / OWNER_FILE).write_text(sub, encoding="utf-8")


def may_open(run_dir: Path) -> bool:
    """Whether the caller may read or change this run. Without sign-in every
    run is open (a local server has one user). With sign-in, only the run's
    owner: a run with no owner was made without sign-in and stays closed."""
    sub = caller()
    if sub is None:
        return True
    try:
        return (run_dir / OWNER_FILE).read_text(encoding="utf-8") == sub
    except OSError:
        return False


# ── Sign-in provider ──────────────────────────────────────────────────────────


class GroupGatedVerifier(JWTVerifier):
    """A JWT verifier that also needs one of `required_groups` in the token's
    `group_claim` (compared as opaque strings, as VAST's boilerplate does).
    A token without one is refused like an invalid token, and audited."""

    def __init__(self, *, required_groups: list[str], group_claim: str, **kw: Any):
        super().__init__(**kw)
        self.required_groups = frozenset(required_groups)
        self.group_claim = group_claim

    async def verify_token(self, token: str):
        result = await super().verify_token(token)
        if result is None or not self.required_groups:
            return result
        if self.required_groups & groups_in(result.claims, self.group_claim):
            return result
        audit("authz.denied", sub=(result.claims or {}).get("sub"))
        return None


def groups_in(claims: dict[str, Any] | None, claim: str) -> frozenset[str]:
    value = (claims or {}).get(claim)
    if isinstance(value, str):
        return frozenset([value])
    if isinstance(value, list):
        return frozenset(str(v) for v in value)
    return frozenset()


class GatedOIDCProxy(OIDCProxy):
    """FastMCP's OIDC proxy with the group gate on its upstream verifier."""

    def __init__(self, *, required_groups: list[str], group_claim: str, **kw: Any):
        # Set before super().__init__, which calls get_token_verifier.
        self._required_groups = required_groups
        self._group_claim = group_claim
        super().__init__(**kw)

    def get_token_verifier(
        self, *, algorithm=None, audience=None, required_scopes=None, **_: Any
    ) -> TokenVerifier:
        return GroupGatedVerifier(
            required_groups=self._required_groups,
            group_claim=self._group_claim,
            jwks_uri=str(self.oidc_config.jwks_uri),
            issuer=str(self.oidc_config.issuer),
            algorithm=algorithm,
            audience=audience,
            required_scopes=required_scopes,
        )


def auth_problems(s: Settings) -> list[str]:
    """What AUTH=oidc is missing; empty when it can start."""
    missing = [
        name.upper()
        for name in (
            "public_base_url",
            "oidc_config_url",
            "oidc_client_id",
            "oidc_client_secret",
            "oidc_jwt_signing_key",
        )
        if not getattr(s, name)
    ]
    problems = [f"{', '.join(missing)} must be set"] if missing else []
    for name in ("public_base_url", "oidc_config_url"):
        value = getattr(s, name)
        if value and not value.startswith("https://"):
            problems.append(f"{name.upper()} must be an https:// URL")
    return problems


def build_auth(s: Settings) -> GatedOIDCProxy:
    """The sign-in provider for AUTH=oidc. Fetches the provider's discovery
    document, so it runs at startup, never at import."""
    if problems := auth_problems(s):
        raise SystemExit("AUTH=oidc: " + "; ".join(problems) + ".")
    return GatedOIDCProxy(
        required_groups=s.required_groups,
        group_claim=s.group_claim,
        config_url=s.oidc_config_url,
        client_id=s.oidc_client_id,
        client_secret=s.oidc_client_secret.get_secret_value(),
        audience=s.oidc_audience,
        base_url=s.public_base_url,
        jwt_signing_key=s.oidc_jwt_signing_key.get_secret_value(),
        allowed_client_redirect_uris=s.oidc_client_redirect_uris,
    )


# ── Audit ─────────────────────────────────────────────────────────────────────


def audit(action: str, **fields: Any) -> None:
    """One JSON line on the audit logger (stderr in a container, where the
    platform collects it). Callers pass identifiers, never page content."""
    entry = {"ts": round(time.time(), 3), "action": action, **_caller_fields()}
    entry.update({k: v for k, v in fields.items() if v is not None})
    AUDIT.info(json.dumps(entry, default=str))


def _tool_fields(args: dict[str, Any] | None) -> dict[str, Any]:
    """The identifying arguments of a tool call: URLs without their query
    strings, run ids, test ids. Never answers or report contents."""
    args = args or {}
    fields: dict[str, Any] = {}
    if isinstance(args.get("url"), str):
        fields["url"] = safe_url(args["url"])
    if isinstance(args.get("other_pages"), list):
        fields["other_pages"] = [
            safe_url(u) for u in args["other_pages"] if isinstance(u, str)
        ]
    if isinstance(args.get("run_id"), str):
        fields["run_id"] = args["run_id"][:64]
    if isinstance(args.get("tests"), list):
        fields["tests"] = [str(t)[:8] for t in args["tests"]][:40]
    if isinstance(args.get("answers"), list):
        fields["answers"] = len(args["answers"])
    return fields


class AuditMiddleware(Middleware):
    """An audit line for every tool call, resource read and prompt, with
    who, what and whether it worked."""

    async def _logged(self, action: str, fields: dict[str, Any], call):
        t0 = time.monotonic()
        try:
            result = await call()
        except Exception as exc:
            audit(action, outcome="error", error=type(exc).__name__, **fields)
            raise
        took = round(time.monotonic() - t0, 2)
        audit(action, outcome="ok", seconds=took, **fields)
        return result

    async def on_call_tool(self, context, call_next):
        m = context.message
        fields = {"tool": m.name, **_tool_fields(m.arguments)}
        return await self._logged("tool.call", fields, lambda: call_next(context))

    async def on_read_resource(self, context, call_next):
        uri = str(context.message.uri)
        fields = {"uri": uri.split("?", 1)[0][:200]}
        return await self._logged("resource.read", fields, lambda: call_next(context))

    async def on_get_prompt(self, context, call_next):
        m = context.message
        fields = {"prompt": m.name, **_tool_fields(m.arguments)}
        return await self._logged("prompt.get", fields, lambda: call_next(context))
