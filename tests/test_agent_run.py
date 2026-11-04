"""The agent loop (evals/agent/run.py) with a scripted model: a real MCP
server over stdio, a frozen round with the site down, the resource reader,
the helper tool, the step log and the leak check. No model API is called."""

from __future__ import annotations

import http.server
import json
import threading

import pytest

from evals.agent import run as agent_run
from evals.agent.arms import PLAYWRIGHT_MCP, tool_arm
from evals.agent.providers import AnthropicMessages, ContextExceeded, Reply, Scripted

from .test_agent_freeze import _frozen_round

FIXTURE_ENV = {
    "DEV_MODE": "true",
    "ALLOWED_DOMAINS": '["127.0.0.1"]',
    "DEV_ALLOWED_ADDRESSES": '["127.0.0.1/32"]',
    "BROWSER_ARGS": '["--disable-features=LocalNetworkAccessChecks"]',
}


def _text(t: str) -> dict:
    return {"type": "text", "text": t}


def _use(i: str, name: str, args: dict) -> dict:
    return {"type": "tool_use", "id": i, "name": name, "input": args}


def _results(messages) -> list[dict]:
    last = messages[-1]["content"]
    return [b for b in last if isinstance(b, dict) and b.get("type") == "tool_result"]


def _usage() -> dict:
    return {"input_tokens": 100, "output_tokens": 10}


def script(urls):
    def fn(system, messages, tools):
        first = messages[0]["content"]
        if first.startswith("Before the task"):  # the leak check
            return Reply(
                [_text('{"user": null, "project": null, "instructions": []}')],
                "end_turn",
                "m-reported",
                _usage(),
            )
        if first == "HELPER TASK":
            return Reply([_text("helper says hi")], "end_turn", "m-reported", _usage())
        n = len(messages)
        if n == 1:
            assert "WCAG 2.0" in first and urls[0] in first
            names = {t["name"] for t in tools}
            assert {"a11y_run_tt_tests", "read_mcp_resource", "ask_helper"} <= names
            return Reply(
                [
                    _use(
                        "u1",
                        "a11y_run_tt_tests",
                        {
                            "url": urls[0],
                            "tests": ["19.A"],
                            "other_pages": [urls[1]],
                            "no_time_limit": True,
                        },
                    )
                ],
                "tool_use",
                "m-reported",
                _usage(),
            )
        if n == 3:
            (res,) = _results(messages)
            assert not res["is_error"], res["content"]
            body = json.loads(res["content"][0]["text"])
            assert body["findings"][0]["test_id"] == "19.A"
            return Reply(
                [
                    _use("u2", "read_mcp_resource", {"uri": body["report_uri"]}),
                    _use("u3", "ask_helper", {"task": "HELPER TASK"}),
                ],
                "tool_use",
                "m-reported",
                _usage(),
            )
        if n == 5:
            report, helper = _results(messages)
            assert '"frozen_pages": "tested_frozen"' in report["content"][0]["text"]
            assert helper["content"][0]["text"] == "helper says hi"
            return Reply(
                [_text('Done.\nRESULT: {"x": {}}')], "end_turn", "m-reported", _usage()
            )
        raise AssertionError(f"unexpected turn {n}")

    return fn


async def test_arm_a_on_a_frozen_round(settings, tmp_path):
    rd, urls = await _frozen_round(settings, tmp_path)
    out = rd / "results" / "arm-a"
    servers = tool_arm((rd / "frozen").resolve(), "m-requested", out / "runs")
    servers[0].env |= FIXTURE_ENV
    s = await agent_run.run_arm(rd, "a", Scripted("m-requested", script(urls)), servers)
    assert s.get("error") is None and s["ended"] == "end_turn", s
    assert s["tool_calls"] == {
        "a11y_run_tt_tests": 1,
        "read_mcp_resource": 1,
        "ask_helper": 1,
    }
    # 3 turns at depth 0, 1 for the helper, plus the leak check.
    assert s["tokens"] == {"input_tokens": 400, "output_tokens": 40}
    assert (
        s["models_reported"] == ["m-reported"] and s["model_requested"] == "m-requested"
    )
    assert s["leak_check"]["leaked"] == []
    assert (out / "final.md").read_text().startswith("Done.\nRESULT:")
    steps = [json.loads(x) for x in (out / "steps.jsonl").read_text().splitlines()]
    assert [r["type"] for r in steps][:2] == ["leak_check", "model"]
    assert any(r["type"] == "model" and r["depth"] == 1 for r in steps)
    tool = next(r for r in steps if r.get("name") == "a11y_run_tt_tests")
    assert tool["seconds"] > 0 and tool["result_chars"] > 0
    reports = list((out / "runs").glob("*/report.json"))
    assert len(reports) == 1  # the tool's own report, for scoring
    assert (
        json.loads(reports[0].read_text())["versions"]["judging_model"] == "m-requested"
    )


async def test_a_leak_stops_the_run(settings, tmp_path, monkeypatch):
    rd = tmp_path / "r"
    (rd / "frozen").mkdir(parents=True)
    (rd / "frozen" / "index.json").write_text("{}")
    (rd / "pages.txt").write_text(f"https://www.example.gov/ {'ab' * 32}\n")
    monkeypatch.setenv("AGENT_LEAK_VALUES", "someone@example.gov")

    def fn(system, messages, tools):
        return Reply([_text('{"user": "someone@example.gov"}')], "end_turn", "m", {})

    s = await agent_run.run_arm(rd, "b", Scripted("m", fn), servers=[])
    assert s["ended"] == "stopped: context leak"
    assert s["leak_check"]["leaked"] == ["someone@example.gov"]


@pytest.mark.skipif(
    not PLAYWRIGHT_MCP.exists(), reason="npm install in evals/agent/node"
)
async def test_arm_b_on_a_frozen_round(settings, tmp_path):
    rd, urls = await _frozen_round(settings, tmp_path)

    def fn(system, messages, tools):
        if messages[0]["content"].startswith("Before the task"):
            return Reply([_text("{}")], "end_turn", "m", _usage())
        n = len(messages)
        if n == 1:
            names = {t["name"] for t in tools}
            assert "a11y_run_tt_tests" not in names
            assert "browser_navigate" in names
            assert "browser_run_code_unsafe" not in names  # escapes the replay
            return Reply(
                [_use("b1", "browser_navigate", {"url": urls[0]})],
                "tool_use",
                "m",
                _usage(),
            )
        if n == 3:
            return Reply(
                [_use("b2", "browser_snapshot", {})], "tool_use", "m", _usage()
            )
        (res,) = _results(messages)
        assert "Apply for benefits" in res["content"][0]["text"]
        return Reply([_text("RESULT: {}")], "end_turn", "m", _usage())

    s = await agent_run.run_arm(rd, "b", Scripted("m", fn))
    assert s.get("error") is None and s["ended"] == "end_turn", s
    assert s["tool_calls"] == {"browser_navigate": 1, "browser_snapshot": 1}


class _FakeApi(http.server.BaseHTTPRequestHandler):
    seen: list = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        headers = {k.lower(): v for k, v in self.headers.items()}
        self.seen.append((self.path, headers, body))
        if body["messages"][0]["content"] == "too long":
            out, code = b'{"error": {"message": "prompt is too long"}}', 400
        else:
            out, code = (
                json.dumps(
                    {
                        "content": [{"type": "text", "text": "hi"}],
                        "stop_reason": "end_turn",
                        "model": "claude-sonnet-5-5",
                        "usage": {
                            "input_tokens": 7,
                            "output_tokens": 2,
                            "cache_read_input_tokens": 0,
                            "service_tier": "std",
                        },
                    }
                ).encode(),
                200,
            )
        self.send_response(code)
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


async def test_anthropic_messages_adapter():
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeApi)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        p = AnthropicMessages(
            f"http://127.0.0.1:{httpd.server_address[1]}/server/anthropic",
            "secret",
            "claude-sonnet-5-5-gov",
            auth_header="x-access-tokens",
        )
        r = await p.complete("sys", [{"role": "user", "content": "q"}], [], 50)
        assert (r.model, r.stop_reason) == ("claude-sonnet-5-5", "end_turn")
        assert r.usage == {
            "input_tokens": 7,
            "output_tokens": 2,
            "cache_read_input_tokens": 0,
        }
        path, headers, body = _FakeApi.seen[-1]
        assert path == "/server/anthropic/v1/messages"
        assert headers["x-access-tokens"] == "secret"
        assert body["temperature"] == 0 and body["model"] == "claude-sonnet-5-5-gov"
        assert "tools" not in body
        with pytest.raises(ContextExceeded):
            await p.complete("sys", [{"role": "user", "content": "too long"}], [], 50)
    finally:
        httpd.shutdown()
        httpd.server_close()
