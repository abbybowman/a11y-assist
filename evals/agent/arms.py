"""The MCP servers each arm gets (docs/plans/2026-10-31-agent-eval.md
section 2): Agent A this server, Agent B Playwright MCP. Both replay the
round's frozen pages only, headless."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NODE = REPO / "evals" / "agent" / "node"
PLAYWRIGHT_MCP = NODE / "node_modules" / ".bin" / "playwright-mcp"
INIT_PAGE = NODE / "frozen-init.cjs"


@dataclass
class Server:
    name: str
    command: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)


def _base_env() -> dict[str, str]:
    keep = ("PATH", "HOME", "LANG", "TMPDIR", "SSL_CERT_FILE")
    return {k: os.environ[k] for k in keep if k in os.environ}


def tool_arm(frozen: Path, model: str, runs_dir: Path) -> list[Server]:
    """Agent A: this server, replaying `frozen` only."""
    env = _base_env() | {
        "BROWSER_CHANNEL": "chromium",
        "HEADLESS": "true",
        "FROZEN_PAGES_DIR": str(frozen),
        "FROZEN_PAGES_MODE": "replay",
        "JUDGING_MODEL": model,  # Agent A answers the open questions
        "RUNS_DIR": str(runs_dir),
        "RUN_TTL_HOURS": "720",  # kept until the round is locked
    }
    return [Server("a11y", sys.executable, ["-m", "a11y_assist.app"], env)]


def browser_arm(frozen: Path, out_dir: Path, executable: str) -> list[Server]:
    """Agent B: Playwright MCP, pinned in evals/agent/node/package.json.
    `executable` is Playwright's full Chromium (the same build Agent A's
    server uses). No sandbox, as Playwright's own default; no WebMCP, so a
    tested page cannot register tools (page content is untrusted)."""
    args = [
        "--headless",
        "--isolated",
        "--no-sandbox",
        "--no-webmcp",
        "--executable-path",
        executable,
        "--init-page",
        str(INIT_PAGE),
        "--output-dir",
        str(out_dir),
    ]
    env = _base_env() | {"A11Y_FROZEN_DIR": str(frozen)}
    return [Server("browser", str(PLAYWRIGHT_MCP), args, env)]
