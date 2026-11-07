"""Tool: explain TT tests, in general or as a run found them."""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from tobi508 import config, explain


def register(mcp: FastMCP) -> None:
    """Register the tobi_explain tool with the MCP server."""

    @mcp.tool(
        name="tobi_explain",
        annotations={
            "title": "Explain tests or a run's results",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def tobi_explain(
        about: Annotated[
            str | None,
            Field(
                max_length=200,
                description='Test IDs ("4.C", or several: "4.C, 4.D"), a WCAG '
                'criterion ("2.1.2"), a test name or words ("keyboard trap"). '
                "Leave empty with run_id for every result of the run.",
            ),
        ] = None,
        run_id: Annotated[
            str | None,
            Field(
                pattern=r"^[A-Za-z0-9_-]{1,64}$",
                description="A run_id from tobi_run_tt_tests: explain what that "
                "run found for the tests in `about` (or all of them).",
            ),
        ] = None,
    ) -> str:
        """The detail behind results, and what tests check, from the source.

        Without run_id: what a test checks, who it helps, how a Trusted Tester
        tests it, what this tool does for it, and the TT text and W3C links.
        With run_id: for each test asked about, the full plain-language
        summary, why it was decided (the technical reasoning and the rule
        trail), the places on the page, what can still change it, and the
        links to explain how to fix it. Results carry one line per finding;
        call this when you report to the user or the user asks why. The
        returned text gives the task and the material: explain from it, not
        from memory. Results are agent-assisted and NOT a certified Trusted
        Tester result.
        """
        return explain.build_for_run(config.settings, about, run_id)
