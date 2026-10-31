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
    assert {"run_tt_tests", "answer_questions"} <= names
    assert not {"collect_keyboard_evidence", "submit_judgments"} & names


async def test_run_tt_tests_on_http_page(settings, server):
    out = await _call("run_tt_tests", {"url": f"{server.base}/no_trap.html"})
    assert out["errors"] == []
    assert "NOT a certified" in out["disclaimer"]
    assert out["forward"]["stopped_because"] == "returned_to_start"
    assert out["backward"]["stops"] > 0
    assert out["tests"] == ["4.C"]  # default selection
    assert [f["test_id"] for f in out["findings"]] == ["4.C"]
    assert [f["outcome"] for f in out["findings"]] == ["NOT_TESTED"]
    assert out["open_questions"] == []

    run_dir = Path(out["run_dir"])
    assert run_dir.parent == settings.runs_dir.resolve()
    assert (run_dir / "evidence" / "page.har.zip").is_file()
    evidence = json.loads(Path(out["keyboard_evidence"]).read_text())
    for stop in evidence["forward"]["stops"] + evidence["backward"]["stops"]:
        assert (run_dir / stop["screenshot"]).is_file()

    report = Report.model_validate_json((run_dir / "report.json").read_text())
    assert report.certified is False
    assert report.versions.playwright == "1.63.0"
    assert report.versions.andi.startswith("29.2.2")
    assert report.versions.browser

    steps = [json.loads(line) for line in (run_dir / "steps.jsonl").open()]
    names = [s["step"] for s in steps]
    assert names[0] == "run_start" and names[-1] == "run_end"
    assert "captured" in names and names.count("focus_walk") == 2


async def test_collect_on_file_fixture_in_dev_mode(settings):
    url = (FIXTURES / "simple_trap.html").as_uri()
    out = await _call("run_tt_tests", {"url": url, "max_presses": 6})
    assert out["errors"] == []
    assert out["forward"]["presses"] == 6
    assert out["forward"]["stopped_because"] == "max_presses"


async def test_selected_tests_are_deduplicated_and_ordered(settings):
    url = (FIXTURES / "no_trap.html").as_uri()
    out = await _call(
        "run_tt_tests", {"url": url, "tests": ["4.E", "4.A", "4.E"], "max_presses": 3}
    )
    assert out["errors"] == []
    assert out["tests"] == ["4.A", "4.E"]
    assert [f["test_id"] for f in out["findings"]] == ["4.A", "4.E"]


@pytest.mark.parametrize("tests", [[], ["4.G"], ["4.H"], ["2.1.2"]])
async def test_invalid_test_selection_is_rejected_by_schema(settings, tests):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "run_tt_tests",
            {"url": "https://x.gov", "tests": tests},
            raise_on_error=False,
        )
    assert result.is_error


async def test_disallowed_url_is_refused_without_browsing(settings, server):
    out = await _call("run_tt_tests", {"url": f"http://localhost:{server.port}/dyn"})
    assert out["errors"] and "not allowed" in out["errors"][0]
    assert server.hits[("localhost", "/dyn")] == 0
    assert "forward" not in out


async def test_redirect_out_of_allowlist_is_reported(settings, server):
    out = await _call("run_tt_tests", {"url": f"{server.base}/redir-bad"})
    assert out["errors"] and "blocked" in out["errors"][0]
    assert server.hits[("localhost", "/landed")] == 0


def _seed_run_with_question(settings) -> tuple[str, str]:
    run = RunRecorder(settings.runs_dir)
    from a11y_assist.models import utcnow
    from a11y_assist.versions import collect_versions

    q = OpenQuestion(
        question_id="q1",
        test_id=TestId.T4D,
        question="Is a focus indicator visible in the screenshot?",
        rubric="test rubric",
        allowed_outcomes=[Outcome.FAIL, Outcome.NEEDS_REVIEW],
        evidence_paths=[str(run.evidence_dir / "x.png")],
    )
    report = Report(
        run_id=run.run_id,
        target="https://x.gov",
        started_at=utcnow(),
        versions=collect_versions(settings, None),
        open_questions=[q],
        evidence_dir=str(run.evidence_dir),
    )
    run.write_json(run.report_path, report)
    return run.run_id, str(run.report_path)


async def test_answer_questions_records_valid_and_rejects_invalid(settings):
    run_id, report_path = _seed_run_with_question(settings)
    answer = {"question_id": "q1", "rationale": "r", "confidence": 0.4}
    out = await _call(
        "answer_questions",
        {
            "run_id": run_id,
            "answers": [
                {**answer, "outcome": "PASS"},  # not allowed for this question
                {**answer, "question_id": "nope", "outcome": "FAIL"},
            ],
        },
    )
    assert out["accepted"] == [] and len(out["rejected"]) == 2
    assert out["still_open"] == ["q1"]

    out = await _call(
        "answer_questions",
        {"run_id": run_id, "answers": [{**answer, "outcome": "NEEDS_REVIEW"}]},
    )
    assert out["accepted"] == ["q1"] and out["still_open"] == []
    report = Report.model_validate_json(Path(report_path).read_text())
    assert report.answers[0].answer.outcome is Outcome.NEEDS_REVIEW
    assert report.answers[0].answer.decided_by.value == "model"
    assert report.findings == []  # recording an answer never sets an outcome


_ANSWER = {"question_id": "q", "outcome": "FAIL", "rationale": "r", "confidence": 1}


async def test_answer_questions_rejects_path_like_run_id_by_schema(settings):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "answer_questions",
            {"run_id": "../etc", "answers": [_ANSWER]},
            raise_on_error=False,
        )
    assert result.is_error


async def test_answer_questions_unknown_run_id(settings):
    out = await _call(
        "answer_questions", {"run_id": "missing-run", "answers": [_ANSWER]}
    )
    assert "No run named" in out["error"]
