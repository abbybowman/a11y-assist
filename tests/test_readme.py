"""The README's examples work: every call matches the tool's schema, and
example 3 runs end to end on its local fixture."""

from __future__ import annotations

import json
import re

from fastmcp import Client

from a11y_assist import config
from a11y_assist.app import mcp
from a11y_assist.config import REPO_ROOT, Settings
from a11y_assist.models import TestId
from a11y_assist.policy import check_url

EXAMPLE = re.compile(r"<!-- example -->\n```json\n(.*?)\n```", re.S)


def _examples() -> list[dict]:
    text = (REPO_ROOT / "README.md").read_text("utf-8")
    return [json.loads(m) for m in EXAMPLE.findall(text)]


async def test_examples_match_the_tool_schemas():
    examples = _examples()
    runs = [e for e in examples if e["tool"] == "run_tt_tests"]
    assert len(runs) >= 3
    async with Client(mcp) as client:
        schemas = {t.name: t.inputSchema for t in await client.list_tools()}
    prod = Settings(_env_file=None)
    for e in examples:
        schema = schemas[e["tool"]]
        assert set(schema.get("required", [])) <= set(e["arguments"])
        assert set(e["arguments"]) <= set(schema["properties"])
    for e in runs:
        args = e["arguments"]
        for t in args.get("tests", []):
            TestId(t)
        dev = args["url"].startswith("file:")
        assert check_url(args["url"], prod.allowed_domains, dev).allowed


async def test_example_3_runs_as_described(settings, monkeypatch):
    monkeypatch.setattr(config, "settings", settings)
    run, answer = [
        e
        for e in _examples()
        if "f06" in json.dumps(e) or e["tool"] == "answer_questions"
    ]
    fixture = REPO_ROOT / "tests/fixtures/4c/f06-script-loop.html"
    args = dict(run["arguments"], url=fixture.as_uri())
    assert run["arguments"]["url"].endswith("/tests/fixtures/4c/f06-script-loop.html")
    async with Client(mcp) as client:
        out = json.loads((await client.call_tool("run_tt_tests", args)).content[0].text)
        [finding] = out["findings"]
        assert finding["outcome"] == "NEEDS_REVIEW"
        assert [q["question_id"] for q in out["open_questions"]] == ["4.C-i1-J1"]
        a_args = dict(answer["arguments"], run_id=out["run_id"])
        res = await client.call_tool("answer_questions", a_args)
        done = json.loads(res.content[0].text)
    assert done["accepted"] == ["4.C-i1-J1"] and done["open_questions"] == []
    [finding] = done["findings"]
    assert finding["outcome"] == "FAIL"
    assert "Keyboard focus gets trapped on this page" in finding["summary"]
