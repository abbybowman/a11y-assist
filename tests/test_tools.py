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
    assert out["passes"]["P1"]["end"] == "wrap"
    assert out["passes"]["P2"]["end"] == "wrap"
    assert out["tests"] == ["4.C"]  # default selection
    [finding] = out["findings"]
    assert (finding["test_id"], finding["outcome"]) == ("4.C", "PASS")
    assert finding["rows"] == ["A3", "G4"]
    assert out["open_questions"] == []

    run_dir = Path(out["run_dir"])
    assert run_dir.parent == settings.runs_dir.resolve()
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
    }

    steps = [json.loads(line) for line in (run_dir / "steps.jsonl").open()]
    names = [s["step"] for s in steps]
    assert names[0] == "run_start" and names[-1] == "run_end"
    assert "captured" in names and "4c_collected" in names


async def test_collect_on_file_fixture_in_dev_mode(settings):
    url = (FIXTURES / "4c/f04-field-swallows-tab.html").as_uri()
    out = await _call("run_tt_tests", {"url": url})
    assert out["errors"] == []
    # The field swallows Tab: P1 ends as soon as it is stuck for 3 presses.
    assert out["passes"]["P1"]["end"] == "stuck"
    assert out["passes"]["P1"]["presses"] == 4
    # 3 tabbable candidates -> spec cap 3 x 3 + 50 = 59 presses.
    assert out["passes"]["P1"]["cap"] == 59


async def test_selected_tests_are_deduplicated_and_ordered(settings):
    url = (FIXTURES / "no_trap.html").as_uri()
    out = await _call("run_tt_tests", {"url": url, "tests": ["4.E", "4.A", "4.E"]})
    assert out["errors"] == []
    assert out["tests"] == ["4.A", "4.E"]
    assert [f["test_id"] for f in out["findings"]] == ["4.A", "4.E"]


async def test_no_test_is_reported_not_tested(settings):
    url = (FIXTURES / "no_trap.html").as_uri()
    out = await _call("run_tt_tests", {"url": url, "tests": [t.value for t in TestId]})
    assert out["errors"] == []
    by_id = {f["test_id"]: f for f in out["findings"]}
    assert set(by_id) == {t.value for t in TestId}
    assert by_id["4.C"]["outcome"] == "PASS"
    for f in [f for t, f in by_id.items() if t != "4.C"]:
        assert f["outcome"] == "NEEDS_REVIEW"
        assert f["note"] == "This test could not be performed"
    for t in ["4.A", "4.B", "4.D", "4.E", "4.F"]:
        assert "No rules spec exists" in by_id[t]["rationale"]
    report = Report.model_validate_json(Path(out["report_path"]).read_text())
    assert all(f.outcome is not Outcome.NOT_TESTED for f in report.findings)


@pytest.mark.parametrize("tests", [[], ["4.G"], ["4.H"], ["2.1.2"]])
async def test_invalid_test_selection_is_rejected_by_schema(settings, tests):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "run_tt_tests",
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
        "run_tt_tests", {"url": f"http://localhost:{server.port}/dyn"}
    )
    assert "not allowed" in msg
    assert server.hits[("localhost", "/dyn")] == 0
    assert not settings.runs_dir.exists() or not any(settings.runs_dir.iterdir())


async def test_redirect_out_of_allowlist_is_a_tool_error(settings, server):
    msg = await _call_error("run_tt_tests", {"url": f"{server.base}/redir-bad"})
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
        "answer_questions",
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
    assert out["still_open"] == []  # one answer closes a question

    # A person's answer overrides the model's.
    yes = {"documented": "yes", "keys": ["Escape"], "quote": "Press Esc"}
    out = await _call(
        "answer_questions",
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
            "answer_questions",
            {"run_id": "../etc", "answers": [_ANSWER]},
            raise_on_error=False,
        )
    assert result.is_error


async def test_answer_questions_unknown_run_id_is_a_tool_error(settings):
    msg = await _call_error(
        "answer_questions", {"run_id": "missing-run", "answers": [_ANSWER]}
    )
    assert "No run named" in msg
