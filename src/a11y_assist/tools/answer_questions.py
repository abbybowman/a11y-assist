"""Tool: answer a run's open questions."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from a11y_assist import config
from a11y_assist.judgment import record_answers
from a11y_assist.models import Answer, Report
from a11y_assist.runlog import RunRecorder


def register(mcp: FastMCP) -> None:
    """Register the answer_questions tool with the MCP server."""

    @mcp.tool(
        name="answer_questions",
        annotations={
            "title": "Answer open questions",
            "readOnlyHint": False,  # updates report.json
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def answer_questions(
        run_id: Annotated[
            str,
            Field(
                min_length=1,
                max_length=64,
                pattern=r"^[A-Za-z0-9_-]+$",
                description="run_id returned by run_tt_tests.",
            ),
        ],
        answers: Annotated[
            list[Answer],
            Field(
                min_length=1,
                description=(
                    "One answer per open question: question_id, outcome (must be "
                    "one of the question's allowed_outcomes), rationale citing the "
                    "evidence you inspected, confidence 0-1, and decided_by "
                    "('model' if you are an AI, 'human' if a person decided). "
                    "If unsure, answer NEEDS_REVIEW when allowed."
                ),
            ),
        ],
    ) -> dict[str, Any]:
        """Answer open questions from a run_tt_tests run.

        Each question names a Trusted Tester test ID, a rubric and evidence file
        paths. Inspect the evidence, apply the rubric, and answer. Answers are
        validated (unknown question ids and disallowed outcomes are rejected),
        then recorded in the run's report.json with who decided. Recording an
        answer does not by itself set a test's outcome; the rules spec does that.

        Returns accepted question ids, rejected answers with reasons, and the
        questions still open. Results are agent-assisted and NOT a certified
        Trusted Tester result.
        """
        settings = config.settings
        try:
            run = RunRecorder.open(settings.runs_dir, run_id)
        except FileNotFoundError as exc:
            return {"error": str(exc)}
        report = Report.model_validate_json(run.report_path.read_text("utf-8"))
        accepted, errors = record_answers(report, answers)
        run.write_json(run.report_path, report)
        run.log(
            "answers_recorded",
            "error" if errors else "ok",
            accepted=accepted,
            rejected=errors,
        )
        return {
            "disclaimer": report.disclaimer,
            "run_id": run_id,
            "accepted": accepted,
            "rejected": errors,
            "still_open": [q.question_id for q in report.open_questions],
            "report_path": str(run.report_path),
        }
