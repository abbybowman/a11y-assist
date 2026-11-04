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
    # Tools of this server the arm never gets (removed before the model sees
    # the list, on both routes).
    deny: list[str] = field(default_factory=list)


def _base_env() -> dict[str, str]:
    # What a browser and Python need to start, on Linux, macOS and Windows;
    # nothing that describes the user or this session.
    keep = (
        "PATH",
        "HOME",
        "LANG",
        "TMPDIR",
        "TEMP",
        "TMP",
        "SSL_CERT_FILE",
        "PLAYWRIGHT_BROWSERS_PATH",
        "SYSTEMROOT",
        "WINDIR",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
    )
    return {k: os.environ[k] for k in keep if k in os.environ}


def tool_arm(frozen: Path, model: str, runs_dir: Path) -> list[Server]:
    """Agent A: this server, replaying `frozen` only."""
    env = _base_env() | {
        "BROWSER_CHANNEL": "chromium",
        "HEADLESS": "true",
        "FROZEN_PAGES_DIR": str(frozen),
        # The tested pages only from the frozen copies; other pages of the
        # tested site, and 19.A's search, live as usual (Abby, 2026-11-04).
        "FROZEN_PAGES_MODE": "tested_frozen",
        "JUDGING_MODEL": model,  # Agent A answers the open questions
        "RUNS_DIR": str(runs_dir),
        "RUN_TTL_HOURS": "720",  # kept until the round is locked
    }
    return [Server("a11y", sys.executable, ["-m", "a11y_assist.app"], env)]


def browser_arm(
    frozen: Path,
    out_dir: Path,
    executable: str,
    proxy: str | None = None,
    live_log: Path | None = None,
) -> list[Server]:
    """Agent B: Playwright MCP, pinned in evals/agent/node/package.json.
    `executable` is Playwright's full Chromium (the same build Agent A's
    server uses). No sandbox, as Playwright's own default; no WebMCP, so a
    tested page cannot register tools (page content is untrusted). Files
    are confined to the workspace (Playwright MCP's default)."""
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
        *(["--proxy-server", proxy] if proxy else []),
    ]
    env = _base_env() | {"A11Y_FROZEN_DIR": str(frozen)}
    if live_log is not None:
        live_log.parent.mkdir(parents=True, exist_ok=True)
        env["A11Y_LIVE_LOG"] = str(live_log)
    # browser_run_code_unsafe runs any code in Playwright's own process: it
    # could open a context the frozen replay does not cover (the live site)
    # or read files on this machine.
    return [
        Server(
            "browser", str(PLAYWRIGHT_MCP), args, env, deny=["browser_run_code_unsafe"]
        )
    ]
