"""Tool: wait for a run that tobi_run_tt_tests started and left running."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from tobi508 import config, jobs
from tobi508.inline import with_pictures
from tobi508.models import Outstanding, RunPending, RunResult, TestId
from tobi508.pipeline import (
    RunRefused,
    outstanding,
    record_follow_up,
    take_follow_ups,
)
from tobi508.pipeline import run_tt_tests as run_pipeline
from tobi508.redact import safe_error


def register(mcp: FastMCP) -> None:
    """Register the tobi_run_status tool with the MCP server."""

    @mcp.tool(
        name="tobi_run_status",
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
        finish: Annotated[
            bool,
            Field(
                description="Without a job_id only: also make every follow-up "
                "call the server may make by itself (19.A with the pages it "
                "suggested; all but no_time_limit calls), as new runs, and wait "
                "for them like any run. Calls that need the user's choice are "
                "listed in for_the_user instead. Use it after answering the open "
                "questions, then call again until nothing is left.",
            ),
        ] = False,
        ctx: Context | None = None,
    ) -> RunResult | RunPending | Outstanding:
        """With a job_id: wait for a run that tobi_run_tt_tests started and
        that was still going when that call returned. Waits up to the
        server's call wait (about 45 s) and returns the full result (status
        "done", the same fields as tobi_run_tt_tests) or, if it is still
        going, the same status object again: call this tool again. Never
        start the run again instead. A tool error here is the run's own error.

        Without a job_id: what is left across this session's runs (status
        "outstanding"): each finished run that still has open questions or
        follow_up_calls, with how many, which tests wait for them and the
        calls to make; and the runs still going. Call it before you report to
        the user, and again until nothing is left. Results are
        agent-assisted and NOT a certified Trusted Tester result.
        """
        s = config.settings
        if job_id is None:
            started = []
            if finish:
                started = _start_follow_ups(s)
                tasks = {j.task for j in started if j.task is not None}
                if tasks:
                    await asyncio.wait(tasks, timeout=s.call_wait_s)
            out = outstanding(s, jobs.all_jobs(s))
            out.started = [
                {"job_id": j.id, "target": j.url, "tests": j.tests} for j in started
            ]
            return with_pictures(out, wrap=True)
        job = jobs.get(job_id)
        if job is None:
            raise ToolError(
                "No running or recent run has this job_id. The server keeps a "
                "finished run's job as long as the run, and a restart forgets "
                "every job; start the run again with tobi_run_tt_tests."
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


def _start_follow_ups(s) -> list[jobs.Job]:
    started = []
    for run_id, call in take_follow_ups(s, jobs.all_jobs(s)):
        url = call["url"]
        tests = [TestId(t) for t in call.get("tests") or []]
        if not tests:
            continue
        pages = list(call.get("other_pages") or [])

        def go(p, url=url, tests=tests, pages=pages):
            return run_pipeline(s, url, tests, p, s.no_time_limit_default, pages)

        job = jobs.start(s, url, go)
        job.tests = [t.value for t in tests]
        record_follow_up(s, run_id, call, job.id)
        started.append(job)
    return started
