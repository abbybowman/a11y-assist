# Hosted sign-in (VAST)

**Goal.** Serve the MCP server over HTTP from VAST (NASA's prototype
cluster, `508-tobi.vast.ndc.nasa.gov` requested in VAMS) so that only
signed-in NASA users can run it, each sees only their own runs, and every
call is audited. GSA requires a hosted server; the loopback-only rule stays
for HTTP without sign-in.

## What VAST gives every prototype

From VAST's documentation and its app boilerplate (`py_auth_boilerplate`):

- An app-level Keycloak realm brokered to the `vast` realm, then to NASA
  Launchpad; NAMS access (AM 34763) is enforced at that layer. The realm is
  provisioned by VAST, not by the app.
- A **confidential** OIDC client, Authorization Code flow, redirect URI
  `{BASE_URL}/auth/callback`, scopes `openid email profile`, Launchpad claim
  names (`employeeNumber`, `nasaPrimaryEmail`, `AgencyUID`, `displayName`,
  groups).
- Roles from one token claim (default `claim_groups`) compared as opaque
  strings against VAMS (`VAST--<client>--<slug>`) or NAMS (`ND-GG-*`)
  groups.
- An audit trail consolidated across the platform; PostgreSQL as the only
  backing service today (persistent volumes are on VAST's roadmap).

The boilerplate signs browsers in with a server-side session cookie. MCP
clients send a bearer token on every request instead (MCP authorization
spec), so its session code is not reused; its realm and client are.

## Design

- **FastMCP's OIDC proxy** (`fastmcp.server.auth.oidc_proxy.OIDCProxy`,
  FastMCP 4.0.11). To MCP clients it is a standard MCP authorization server
  with dynamic client registration; upstream it uses one confidential
  Keycloak client. Its callback path is `/auth/callback`, the redirect URI
  VAST's realm already expects, so the standard VAST client works without
  Keycloak's own dynamic registration (FastMCP's `KeycloakAuthProvider`
  needs that and Keycloak 26.6 or later). Clients are sent back only to
  `OIDC_CLIENT_REDIRECT_URIS` (default: localhost ports, as Claude Code
  uses).
- **Settings** (`config.py`): `AUTH=oidc`, `PUBLIC_BASE_URL`,
  `OIDC_CONFIG_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`,
  `OIDC_JWT_SIGNING_KEY`; optional `OIDC_AUDIENCE`, `REQUIRED_GROUPS`,
  `GROUP_CLAIM`. Missing or non-https values stop the server at start.
  Secrets are `SecretStr`.
- **Transport** (`app.http_options`): without sign-in, loopback only, as
  before. With it, the proxy and the audit middleware are installed, the
  public host joins the Host check, and `MCP_HOST` may be `0.0.0.0` behind
  VAST's HTTPS.
- **Group gate** (`access.GroupGatedVerifier`): with `REQUIRED_GROUPS`, the
  upstream token needs one listed value in `GROUP_CLAIM`; otherwise it is
  refused as invalid and an `authz.denied` line is audited.
- **Run ownership** (`access.claim_run`, `access.may_open`): a new run
  records its maker's `sub`; `RunRecorder.open` and `run_file` (every path
  to a run: answers, `run://`, read_report, explain) treat another person's
  run as expired. Without sign-in nothing changes.
- **Audit** (`access.AuditMiddleware`): one JSON line per tool call,
  resource read and prompt, on the `a11y_assist.audit` logger (stderr):
  `sub`, a name claim, action, tool, URL without query, run ID, test IDs,
  answer count, outcome, seconds. Never answers, page text or report
  content.

## Clients

Claude's custom connectors (claude.ai, Claude Desktop) connect from
Anthropic's cloud and need a server reachable from the public internet
(Anthropic, "Getting started with custom connectors", 2026-11-06), so they
cannot reach VAST unless NASA admits Anthropic's IP ranges. Claude Code runs
on the user's machine and connects from there:
`claude mcp add --transport http a11y-assist https://508-tobi.vast.ndc.nasa.gov/mcp`.
NASA-internal tools (Ask Sage, ChatGSFC) take only MCP servers their admins
add; whether they support remote HTTP and per-user OAuth is for their
admins.

## Verified and not

- Verified (`tests/test_access.py`, local stand-in provider): refused
  settings; the group gate on RS256 tokens; run ownership; audit fields;
  the audit middleware on real tool calls; 401 with the metadata link on
  `/mcp` without a token or with a token not issued by this server; the
  protected-resource and authorization-server metadata.
- Verified (`tests/test_access_signin.py`, a stand-in Keycloak with
  discovery, JWKS, /auth and /token): the whole MCP authorization flow
  (register, authorize with PKCE, upstream sign-in, callback, token); the
  tools see the person who signed in (also in a sync tool's worker thread)
  and the audit line names them; a second person's run reads as missing;
  a person outside REQUIRED_GROUPS gets 401 after signing in. The consent
  page is off in that test; it stays on in the server.
- Not verified: a sign-in with VAST's Keycloak and a real client;
  whether VAST's access tokens carry `sub` and `claim_groups` (the gate and
  ownership need them; FastMCP's `verify_id_token` option is the fallback
  if only the ID token has them); the audience Keycloak puts in tokens.

## Open questions for the VAST admin

1. Is there a persistent volume (the boilerplate's `/data`)? Runs and the
   proxy's client registrations (`FASTMCP_HOME`) should survive restarts.
2. Can the build pipeline pull `ghcr.io/abbybowman/a11y-assist`, so the
   Containerfile is one `FROM` line (no apt under FIPS)?
3. Is a service that drives Chromium acceptable in the namespace (4 CPU,
   16 GB was the dev container)?
4. Can the app's access tokens include `sub` and the groups claim, and an
   audience mapper for this server?
5. Can Anthropic's outbound IP ranges reach the app, for Claude Desktop
   custom connectors? If not, Claude Code is the demo client.

## Next

Deploy on VAST once the prototype exists, sign in from Claude Code, run one
page, confirm the audit lines and that a second user cannot open the run;
then remove the [PENDING] in the evaluation document and deck.
