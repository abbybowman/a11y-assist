"""Run one arm of the agent eval on a frozen round (docs/plans/
2026-10-31-agent-eval.md sections 2, 5 and 7).

    uv run python -m evals.agent.run --arm a evals/judging/<round>
    uv run python -m evals.agent.run --arm b evals/judging/<round>

One conversation covers every page of the round. The arm sees only the task
prompt (prompt.py) and its tools: its MCP servers (arms.py), a tool to read
MCP resources (as MCP clients such as Claude Code offer), and a helper tool,
the same for both arms. Output goes to <round>/results/arm-<a|b>/:

    steps.jsonl    every model call and tool call: times, tokens, text
    transcript.json  the whole conversation, helpers' included
    final.md       the arm's final message, in full
    summary.json   totals, models (requested and reported), route, commit
    runs/          Agent A only: the tool's run folders (reports, pre-SCRT)
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import time
from contextlib import AsyncExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evals.agent import prompt as task_prompt
from evals.agent.arms import Server, browser_arm, tool_arm
from evals.agent.cli import ClaudeCodeCLI
from evals.agent.providers import ContextExceeded, Provider, Reply

REPO = Path(__file__).resolve().parents[2]
MAX_TOKENS = 16_000
MAX_TURNS = 400  # model calls per conversation, helpers' counted separately
HELPER_TURNS = 150

READ_RESOURCE = {
    "name": "read_mcp_resource",
    "description": "Read a resource that a tool result links to (for example "
    "a run:// URI), and return its contents.",
    "input_schema": {
        "type": "object",
        "properties": {"uri": {"type": "string", "description": "The URI."}},
        "required": ["uri"],
    },
}
HELPER = {
    "name": "ask_helper",
    "description": "Hand a self-contained task to a helper agent that has the "
    "same tools as you (except this one) and none of this conversation. "
    "Returns the helper's final reply.",
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "Everything it needs to know."}
        },
        "required": ["task"],
    },
}

LEAK_QUESTION = (
    "Before the task: answer from your context only, not general knowledge, "
    "as one line of JSON with these keys: "
    '"user" (any name, email or employer of the user you were told, else null), '
    '"project" (any project, repository or codebase you were told about, '
    'else null), "instructions" (a list naming any memory, user preferences, '
    "project instructions or files you were given besides this message; empty "
    "if none)."
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StepLog:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")

    def add(self, **row: Any) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")


def _mcp_blocks(result) -> list[dict]:
    """An MCP tool result as Anthropic content blocks."""
    out: list[dict] = []
    for c in result.content or []:
        kind = getattr(c, "type", "")
        if kind == "text":
            out.append({"type": "text", "text": c.text})
        elif kind == "image":
            out.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": c.mimeType,
                        "data": c.data,
                    },
                }
            )
        elif kind == "resource_link":
            out.append({"type": "text", "text": f"Resource link: {c.uri} ({c.name})"})
        elif kind == "resource":
            out += _resource_blocks([c.resource])
    if not out and getattr(result, "structuredContent", None):
        out.append({"type": "text", "text": json.dumps(result.structuredContent)})
    return out or [{"type": "text", "text": "(no content)"}]


def _resource_blocks(contents) -> list[dict]:
    out: list[dict] = []
    for r in contents:
        mime = getattr(r, "mimeType", None) or ""
        if getattr(r, "text", None) is not None:
            out.append({"type": "text", "text": r.text})
        elif mime.startswith("image/"):
            out.append(
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": mime, "data": r.blob},
                }
            )
        else:
            out.append({"type": "text", "text": f"(binary {mime or 'data'} omitted)"})
    return out


def _chars(blocks: list[dict]) -> int:
    return sum(
        len(b.get("text") or b.get("source", {}).get("data", "")) for b in blocks
    )


class Agent:
    """One arm: its MCP sessions, provider and step log."""

    def __init__(self, provider: Provider, log: StepLog):
        self.provider, self.log = provider, log
        self.sessions: list = []
        self.tool_owner: dict[str, Any] = {}
        self.mcp_tools: list[dict] = []
        self.totals: dict[str, int] = {}
        self.models: set[str] = set()
        self.tool_calls: dict[str, int] = {}
        self.transcripts: list[dict] = []

    async def connect(self, servers: list[Server], stack: AsyncExitStack) -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        for s in servers:
            params = StdioServerParameters(command=s.command, args=s.args, env=s.env)
            r, w = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(r, w))
            await session.initialize()
            self.sessions.append(session)
            for t in (await session.list_tools()).tools:
                if t.name in s.deny:
                    continue
                if t.name in self.tool_owner or t.name in (
                    READ_RESOURCE["name"],
                    HELPER["name"],
                ):
                    raise RuntimeError(f"Tool name {t.name} is used twice")
                self.tool_owner[t.name] = session
                self.mcp_tools.append(
                    {
                        "name": t.name,
                        "description": t.description or "",
                        "input_schema": t.input_schema,
                    }
                )

    def tools(self, helper: bool) -> list[dict]:
        return [*self.mcp_tools, READ_RESOURCE, *([HELPER] if helper else [])]

    async def _read_resource(self, uri: str) -> tuple[list[dict], bool]:
        errors = []
        for s in self.sessions:
            try:
                res = await s.read_resource(uri)
                return _resource_blocks(res.contents), False
            except Exception as exc:
                errors.append(str(exc)[:200])
        return [{"type": "text", "text": f"Could not read {uri}: {errors}"}], True

    async def _tool(self, use: dict, depth: int) -> tuple[list[dict], bool]:
        name, args = use["name"], use.get("input") or {}
        if name == READ_RESOURCE["name"]:
            return await self._read_resource(str(args.get("uri", "")))
        if name == HELPER["name"] and depth == 0:
            text, _ = await self.converse(str(args.get("task", "")), depth + 1)
            return [{"type": "text", "text": text or "(no reply)"}], False
        session = self.tool_owner.get(name)
        if session is None:
            return [{"type": "text", "text": f"No tool named {name}"}], True
        try:
            res = await session.call_tool(name, args)
        except Exception as exc:
            return [{"type": "text", "text": f"Tool error: {exc}"[:2000]}], True
        return _mcp_blocks(res), bool(getattr(res, "is_error", False))

    def _count(self, reply: Reply) -> None:
        self.models.add(reply.model)
        for k, v in reply.usage.items():
            self.totals[k] = self.totals.get(k, 0) + v

    async def converse(self, task: str, depth: int = 0) -> tuple[str, str]:
        """Run one conversation to its end. Returns (final text, how it ended)."""
        messages: list[dict] = [{"role": "user", "content": task}]
        self.transcripts.append({"depth": depth, "messages": messages})
        limit = MAX_TURNS if depth == 0 else HELPER_TURNS
        final, ended = "", "max_turns"
        for turn in range(limit):
            t0, start = time.monotonic(), _now()
            try:
                reply = await self.provider.complete(
                    task_prompt.SYSTEM, messages, self.tools(depth == 0), MAX_TOKENS
                )
            except ContextExceeded as exc:
                self.log.add(type="model", depth=depth, turn=turn, error=str(exc))
                ended = "context_exceeded"
                break
            self._count(reply)
            text = "\n".join(b["text"] for b in reply.content if b["type"] == "text")
            uses = [b for b in reply.content if b["type"] == "tool_use"]
            self.log.add(
                type="model",
                depth=depth,
                turn=turn,
                start=start,
                seconds=round(time.monotonic() - t0, 3),
                model=reply.model,
                stop_reason=reply.stop_reason,
                usage=reply.usage,
                text=text,
                tool_uses=[u["name"] for u in uses],
            )
            messages.append({"role": "assistant", "content": reply.content})
            if text:
                final = text
            if not uses:
                ended = reply.stop_reason or "end_turn"
                break
            results = []
            for u in uses:
                t1, start1 = time.monotonic(), _now()
                blocks, is_error = await self._tool(u, depth)
                self.tool_calls[u["name"]] = self.tool_calls.get(u["name"], 0) + 1
                self.log.add(
                    type="tool",
                    depth=depth,
                    turn=turn,
                    start=start1,
                    seconds=round(time.monotonic() - t1, 3),
                    name=u["name"],
                    args=u.get("input"),
                    is_error=is_error,
                    result_chars=_chars(blocks),
                )
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": u["id"],
                        "content": blocks,
                        "is_error": is_error,
                    }
                )
            messages.append({"role": "user", "content": results})
        return final, ended


def leak_values() -> list[str]:
    # Old and new names: the repository URL still says a11y-assist.
    vals = ["tobi508", "508-tobi", "a11y_assist", "a11y-assist", "a11y assist"]
    vals.append("trusted tester")
    for key in ("user.email", "user.name"):
        try:
            v = subprocess.run(
                ["git", "config", key], capture_output=True, text=True, cwd=REPO
            ).stdout.strip()
        except OSError:
            v = ""
        if v:
            vals.append(v.lower())
    from evals.agent.providers import env

    vals += [v.strip().lower() for v in (env("AGENT_LEAK_VALUES") or "").split(",")]
    return [v for v in vals if v]


async def leak_check(provider, log: StepLog, servers: list[Server]) -> dict:
    """The arm's context before the task holds nothing of the user, this
    repo or its memory (plan section 7.2). On the CLI route the arm's
    servers are attached, as in the run."""
    t0 = time.monotonic()
    if isinstance(provider, ClaudeCodeCLI):
        got = await provider.leak_check(servers, LEAK_QUESTION)
        text, usage, model = got["text"], got["usage"], got["model"]
        extra = {"init": got["init"]}
    else:
        reply = await provider.complete(
            task_prompt.SYSTEM,
            [{"role": "user", "content": LEAK_QUESTION}],
            [],
            1000,
        )
        text = "\n".join(b["text"] for b in reply.content if b["type"] == "text")
        usage, model, extra = reply.usage, reply.model, {}
    try:
        got = json.loads(text[text.index("{") : text.rindex("}") + 1])
    except ValueError:
        got = {"unparsed": text}
    said = json.dumps(got).lower()
    hits = [v for v in leak_values() if v in said]
    out = {"answer": got, "leaked": hits, "usage": usage, "model": model, **extra}
    log.add(type="leak_check", seconds=round(time.monotonic() - t0, 3), **out)
    return out


def _describe(exc: BaseException) -> str:
    """The real cause, not "unhandled errors in a TaskGroup"."""
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return f"{type(exc).__name__}: {exc}"


def _commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
        ).stdout.strip()
    except OSError:
        return "unknown"


async def _executable() -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        return pw.chromium.executable_path


async def run_arm(
    rd: Path,
    arm: str,
    provider: Provider,
    servers: list[Server] | None = None,
    check_leaks: bool = True,
    egress_settings=None,
    label: str | None = None,
    prompt_version: str | None = None,
) -> dict:
    """Run arm "a" or "b" on round folder `rd`; returns the summary.

    Agent B's browser connects through an egress proxy (egress.py) with the
    server's own address checks, as Agent A's server does; its live pages
    are logged to results/arm-b/live.jsonl."""
    name = f"arm-{arm}" + (f"-{label}" if label else "")
    if servers is not None or arm == "a":
        return await _run_arm(
            rd, arm, provider, servers, check_leaks, name, prompt_version
        )
    from tobi508.config import Settings
    from tobi508.egress import EgressProxy

    out = (rd / "results" / name).resolve()
    async with EgressProxy(egress_settings or Settings()) as proxy:
        servers = browser_arm(
            (rd / "frozen").resolve(),
            out / "browser-files",
            await _executable(),
            proxy=proxy.url,
            live_log=out / "live.jsonl",
        )
        s = await _run_arm(
            rd, arm, provider, servers, check_leaks, name, prompt_version
        )
    s["egress_refused"] = proxy.refused[:100]
    (out / "summary.json").write_text(json.dumps(s, indent=1, default=str) + "\n")
    return s


async def _run_arm(
    rd, arm, provider, servers, check_leaks, name, prompt_version=None
) -> dict:
    from evals.agent import prompt_dev
    from evals.judging import _pages

    version = prompt_version or task_prompt.PROMPT_VERSION
    if version != task_prompt.PROMPT_VERSION and arm != "a":
        raise RuntimeError(f"Prompt {version} is for Agent A only")

    if (rd / "results" / "lock.json").exists():
        raise RuntimeError("This round is locked")
    frozen = (rd / "frozen").resolve()
    if not (frozen / "index.json").exists():
        raise RuntimeError(f"No frozen pages in {frozen}: run evals.agent.freeze")
    out = (rd / "results" / name).resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"{out} is not empty: this arm already ran")
    urls = [u for u, _ in _pages(rd)]
    task = prompt_dev.task(urls, version)
    if servers is None:
        servers = tool_arm(frozen, provider.model, out / "runs")
    log = StepLog(out / "steps.jsonl")
    agent = Agent(provider, log)
    summary: dict[str, Any] = {
        "arm": arm,
        "route": provider.route,
        "model_requested": provider.model,
        "prompt_version": version,
        "task_sha256": hashlib.sha256(task.encode()).hexdigest(),
        "code_commit": _commit(),
        "pages": urls,
        "servers": [
            {"name": s.name, "command": s.command, "args": s.args} for s in servers
        ],
        "started_at": _now(),
    }
    t0 = time.monotonic()
    final, ended = "", "error"
    try:
        if check_leaks:
            summary["leak_check"] = await leak_check(provider, log, servers)
            if summary["leak_check"]["leaked"]:
                ended = "stopped: context leak"
                raise RuntimeError(f"Context leak: {summary['leak_check']['leaked']}")
        if isinstance(provider, ClaudeCodeCLI):
            from urllib.parse import urlsplit

            hosts = sorted({urlsplit(u).hostname or "" for u in urls} - {""})
            res = await provider.run(task, servers, arm, log, hosts)
            final, ended = res["final"], res["ended"]
            agent.totals, agent.models = res["tokens"], set(res["models"])
            agent.tool_calls = res["tool_calls"]
            agent.transcripts = res["transcript"]
            for k in (
                "init",
                "model_usage",
                "cli_usage",
                "cli_duration_ms",
                "num_turns",
                "cost_usd_list_price",
                "exit_code",
                "stderr",
                "is_error",
            ):
                if k in res:
                    summary[k] = res[k]
            limits = res["rate_limits"]
            summary["usage_windows"] = {"first": limits[:1], "last": limits[-1:]}
            if res.get("error"):
                raise RuntimeError(res["error"])
        else:
            async with AsyncExitStack() as stack:
                await agent.connect(servers, stack)
                summary["tools"] = [t["name"] for t in agent.tools(True)]
                final, ended = await agent.converse(task)
    except Exception as exc:
        summary["error"] = _describe(exc)[:2000]
    finally:
        summary.update(
            ended=ended,
            finished_at=_now(),
            wall_s=round(time.monotonic() - t0, 1),
            tokens=agent.totals,
            models_reported=sorted(agent.models),
            tool_calls=agent.tool_calls,
            model_calls=sum(1 for line in log.path.open() if '"type": "model"' in line),
        )
        (out / "final.md").write_text(final + "\n", "utf-8")
        (out / "transcript.json").write_text(
            json.dumps(agent.transcripts, indent=1, default=str) + "\n", "utf-8"
        )
        (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main(argv: list[str]) -> None:
    from evals.agent.providers import AnthropicMessages

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arm", choices=["a", "b"], required=True)
    ap.add_argument(
        "--route",
        choices=["api", "cli"],
        default="api",
        help="api: an Anthropic-style API (Ask Sage); cli: the Claude Code CLI",
    )
    ap.add_argument("--model", default="claude-sonnet-5-5", help="cli route only")
    ap.add_argument(
        "--label", help="a repeat of an arm: results/arm-<arm>-<label>/ (e.g. 2)"
    )
    ap.add_argument(
        "--prompt",
        help="a development prompt version from prompt_dev.py (Agent A, never "
        "scored as a round); default: the round prompt",
    )
    ap.add_argument(
        "--no-subagents",
        action="store_true",
        help="cli route only: deny the CLI's own subagent tool",
    )
    ap.add_argument("round", type=Path)
    a = ap.parse_args(argv)
    provider = (
        ClaudeCodeCLI(a.model, no_subagents=a.no_subagents)
        if a.route == "cli"
        else AnthropicMessages.from_env()
    )
    s = asyncio.run(
        run_arm(a.round, a.arm, provider, label=a.label, prompt_version=a.prompt)
    )
    print(json.dumps({k: s[k] for k in ("ended", "wall_s", "tokens", "tool_calls")}))
    if s.get("error"):
        sys.exit(s["error"])


if __name__ == "__main__":
    main(sys.argv[1:])
