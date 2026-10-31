"""Run 4.C on a page end to end, answering open questions with scripted
answers that stand in for the judge. The answers are test data (what a correct
judge would say about the page), never outcomes; they live in the test files,
never in a page."""

from __future__ import annotations

from typing import Any

from a11y_assist.judgment import record_answers
from a11y_assist.models import Answer, J1Answer, J2Answer, Report, TestId
from a11y_assist.pipeline import resume_4c, run_tt_tests
from a11y_assist.runlog import RunRecorder

NO_DOCS = {"documented": "no"}


async def run_4c(
    settings, url: str, j1: dict | None = None, j2: dict | None = None
) -> dict[str, Any]:
    out = await run_tt_tests(settings, url, [TestId.T4C])
    assert out["errors"] == [], out["errors"]
    run = RunRecorder.open(settings.runs_dir, out["run_id"])
    for _ in range(3):
        report = Report.model_validate_json(run.report_path.read_text("utf-8"))
        if not report.open_questions:
            break
        answers = []
        for q in report.open_questions:
            if q.kind == "J2":
                assert j2 is not None, (
                    f"{url}: J2 asked but the test gives no J2 answer"
                )
            for n in (1, 2, 3):
                answers.append(
                    Answer(
                        question_id=q.question_id,
                        sample=n,
                        j1=J1Answer(**(j1 or NO_DOCS)) if q.kind == "J1" else None,
                        j2=J2Answer(**j2) if q.kind == "J2" else None,
                        rationale="scripted test answer",
                    )
                )
        _, errors = record_answers(report, answers)
        errors += await resume_4c(settings, run, report)
        assert errors == [], errors
        run.write_json(run.report_path, report)
    report = Report.model_validate_json(run.report_path.read_text("utf-8"))
    [finding] = [f for f in report.findings if f.test_id is TestId.T4C]
    return {"finding": finding, "open": [q.question_id for q in report.open_questions]}


def instance_rows(finding) -> list[str]:
    return sorted(r.split(":")[1] for r in finding.rows if ":" in r)
