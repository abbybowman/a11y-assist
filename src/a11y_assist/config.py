"""Server configuration loaded from environment variables or a .env file.

Every field can be overridden by an environment variable of the same name,
prefixed with nothing (e.g. `HEADLESS=true`, `DEV_MODE=true`). Copy
`.env.example` to `.env` in the repository root for local development; it is
read from there whatever the working directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
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
    # Wall clock for one a11y_run_tt_tests call: short enough for HTTP proxies when
    # hosted. Tests not finished in time are NEEDS_REVIEW with the reason.
    run_limit_s: int = Field(default=120, ge=10)
    # Seconds the run limit grows by for each other page of the same site the
    # caller names (9.A-9.C: recording it and reading it; Abby, 2026-11-02).
    other_page_s: int = Field(default=20, ge=5)
    runs_dir: Path = REPO_ROOT / "runs"
    # Runs are working files, not an archive: deleted after this many hours.
    # Durable results belong in the user's codebase (saved from tool output).
    run_ttl_hours: float = Field(default=24, gt=0)

    # ── Vendored tools ────────────────────────────────────────────────────────
    third_party_dir: Path = REPO_ROOT / "third_party"

    # ── Rules specs ───────────────────────────────────────────────────────────
    # One spec per TT test. Each spec's version comes from its own front matter
    # (spec_version) and is recorded in every report; it is not configurable.
    rules_dir: Path = REPO_ROOT / "docs" / "rules"

    # ── Versions recorded in every report ─────────────────────────────────────
    # "client": open questions go to the calling agent (a11y_answer_questions).
    # "api" (NASA hosted model) joins this choice when ApiJudge is built, so an
    # unbuilt backend fails at startup, not after a run.
    judge_backend: Literal["client"] = "client"
    # Identifier of the model that answers open questions, if any.
    judging_model: str = "none"


settings = Settings()
