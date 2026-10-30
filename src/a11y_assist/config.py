"""Server configuration loaded from environment variables or a .env file.

Every field can be overridden by an environment variable of the same name,
prefixed with nothing (e.g. `HEADLESS=true`, `DEV_MODE=true`). Copy
`.env.example` to `.env` for local development.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """MCP server settings. Override any field via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
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

    # ── Browser ───────────────────────────────────────────────────────────────
    # "chrome" = installed Google Chrome. "chromium" = Playwright's bundled build
    # (used in CI/containers where Chrome is not installed).
    browser_channel: str = "chrome"
    headless: bool = False
    viewport_width: int = 1280
    viewport_height: int = 900
    navigation_timeout_ms: int = 30_000

    # ── Evidence ──────────────────────────────────────────────────────────────
    max_tab_presses: int = Field(default=150, ge=1, le=2000)
    runs_dir: Path = REPO_ROOT / "runs"

    # ── Vendored tools ────────────────────────────────────────────────────────
    third_party_dir: Path = REPO_ROOT / "third_party"

    # ── Rules specs ───────────────────────────────────────────────────────────
    # One spec per TT test. Each spec's version comes from its own front matter
    # (spec_version) and is recorded in every report; it is not configurable.
    rules_dir: Path = REPO_ROOT / "docs" / "rules"

    # ── Versions recorded in every report ─────────────────────────────────────
    # "client": questions go to the calling agent (submit_judgments).
    # "api": NASA hosted model (not implemented yet).
    judge_backend: str = "client"
    # Identifier of the model that answers judgment questions, if any.
    judging_model: str = "none"


settings = Settings()
