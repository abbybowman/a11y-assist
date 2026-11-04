"""The Claude Code CLI route (docs/plans/2026-10-31-agent-eval.md section
7.1): each arm runs as its own `claude -p` process, isolated from this
repository, its memory and the account's profile, with only its arm's MCP
servers. The CLI runs the agent loop itself; this module starts it, reads
its stream-json output, and writes the same step log and totals the API
route writes.

Isolation (plan section 7.2): an empty working folder and an empty HOME, no
settings, skills, slash commands or session files, and the session's
identifying variables unset. A leak check with the arm's servers attached
runs first, and the run stops if it finds anything.

Timing comes from the stream: a model call runs from its message_start to
its message_stop; a tool call from the assistant message that asked for it
to the arrival of its result.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evals.agent import prompt as task_prompt
from evals.agent.arms import Server

# Variables a cloud session sets that would tell the model who the user is,
# which repo it is in, or load this project's instructions (checked
# 2026-11-03, plan section 7.2).
DROP = (
    "CLAUDE_CODE_USER_EMAIL",
    "CLAUDE_ADDITIONAL_DIRECTORIES",
    "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD",
    "CLAUDE_CODE_REMOTE",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_ACCOUNT_UUID",
    "CLAUDE_CODE_ORGANIZATION_UUID",
    "CLAUDE_CODE_SYNC_SKILLS",
    "CLAUDE_CODE_SYNC_PLUGINS",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_REMOTE_SESSION_ID",
    "CLAUDECODE",
)
# Tools every arm gets besides its MCP servers: a helper (one level deep)
# and an MCP resource reader. Agent B also gets web search and WebFetch, as a
# capable agent would look up guidance, but WebFetch is refused on the
# tested site's hosts (Abby, 2026-11-04): the tested pages come only from
# the frozen copies.
MCP_TOOL_TIMEOUT_MS = 3_600_000  # one hour per tool call
COMMON_TOOLS = ["Agent", "ListMcpResourcesTool", "ReadMcpResourceTool"]
ARM_TOOLS = {"a": COMMON_TOOLS, "b": [*COMMON_TOOLS, "WebSearch", "WebFetch"]}


def fetch_denials(hosts: list[str]) -> list[str]:
    """WebFetch rules for the tested hosts, with and without www."""
    out: set[str] = set()
    for h in hosts:
        h = h.lower().rstrip(".")
        out |= {h, h.removeprefix("www."), "www." + h.removeprefix("www.")}
    return [f"WebFetch(domain:{h})" for h in sorted(out) if h]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ClaudeCodeCLI:
    route = "claude-code-cli"

    def __init__(self, model: str = "claude-sonnet-5-5", binary: str = "claude"):
        self.model = model
        self.binary = shutil.which(binary) or binary

    # ── process ───────────────────────────────────────────────────────────
    def _env(self, home: Path) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in DROP}
        env["HOME"] = str(home)
        env["CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"] = "1"
        # The CLI cuts an MCP tool call off at 60 s by default; a run of the
        # tool with other pages takes minutes (round 1's first attempt, 2026-11-04).
        env["MCP_TOOL_TIMEOUT"] = str(MCP_TOOL_TIMEOUT_MS)
        return env

    def _args(
        self, prompt: str, mcp: Path, tools: list[str], servers, hosts=()
    ) -> list[str]:
        allowed = [f"mcp__{s.name}" for s in servers] + tools
        denied = [f"mcp__{s.name}__{t}" for s in servers for t in s.deny]
        if "WebFetch" in tools:
            denied += fetch_denials(list(hosts))
        return [
            self.binary,
            "-p",
            prompt,
            "--model",
            self.model,
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--setting-sources",
            "",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--mcp-config",
            str(mcp),
            "--tools",
            ",".join(tools),
            "--allowedTools",
            ",".join(allowed),
            *(["--disallowedTools", ",".join(denied)] if denied else []),
            "--no-session-persistence",
            "--system-prompt",
            task_prompt.SYSTEM,
        ]

    async def _stream(self, prompt, servers, tools, on_event, hosts=()) -> int:
        """Run one isolated `claude -p` and call on_event(event, t) per line."""
        with tempfile.TemporaryDirectory(prefix="arm-") as tmp:
            tmp = Path(tmp)
            (tmp / "home").mkdir()
            (tmp / "work").mkdir()
            mcp = tmp / "mcp.json"
            mcp.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            s.name: {"command": s.command, "args": s.args, "env": s.env}
                            for s in servers
                        }
                    }
                )
            )
            proc = await asyncio.create_subprocess_exec(
                *self._args(prompt, mcp, tools, servers, hosts),
                cwd=tmp / "work",
                env=self._env(tmp / "home"),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=64 * 1024 * 1024,
            )
            async for raw in proc.stdout:
                t = time.monotonic()
                try:
                    ev = json.loads(raw)
                except ValueError:
                    continue
                if on_event(ev, t) is False:
                    proc.kill()
                    break
            err = (await proc.stderr.read()).decode("utf-8", "replace")
            code = await proc.wait()
            if code not in (0, -9) and err.strip():
                self.stderr = err[-2000:]
            return code

    # ── leak check ────────────────────────────────────────────────────────
    async def leak_check(self, servers: list[Server], question: str) -> dict:
        """The question with the arm's servers attached and no tools."""
        state: dict[str, Any] = {"text": "", "usage": {}, "model": "", "init": {}}

        def on(ev, t):
            if ev.get("type") == "system" and ev.get("subtype") == "init":
                state["init"] = {
                    k: ev.get(k) for k in ("tools", "mcp_servers", "skills")
                }
            if ev.get("type") == "result":
                state["text"] = ev.get("result") or ""
                state["usage"] = ev.get("modelUsage") or {}
                state["model"] = ",".join(state["usage"])

        await self._stream(question, servers, [], on)
        return state

    # ── a whole arm ───────────────────────────────────────────────────────
    async def run(
        self, task: str, servers: list[Server], arm: str, log, hosts: list[str] = ()
    ) -> dict:
        calls: dict[str, dict] = {}  # api message id -> model call
        uses: dict[str, dict] = {}  # tool_use id -> tool call
        out: dict[str, Any] = {
            "final": "",
            "ended": "no result",
            "tool_calls": {},
            "rate_limits": [],
            "transcript": [],
        }
        failed_servers: list = []

        def depth(ev) -> int:
            return 0 if not ev.get("parent_tool_use_id") else 1

        def on(ev, t):
            kind = ev.get("type")
            if kind == "stream_event":
                se, mid = ev.get("event") or {}, ev.get("api_message_id")
                if se.get("type") == "message_start":
                    m = se.get("message") or {}
                    calls[m.get("id") or mid] = {
                        "start": _now(),
                        "t0": t,
                        "depth": depth(ev),
                        "model": m.get("model"),
                        "usage": dict(m.get("usage") or {}),
                        "text": "",
                        "tool_uses": [],
                    }
                elif se.get("type") == "message_delta" and mid in calls:
                    calls[mid]["usage"].update(se.get("usage") or {})
                    calls[mid]["stop_reason"] = (se.get("delta") or {}).get(
                        "stop_reason"
                    )
                elif se.get("type") == "message_stop" and mid in calls:
                    calls[mid]["seconds"] = round(t - calls[mid]["t0"], 3)
                return True  # deltas stay out of the transcript
            out["transcript"].append(ev)
            if kind == "system" and ev.get("subtype") == "init":
                out["init"] = {
                    k: ev.get(k)
                    for k in ("tools", "mcp_servers", "model", "agents", "skills")
                }
                failed_servers.extend(
                    s
                    for s in ev.get("mcp_servers") or []
                    if s.get("status") != "connected"
                )
                if failed_servers:
                    return False
            elif kind == "assistant":
                msg = ev.get("message") or {}
                c = calls.get(msg.get("id"))
                for b in msg.get("content") or []:
                    if b.get("type") == "text" and c is not None:
                        c["text"] += b.get("text", "")
                    elif b.get("type") == "tool_use":
                        uses[b["id"]] = {
                            "name": b.get("name"),
                            "args": b.get("input"),
                            "start": _now(),
                            "t0": t,
                            "depth": depth(ev),
                        }
                        if c is not None:
                            c["tool_uses"].append(b.get("name"))
            elif kind == "user":
                for b in (ev.get("message") or {}).get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        u = uses.get(b.get("tool_use_id"))
                        if u is None:
                            continue
                        content = b.get("content")
                        text = (
                            content
                            if isinstance(content, str)
                            else json.dumps(content, default=str)
                        )
                        u["seconds"] = round(t - u["t0"], 3)
                        u["is_error"] = bool(b.get("is_error"))
                        u["result_chars"] = len(text)
                        # Enough to see an error or a refusal (untrusted text).
                        u["result_preview"] = text[:500]
                        out["tool_calls"][u["name"]] = (
                            out["tool_calls"].get(u["name"], 0) + 1
                        )
                        log.add(
                            type="tool",
                            **{k: v for k, v in u.items() if k != "t0"},
                        )
            elif kind == "rate_limit_event":
                info = ev.get("rate_limit_info") or {}
                out["rate_limits"].append(info)
                log.add(type="rate_limit", info=info)
            elif kind == "result":
                out["final"] = ev.get("result") or ""
                out["ended"] = (
                    ev.get("terminal_reason") or ev.get("subtype") or "result"
                )
                out["is_error"] = bool(ev.get("is_error"))
                out["model_usage"] = ev.get("modelUsage") or {}
                out["cli_usage"] = ev.get("usage") or {}
                out["cli_duration_ms"] = ev.get("duration_ms")
                out["num_turns"] = ev.get("num_turns")
                out["cost_usd_list_price"] = ev.get("total_cost_usd")
            return True

        out["exit_code"] = await self._stream(task, servers, ARM_TOOLS[arm], on, hosts)
        if failed_servers:
            out["ended"] = "error: MCP server not connected"
            out["error"] = f"MCP servers not connected: {failed_servers}"
        for mid, c in calls.items():
            log.add(
                type="model",
                id=mid,
                depth=c["depth"],
                start=c["start"],
                seconds=c.get("seconds"),
                model=c["model"],
                stop_reason=c.get("stop_reason"),
                usage={k: v for k, v in c["usage"].items() if isinstance(v, int)},
                text=c["text"],
                tool_uses=c["tool_uses"],
            )
        out["model_calls"] = len(calls)
        out["models"] = sorted({c["model"] for c in calls.values() if c["model"]})
        totals: dict[str, int] = {}
        for c in calls.values():
            for k, v in c["usage"].items():
                if isinstance(v, int):
                    totals[k] = totals.get(k, 0) + v
        out["tokens"] = totals
        if getattr(self, "stderr", None):
            out["stderr"] = self.stderr
        return out
