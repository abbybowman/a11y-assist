"""Prompt: explain TT tests, before or after running them.

Clients show MCP prompts as commands (in Claude Code: /mcp__a11y-assist__explain).
The material comes from explain.py, which failure reports will reuse.

  explain about="4.C"                  what the test checks, before a run
  explain about="keyboard trap"        the same, found by words
  explain about="1.3.1"                every TT test for a WCAG criterion
  explain run_id=<id>                  every result of a run, failures first
  explain about="4.C" run_id=<id>      one result of a run
"""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from a11y_assist import config, explain
from a11y_assist.models import Report
from a11y_assist.runlog import RunRecorder


def build(about: str | None = None, run_id: str | None = None) -> str:
    if not run_id:
        return explain.build(about)
    try:
        run = RunRecorder.open(config.settings.runs_dir, run_id)
        report = Report.model_validate_json(run.report_path.read_text("utf-8"))
    except (FileNotFoundError, ValueError):
        return (
            f"Run {run_id!r} is no longer on the server (runs expire). If the user "
            "saved its report (report.json), read that file and explain its "
            "findings using the material below; otherwise explain the test in "
            "general.\n\n" + explain.build(about)
        )
    return explain.build(about, report)


def register(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="explain",
        description="Explain Trusted Tester tests in plain language: what a test "
        "checks before you run it, or what a run found and how to fix it. Give a "
        "test ID, WCAG criterion, test name or a few words, and/or a run_id.",
    )
    def explain_prompt(
        about: Annotated[
            str | None,
            Field(
                default=None,
                max_length=200,
                description='A test ID ("4.C"), WCAG criterion ("2.1.2"), test name '
                'or words ("keyboard trap"). Leave empty with run_id for every '
                "result of the run.",
            ),
        ] = None,
        run_id: Annotated[
            str | None,
            Field(
                default=None,
                pattern=r"^[A-Za-z0-9_-]{1,64}$",
                description="A run_id from run_tt_tests, to explain its results.",
            ),
        ] = None,
    ) -> str:
        return build(about, run_id)
