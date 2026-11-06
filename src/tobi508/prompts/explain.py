"""Prompt: explain TT tests, before or after running them.

Clients show MCP prompts as commands (in Claude Code: /mcp__tobi508__explain).
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

from tobi508 import config, explain


def build(about: str | None = None, run_id: str | None = None) -> str:
    return explain.build_for_run(config.settings, about, run_id)


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
                description="A run_id from tobi_run_tt_tests, to explain its results.",
            ),
        ] = None,
    ) -> str:
        return build(about, run_id)
