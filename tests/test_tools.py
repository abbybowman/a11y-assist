"""MCP tools end to end through an in-memory FastMCP client.

Checks evidence collection and open-question plumbing only, never outcomes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import Client

from a11y_assist import config
from a11y_assist.app import mcp
from a11y_assist.models import (
    OpenQuestion,
    Outcome,
    Report,
    TestId,
)
from a11y_assist.runlog import RunRecorder

from .conftest import FIXTURES


@pytest.fixture(autouse=True)
def _use_test_settings(settings, monkeypatch):
    monkeypatch.setattr(config, "settings", settings)


async def _call(name: str, args: dict) -> dict:
    async with Client(mcp) as client:
        result = await client.call_tool(name, args, raise_on_error=False)
    return json.loads(result.content[0].text)


async def test_tools_are_listed():
    async with Client(mcp) as client:
        names = {t.name for t in await client.list_tools()}
    assert {"a11y_run_tt_tests", "a11y_answer_questions"} <= names
    # Old names are gone (renamed with the service prefix, 2026-11-01).
    assert not {"run_tt_tests", "answer_questions"} & names
    assert not {"collect_keyboard_evidence", "submit_judgments"} & names


async def test_no_time_limit_is_an_opt_in_input():
    async with Client(mcp) as client:
        [tool] = [t for t in await client.list_tools() if t.name == "a11y_run_tt_tests"]
    prop = tool.inputSchema["properties"]["no_time_limit"]
    assert prop["type"] == "boolean" and prop["default"] is False
    assert "no_time_limit=true" in tool.description


async def test_run_tt_tests_on_http_page(settings, server):
    out = await _call(
        "a11y_run_tt_tests", {"url": f"{server.base}/no_trap.html", "tests": ["4.C"]}
    )
    assert out["errors"] == []
    assert "NOT a certified" in out["disclaimer"]
    assert out["walk"]["P1"]["end"] == "wrap"
    assert out["walk"]["P2"]["end"] == "wrap"
    [finding] = out["findings"]
    assert (finding["test_id"], finding["outcome"]) == ("4.C", "PASS")
    assert finding["rows"] == ["A3", "G4"]
    assert "never got trapped" in finding["summary"]
    assert out["open_questions"] == []
    # The full report is a resource, not inline (it was ~60% of the result).
    assert "report" not in out
    assert out["report_uri"] == f"run://{out['run_id']}/report.json"
    assert f"run://{out['run_id']}/report.json" in out["evidence"]
    assert f"run://{out['run_id']}/evidence/walk.json" in out["evidence"]
    assert not any("/home/" in u or "\\" in u for u in out["evidence"])

    run_dir = settings.runs_dir / out["run_id"]
    assert (run_dir / "evidence" / "page.har.zip").is_file()
    # Screenshots only at trap events (spec 1.5.0); this page has none.
    assert not (run_dir / "evidence" / "shots").exists()

    report = Report.model_validate_json((run_dir / "report.json").read_text())
    assert report.certified is False
    assert report.versions.playwright == "1.63.0"
    assert report.versions.andi.startswith("29.2.2")
    assert report.versions.browser
    assert report.versions.run_settings == {
        "settle_quiet_ms": settings.settle_quiet_ms,
        "record_scroll_passes": settings.record_scroll_passes,
        "run_limit_s": settings.run_limit_s,
        "no_time_limit": False,
    }

    steps = [json.loads(line) for line in (run_dir / "steps.jsonl").open()]
    names = [s["step"] for s in steps]
    assert names[0] == "run_start" and names[-1] == "run_end"
    assert "captured" in names and "walk" in names and "collected" in names
    # Each phase's cost, to decide where the time budget goes (evals/time_budget.py).
    [walk] = [s for s in steps if s["step"] == "walk"]
    assert walk["detail"]["cost"]["loads"] == 2
    assert walk["detail"]["cost"]["presses"] == (
        out["walk"]["P1"]["presses"] + out["walk"]["P2"]["presses"]
    )
    for s in steps:
        if s["step"] == "collected":
            assert set(s["detail"]["cost"]) == {"loads", "presses", "seconds"}


async def test_collect_on_file_fixture_in_dev_mode(settings):
    url = (FIXTURES / "4c/f04-field-swallows-tab.html").as_uri()
    out = await _call("a11y_run_tt_tests", {"url": url})
    assert out["errors"] == []
    # The field swallows Tab: P1 ends as soon as it is stuck for 3 presses.
    assert out["walk"]["P1"]["end"] == "stuck"
    assert out["walk"]["P1"]["presses"] == 4
    # 3 tabbable candidates -> spec cap 3 x 3 + 50 = 59 presses.
    assert out["walk"]["P1"]["cap"] == 59


async def test_selected_tests_are_deduplicated_and_ordered(settings):
    url = (FIXTURES / "no_trap.html").as_uri()
    out = await _call("a11y_run_tt_tests", {"url": url, "tests": ["4.E", "4.A", "4.E"]})
    assert out["errors"] == []
    assert out["tests"] == ["4.A", "4.E"]
    assert [f["test_id"] for f in out["findings"]] == ["4.A", "4.E"]


async def test_no_test_is_reported_not_tested(settings):
    url = (FIXTURES / "no_trap.html").as_uri()
    out = await _call(
        "a11y_run_tt_tests", {"url": url, "tests": [t.value for t in TestId]}
    )
    assert out["errors"] == []
    by_id = {f["test_id"]: f for f in out["findings"]}
    assert set(by_id) == {t.value for t in TestId}
    from a11y_assist.checks import REGISTRY

    built = {t.value for t in REGISTRY}
    for t in built:
        assert by_id[t]["outcome"] == "PASS", (t, by_id[t]["summary"])
    for f in [f for t, f in by_id.items() if t not in built]:
        assert f["outcome"] == "NEEDS_REVIEW"
        assert f["note"] == "This test could not be performed"
    for t in by_id:
        if t not in built:
            assert "No rules exist" in by_id[t]["summary"], t
    async with Client(mcp) as client:
        [content] = await client.read_resource(out["report_uri"])
    report = Report.model_validate_json(content.text)
    assert report.certified is False
    assert all(f.outcome is not Outcome.NOT_TESTED for f in report.findings)


@pytest.mark.parametrize("tests", [[], ["4.G"], ["4.H"], ["2.1.2"]])
async def test_invalid_test_selection_is_rejected_by_schema(settings, tests):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "a11y_run_tt_tests",
            {"url": "https://x.gov", "tests": tests},
            raise_on_error=False,
        )
    assert result.is_error


async def _call_error(name: str, args: dict) -> str:
    async with Client(mcp) as client:
        result = await client.call_tool(name, args, raise_on_error=False)
    assert result.is_error
    return result.content[0].text


async def test_disallowed_url_is_a_tool_error_without_browsing(settings, server):
    msg = await _call_error(
        "a11y_run_tt_tests", {"url": f"http://localhost:{server.port}/dyn"}
    )
    assert "not allowed" in msg
    assert server.hits[("localhost", "/dyn")] == 0
    assert not settings.runs_dir.exists() or not any(settings.runs_dir.iterdir())


async def test_redirect_out_of_allowlist_is_a_tool_error(settings, server):
    msg = await _call_error("a11y_run_tt_tests", {"url": f"{server.base}/redir-bad"})
    assert "blocked" in msg.lower()
    assert server.hits[("localhost", "/landed")] == 0
    assert not any(settings.runs_dir.iterdir())  # nothing kept for an untested page


def _seed_run_with_question(settings) -> tuple[str, str]:
    run = RunRecorder(settings.runs_dir)
    from a11y_assist.models import utcnow
    from a11y_assist.versions import collect_versions

    q = OpenQuestion(
        question_id="q1",
        test_id=TestId.T4C,
        kind="J1",
        instance="i1",
        question="Does this text document an exit key?",
        rubric="test rubric",
        input={"text": []},
    )
    report = Report(
        run_id=run.run_id,
        target="https://x.gov",
        started_at=utcnow(),
        versions=collect_versions(settings, None),
        questions=[q],
        open_questions=[q],
        evidence_dir=str(run.evidence_dir),
    )
    run.write_json(run.report_path, report)
    return run.run_id, str(run.report_path)


async def test_answer_questions_records_and_rejects_invalid(settings):
    run_id, report_path = _seed_run_with_question(settings)
    j1 = {"documented": "no"}
    out = await _call(
        "a11y_answer_questions",
        {
            "run_id": run_id,
            "answers": [
                {"question_id": "q1", "rationale": "r", "j2": {"gate": "no"}},
                {"question_id": "nope", "rationale": "r", "j1": j1},
                {"question_id": "q1", "rationale": "r", "j1": j1},
            ],
        },
    )
    assert out["accepted"] == ["q1"] and len(out["rejected"]) == 2
    assert out["open_questions"] == []  # one answer closes a question

    # A person's answer overrides the model's.
    yes = {"documented": "yes", "keys": ["Escape"], "quote": "Press Esc"}
    out = await _call(
        "a11y_answer_questions",
        {
            "run_id": run_id,
            "answers": [
                {
                    "question_id": "q1",
                    "rationale": "r",
                    "j1": yes,
                    "decided_by": "human",
                }
            ],
        },
    )
    assert out["accepted"] == ["q1"]
    report = Report.model_validate_json(Path(report_path).read_text())
    assert [a.answer.decided_by.value for a in report.answers] == ["model", "human"]
    assert report.findings == []  # recording an answer never sets an outcome


_ANSWER = {
    "question_id": "q",
    "rationale": "r",
    "j1": {"documented": "no"},
}


async def test_answer_questions_rejects_path_like_run_id_by_schema(settings):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "a11y_answer_questions",
            {"run_id": "../etc", "answers": [_ANSWER]},
            raise_on_error=False,
        )
    assert result.is_error


async def test_answer_questions_unknown_run_id_is_a_tool_error(settings):
    msg = await _call_error(
        "a11y_answer_questions", {"run_id": "missing-run", "answers": [_ANSWER]}
    )
    assert "No run named" in msg


async def test_evidence_is_readable_as_resources_and_confined(settings, server):
    out = await _call("a11y_run_tt_tests", {"url": f"{server.base}/no_trap.html"})
    async with Client(mcp) as client:
        [content] = await client.read_resource(f"run://{out['run_id']}/report.json")
        assert json.loads(content.text)["run_id"] == out["run_id"]
        for bad in (
            f"run://{out['run_id']}/../../etc/passwd",
            f"run://{out['run_id']}/evidence/nope.json",
        ):
            with pytest.raises(Exception):
                await client.read_resource(bad)


async def test_old_runs_expire(settings, server):
    import os
    import time

    from a11y_assist.runlog import prune_runs

    out = await _call("a11y_run_tt_tests", {"url": f"{server.base}/no_trap.html"})
    run_dir = settings.runs_dir / out["run_id"]
    old = time.time() - 25 * 3600
    os.utime(run_dir / "report.json", (old, old))
    assert prune_runs(settings.runs_dir, 24) == 1 and not run_dir.exists()
    msg = await _call_error(
        "a11y_answer_questions", {"run_id": out["run_id"], "answers": [_ANSWER]}
    )
    assert "may have expired" in msg and "/" not in msg.split("(")[0]


async def test_tt_text_is_available_as_resources(settings):
    async with Client(mcp) as client:
        [index] = await client.read_resource("tt://5.1.3/index")
        rows = json.loads(index.text)
        assert len(rows) == 63 and {r["id"] for r in rows} >= {"4.C", "6.B"}
        [t] = await client.read_resource("tt://5.1.3/tests/4.C")
        assert "There is no keyboard trap." in t.text
        assert "Understanding/no-keyboard-trap.html" in t.text
        [part] = await client.read_resource("tt://5.1.3/parts/appendix-b-change-log")
        assert "Document Change Log" in part.text
        for bad in ("tt://5.1.3/tests/9.Z", "tt://5.1.3/parts/../tt"):
            with pytest.raises(Exception):
                await client.read_resource(bad)


async def _prompt(args: dict) -> str:
    async with Client(mcp) as client:
        r = await client.get_prompt("explain", args)
    return r.messages[0].content.text


async def test_explain_before_a_run(settings):
    text = await _prompt({"about": "4.C"})
    assert "before any testing" in text
    assert "There is no keyboard trap." in text  # the TT text
    assert "Understanding/no-keyboard-trap.html" in text
    assert "tries the keys a person would" in text  # what this tool does
    assert "NOT a certified" in text
    # Untested tests say so plainly.
    assert "cannot run this test yet" in await _prompt({"about": "5.A"})


async def test_explain_finds_tests_by_words_criterion_or_name(settings):
    assert "=== 4.C ===" in await _prompt({"about": "keyboard trap"})
    assert "=== 4.C ===" in await _prompt({"about": "2.1.2-no-keyboard-trap"})
    many = await _prompt({"about": "1.3.1"})  # one WCAG SC, many TT tests
    assert "=== 5.C ===" in many and "=== 14.B ===" in many
    assert "Full text: tt://5.1.3/tests/14.B" in many  # brief entries
    assert "Ask the user which" in await _prompt({"about": "zzzz"})


async def test_explain_after_a_run(settings, server):
    out = await _call(
        "a11y_run_tt_tests", {"url": f"{server.base}/no_trap.html", "tests": ["4.C"]}
    )
    [f] = out["findings"]
    assert f["reference"] == "tt://5.1.3/tests/4.C"
    assert f["understanding"] == [
        "https://www.w3.org/WAI/WCAG22/Understanding/no-keyboard-trap.html"
    ]
    text = await _prompt({"run_id": out["run_id"]})  # every result of the run
    assert "Explain these results" in text and "Result for 4.C: PASS" in text
    gone = await _prompt({"about": "4.C", "run_id": "20000101T000000Z-000000"})
    assert "no longer on the server" in gone and "saved its report" in gone


async def test_tool_descriptions_follow_the_registry():
    # The implemented-test list and the default come from checks.REGISTRY, so
    # they cannot go stale when a check is added.
    from a11y_assist.checks import REGISTRY

    async with Client(mcp) as client:
        tools = {t.name: t for t in await client.list_tools()}
    run = tools["a11y_run_tt_tests"]
    built = [t.value for t in TestId if t in REGISTRY]
    assert run.inputSchema["properties"]["tests"]["default"] == built
    for t in REGISTRY:
        assert f"{t.value} ({t.tt_name})" in run.description
    assert "subagent" in run.description and "certified" in run.description
    answer = tools["a11y_answer_questions"].inputSchema
    assert "duration_ms" in str(answer)


async def test_open_questions_are_named_in_the_summary(settings, server):
    # While a question is open the summary says so, instead of "a person needs
    # to check it" (the agent answers it next). Wording only.
    url = f"{server.base}/4a/f01-click-only-text.html"
    out = await _call("a11y_run_tt_tests", {"url": url, "tests": ["4.A"]})
    [f] = out["findings"]
    assert f["outcome"] == "NEEDS_REVIEW"
    assert f["summary"].startswith("This test is not finished yet: 1 question about")
    assert "a person needs to check it" not in f["summary"]
    assert '"Show delivery times"' in f["summary"]


async def test_shared_evidence_is_sent_once(settings, server):
    # Judge eval 2026-10-31: every 4.A question repeated the whole stop list.
    # It now goes once per result, and questions name it.
    url = f"{server.base}/4a/f04-hover-only-menu.html"
    out = await _call("a11y_run_tt_tests", {"url": url, "tests": ["4.A"]})
    assert len(out["open_questions"]) == 2
    for q in out["open_questions"]:
        assert q["shared"] == ["stops"] and "stops" not in q["input"]
    names = [s["name"] for s in out["shared_inputs"]["stops"]]
    assert names == ["Home", "Services"]
