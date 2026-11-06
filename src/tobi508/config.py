"""Server configuration loaded from environment variables or a .env file.

Every field can be overridden by an environment variable of the same name,
prefixed with nothing (e.g. `HEADLESS=true`, `DEV_MODE=true`). Copy
`.env.example` to `.env` in the repository root for local development; it is
read from there whatever the working directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
# The server's own .env, wherever the client launches it from. Never the
# working directory's: an MCP client may start the server in another project,
# whose .env could change ALLOWED_DOMAINS or DEV_MODE.
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    """MCP server settings. Override any field via environment variables."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Transport ─────────────────────────────────────────────────────────────
    mcp_transport: str = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000

    # ── Sign-in (HTTP only) ───────────────────────────────────────────────────
    # "none": HTTP listens on loopback only. "oidc": every MCP request needs a
    # token from the OIDC provider (VAST's Keycloak app realm), through
    # FastMCP's OIDC proxy; only then may MCP_HOST be a public interface.
    # docs/plans/2026-11-06-hosted-auth.md.
    auth: Literal["none", "oidc"] = "none"
    # This server's public URL (https), e.g. https://508-tobi.vast.ndc.nasa.gov.
    # Keycloak's redirect URI is {PUBLIC_BASE_URL}/auth/callback, and only
    # this host passes the Host check.
    public_base_url: str | None = None
    # .../realms/<realm>/.well-known/openid-configuration
    oidc_config_url: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: SecretStr | None = None
    # Expected `aud` of upstream access tokens (Keycloak needs an audience
    # mapper for this); unset skips the audience check.
    oidc_audience: str | None = None
    # Signs the tokens this server gives MCP clients, and encrypts its stored
    # client registrations. Keep it stable, or every client signs in again.
    oidc_jwt_signing_key: SecretStr | None = None
    # Where MCP clients may ask to be sent back after sign-in. Claude Code
    # uses a localhost port; add e.g. a web client's callback here.
    oidc_client_redirect_uris: list[str] = Field(
        default_factory=lambda: ["http://localhost:*", "http://127.0.0.1:*"]
    )
    # Optional gate: a caller needs one of these values in the token claim
    # `group_claim` (VAMS groups such as VAST--<client>--<slug>, or NAMS
    # groups). Empty: any signed-in NASA user who passes NAMS.
    required_groups: list[str] = Field(default_factory=list)
    group_claim: str = "claim_groups"

    # ── Navigation policy ─────────────────────────────────────────────────────
    # Entries starting with "." match that suffix (".gov" matches "www.nasa.gov"
    # and "nasa.gov"). Other entries match a hostname exactly. Enforced on every
    # top-level navigation, including each redirect hop.
    allowed_domains: list[str] = Field(default_factory=lambda: [".gov", ".mil"])
    # file:// is allowed only when dev_mode is on (for local fixtures).
    dev_mode: bool = False
    max_redirects: int = Field(default=10, ge=0, le=50)
    # Every browser connection goes through egress.EgressProxy, which refuses
    # any host that resolves to a private, loopback, link-local, multicast,
    # reserved or cloud-metadata address, and any port not listed here.
    egress_ports: list[int] = Field(default_factory=lambda: [80, 443])
    # Dev mode only (ignored otherwise): addresses (CIDRs) the proxy lets
    # through, at any port, for the local fixture server. Exact match: an
    # IPv4-mapped form of a listed address is still refused.
    dev_allowed_addresses: list[str] = Field(default_factory=list)
    # Where a host's direct connections are re-signed by a gateway that
    # browsers do not trust (a cloud container: its HTTPS_PROXY), the proxy
    # checks each address as usual, then tunnels by name through this
    # http:// proxy, which resolves the name again (weaker against DNS
    # rebinding than connecting to the checked address). Off by default.
    upstream_proxy: str | None = None

    # ── Browser ───────────────────────────────────────────────────────────────
    # "chrome" = installed Google Chrome. "chromium" = Playwright's bundled build
    # (used in CI/containers where Chrome is not installed).
    browser_channel: str = "chrome"
    headless: bool = False
    # Extra Chromium flags. Empty for real runs; tests serve cross-origin
    # fixtures from two loopback hosts and turn off Local Network Access checks,
    # which block intercepted loopback requests (they never apply to public hosts).
    browser_args: list[str] = Field(default_factory=list)
    viewport_width: int = 1280
    viewport_height: int = 900
    navigation_timeout_ms: int = 30_000

    # ── Evidence ──────────────────────────────────────────────────────────────
    # The Tab press cap is not a setting: it comes from the 4.C spec
    # (3 x DOM inventory + 50, max 3,000; see traverse.tab_press_cap).
    # 4.C spec run limits; every report records them (Versions.run_settings).
    # settle_quiet_ms: the settle rule's DOM-quiet window after each key press.
    settle_quiet_ms: int = Field(default=150, ge=50, le=1000)
    record_scroll_passes: int = Field(default=1, ge=0, le=50)
    # The media store (2.A-2.D plan Q9): media saved in full while recording
    # so its byte ranges replay. None lifts the cap (a run with
    # no_time_limit, the user's choice when a file was over it).
    media_cap_mb: float | None = Field(default=50, gt=0)
    media_cap_s: float | None = Field(default=15, gt=0)
    # Wall clock for one run. Tests not finished in time are NEEDS_REVIEW
    # with the reason. 600 s since long polling (Abby, 2026-11-05): a call
    # no longer waits for the whole run (call_wait_s), so the limit no
    # longer has to fit client and proxy timeouts; it was 120 s, and the
    # time limit was the largest loss left after the post-round 1 fixes.
    run_limit_s: int = Field(default=600, ge=10)
    # Seconds the run limit grows by for each other page of the same site the
    # caller names (9.A-9.C: recording it and reading it; Abby, 2026-11-02).
    other_page_s: int = Field(default=20, ge=5)
    # Extra time for a page with content that keeps changing by itself (a
    # ticker, a carousel), added once pass T finds it (Abby, 2026-11-04, T1
    # (a)): every key press waits longer there, and 2.A-2.C probe it.
    moving_allowance_s: int = Field(default=45, ge=0, le=300)
    # How long one tool call waits for its run before it returns the job id
    # and progress (post-round 1 fixes 2 and 5, option C): under the common
    # 60 s MCP client timeout. The run goes on; tobi_run_status waits again.
    call_wait_s: int = Field(default=45, ge=1, le=600)
    # Browser runs one server does at once. A run waiting for a slot does not
    # use its own time limit (round1-answers: 12 at once overloaded 4 CPUs).
    max_concurrent_runs: int = Field(default=2, ge=1, le=32)
    # Finished jobs kept in memory for tobi_run_status (the run folder is kept
    # for run_ttl_hours either way).
    job_keep_s: int = Field(default=86400, ge=60)
    # An other page's recording, and its reads, reused for this long within
    # one server session (pagecache.py); 0 turns the cache off.
    page_cache_s: int = Field(default=1800, ge=0)
    runs_dir: Path = REPO_ROOT / "runs"
    # Runs are working files, not an archive: deleted after this many hours.
    # Durable results belong in the user's codebase (saved from tool output).
    run_ttl_hours: float = Field(default=24, gt=0)

    # ── Frozen pages (evals only) ─────────────────────────────────────────────
    # A folder of recordings made once (evals/agent/freeze.py). When set, the
    # server replays a URL's recording instead of loading it live: the tested
    # page, other pages and 19.A's site search. "replay" refuses a URL with no
    # recording (a tool error, nothing fetched live); "tested_frozen" (the
    # agent eval) requires a recording of the tested page, and records other
    # pages of the same host live as usual (other pages, 19.A's search);
    # "record_missing" records a URL live and adds it (the freeze step). A
    # server setting, never a tool input: neither the caller nor page content
    # chooses a recording.
    frozen_pages_dir: Path | None = None
    frozen_pages_mode: Literal["replay", "tested_frozen", "record_missing"] = "replay"

    # ── Vendored tools ────────────────────────────────────────────────────────
    third_party_dir: Path = REPO_ROOT / "third_party"

    # ── Rules specs ───────────────────────────────────────────────────────────
    # One spec per TT test. Each spec's version comes from its own front matter
    # (spec_version) and is recorded in every report; it is not configurable.
    rules_dir: Path = REPO_ROOT / "docs" / "rules"

    # ── Versions recorded in every report ─────────────────────────────────────
    # "client": open questions go to the calling agent (tobi_answer_questions).
    # "api" (NASA hosted model) joins this choice when ApiJudge is built, so an
    # unbuilt backend fails at startup, not after a run.
    judge_backend: Literal["client"] = "client"
    # Identifier of the model that answers open questions, if any.
    judging_model: str = "none"


settings = Settings()
