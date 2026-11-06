"""Tool: wait for a run that a11y_run_tt_tests started and left running."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from a11y_assist import config, jobs
from a11y_assist.inline import with_pictures
from a11y_assist.models import Outstanding, RunPending, RunResult
from a11y_assist.pipeline import RunRefused, outstanding
from a11y_assist.redact import safe_error


def register(mcp: FastMCP) -> None:
    """Register the a11y_run_status tool with the MCP server."""

    @mcp.tool(
        name="a11y_run_status",
        annotations={
            "title": "Wait for a running test run",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def run_status(
        job_id: Annotated[
            str | None,
            Field(
                pattern=r"^job-[0-9a-f]{12}$",
                description='job_id from a result with status "queued" or '
                '"running": wait for that run. Leave it out to list the work '
                "left across this session's runs instead.",
            ),
        ] = None,
        ctx: Context | None = None,
    ) -> RunResult | RunPending | Outstanding:
        """With a job_id: wait for a run that a11y_run_tt_tests started and
        that was still going when that call returned. Waits up to the
        server's call wait (about 45 s) and returns the full result (status
        "done", the same fields as a11y_run_tt_tests) or, if it is still
        going, the same status object again: call this tool again. Never
        start the run again instead. A tool error here is the run's own error.

        Without a job_id: what is left across this session's runs (status
        "outstanding"): each finished run that still has open questions or
        follow_up_calls, with how many, which tests wait for them and the
        calls to make; and the runs still going. Call it before you report to
        the user, and again until nothing is left. Results are
        agent-assisted and NOT a certified Trusted Tester result.
        """
        if job_id is None:
            return outstanding(config.settings, jobs.all_jobs(config.settings))
        job = jobs.get(job_id)
        if job is None:
            raise ToolError(
                "No running or recent run has this job_id. The server keeps a "
                "finished run's job as long as the run, and a restart forgets "
                "every job; start the run again with a11y_run_tt_tests."
            )
        progress = ctx.report_progress if ctx is not None else None
        try:
            return with_pictures(
                await jobs.wait(job, config.settings.call_wait_s, progress), wrap=True
            )
        except RunRefused as exc:
            raise ToolError(str(exc)) from None
        except Exception as exc:
            # One redacted line, no stack trace or call log (redact.py).
            raise ToolError(safe_error(exc)) from None
