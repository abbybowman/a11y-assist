"""The Claude Code CLI route (evals/agent/cli.py) against a fake `claude`
that records its arguments and environment and prints a canned stream:
isolation flags, the step log, totals and usage windows. No model call."""

# ruff: noqa: E501  (the fake CLI script is kept on readable lines)
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from evals.agent import run as agent_run
from evals.agent.arms import Server
from evals.agent.cli import DROP, ClaudeCodeCLI

FAKE = r"""
import json, os, sys, time
out = os.environ["FAKE_OUT"]
prompt = sys.argv[sys.argv.index("-p") + 1]
json.dump({"argv": sys.argv, "env": dict(os.environ), "cwd": os.getcwd(),
           "cwd_files": os.listdir(".")},
          open(os.path.join(out, "call-%d.json" % len(os.listdir(out))), "w"))
def say(e): print(json.dumps(e), flush=True)
say({"type": "system", "subtype": "init", "tools": ["mcp__x__t"],
     "mcp_servers": [{"name": "x", "status": "connected"}], "model": "m"})
if prompt.startswith("Before the task"):
    say({"type": "result", "result": '{"user": null, "project": null, "instructions": []}',
         "modelUsage": {"m": {"inputTokens": 1}}})
    sys.exit(0)
def call(mid, parent, content, stop, out_tokens):
    base = {"type": "stream_event", "api_message_id": mid, "parent_tool_use_id": parent}
    say({**base, "event": {"type": "message_start", "message": {"id": mid, "model": "m-reported",
         "usage": {"input_tokens": 10, "cache_read_input_tokens": 5, "output_tokens": 1}}}})
    say({**base, "event": {"type": "content_block_delta", "delta": {"text": "x"}}})
    say({"type": "assistant", "parent_tool_use_id": parent,
         "message": {"id": mid, "content": content}})
    say({**base, "event": {"type": "message_delta", "delta": {"stop_reason": stop},
         "usage": {"output_tokens": out_tokens}}})
    time.sleep(0.05)
    say({**base, "event": {"type": "message_stop"}})
call("m1", None, [{"type": "tool_use", "id": "u1", "name": "mcp__x__t", "input": {"a": 1}}],
     "tool_use", 7)
time.sleep(0.1)
say({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "u1",
     "content": [{"type": "text", "text": "result!"}]}]}})
say({"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows":
     {"five_hour": {"utilization": 0.1, "resetsAt": 1}}}})
call("m2", None, [{"type": "text", "text": "Done.\nRESULT: {}"}], "end_turn", 9)
say({"type": "result", "result": "Done.\nRESULT: {}", "terminal_reason": "completed",
     "modelUsage": {"m-reported": {"inputTokens": 20}}, "num_turns": 2,
     "total_cost_usd": 0.01, "duration_ms": 300})
"""


async def test_cli_route_isolation_and_log(tmp_path, monkeypatch):
    fake = tmp_path / "claude"
    fake.write_text(f"#!{sys.executable}\n{FAKE}")
    fake.chmod(0o755)
    calls = tmp_path / "calls"
    calls.mkdir()
    monkeypatch.setenv("FAKE_OUT", str(calls))
    monkeypatch.setenv("CLAUDE_CODE_USER_EMAIL", "someone@example.gov")
    rd = tmp_path / "round"
    (rd / "frozen").mkdir(parents=True)
    (rd / "frozen" / "index.json").write_text("{}")
    (rd / "pages.txt").write_text(f"https://www.example.gov/a {'ab' * 32}\n")
    servers = [Server("x", "true", [], {}, deny=["evil"])]
    s = await agent_run.run_arm(rd, "b", ClaudeCodeCLI("m", str(fake)), servers)
    assert s.get("error") is None and s["ended"] == "completed", s
    assert s["leak_check"]["leaked"] == []
    assert s["tool_calls"] == {"mcp__x__t": 1}
    assert s["model_calls"] == 2 and s["models_reported"] == ["m-reported"]
    assert s["tokens"] == {
        "input_tokens": 20,
        "cache_read_input_tokens": 10,
        "output_tokens": 16,
    }
    assert s["usage_windows"]["last"][0]["unifiedWindows"]["five_hour"]["utilization"]
    out = rd / "results" / "arm-b"
    assert (out / "final.md").read_text().startswith("Done.\nRESULT:")
    steps = [json.loads(x) for x in (out / "steps.jsonl").read_text().splitlines()]
    tool = next(r for r in steps if r["type"] == "tool")
    assert tool["seconds"] >= 0.1 and tool["result_chars"] > 0
    model = [r for r in steps if r["type"] == "model"]
    assert all(r["seconds"] >= 0.05 for r in model)
    transcript = json.loads((out / "transcript.json").read_text())
    assert not any(e.get("type") == "stream_event" for e in transcript)  # no deltas

    leak, run = [json.loads(p.read_text()) for p in sorted(calls.iterdir())]
    for c in (leak, run):
        argv, env = c["argv"], c["env"]
        assert not set(DROP) & set(env)  # the email and session ids are gone
        assert Path(env["HOME"]).name == "home" and env["HOME"] != os.environ["HOME"]
        assert Path(c["cwd"]).name == "work" and c["cwd_files"] == []
        for flag in (
            "--strict-mcp-config",
            "--disable-slash-commands",
            "--no-session-persistence",
        ):
            assert flag in argv
        assert argv[argv.index("--setting-sources") + 1] == ""
    assert leak["argv"][leak["argv"].index("--tools") + 1] == ""
    argv = run["argv"]
    tools = argv[argv.index("--tools") + 1].split(",")
    assert "WebSearch" in tools and "WebFetch" not in tools  # never the live site
    assert argv[argv.index("--disallowedTools") + 1] == "mcp__x__evil"
