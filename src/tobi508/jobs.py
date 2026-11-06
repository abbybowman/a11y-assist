"""Runs that outlive one tool call (post-round 1 fixes 2 and 5, option C).

A tool call starts a run as a job and waits for it up to `call_wait_s`
(default 45 s, under the common 60 s MCP client timeout). A run that
finishes in time is returned as before; otherwise the call returns the job
id and the progress so far, and tobi_run_status waits again. The run goes
on in the server meanwhile, within its own time limit (`run_limit_s` and
the rest, unchanged), so a client's timeout or background move no longer
loses it.

At most `max_concurrent_runs` runs use a browser at once. A job waiting for
a slot has not started its run yet, so the wait does not use its time limit
(the pipeline starts the clock when it is called).

Jobs live in this process's memory: a server restart loses running jobs
and the record of finished ones (a finished run's folder and report stay
until `run_ttl_hours`; an unfinished one's folder is pruned with them). No
outcome is decided here.
"""

from __future__ import annotations

import asyncio
import secrets
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from tobi508.config import Settings
from tobi508.models import RunPending, RunResult

ProgressFn = Callable[[float, float | None, str], Awaitable[None]]


@dataclass
class Job:
    id: str
    url: str
    tests: list[str] = field(default_factory=list)
    created: float = field(default_factory=time.monotonic)
    started: float | None = None  # when it got a browser slot
    finished: float | None = None
    step: float = 0.0
    message: str = "Waiting for a free browser slot"
    task: asyncio.Task | None = None
    waiters: list[ProgressFn] = field(default_factory=list)

    async def progress(self, step: float, total: float | None, message: str) -> None:
        self.step, self.message = step, message
        for w in list(self.waiters):
            try:
                await w(step, total, message)
            except Exception:
                # A waiter whose call has ended: its client is gone.
                if w in self.waiters:
                    self.waiters.remove(w)


_JOBS: dict[str, Job] = {}
_SLOTS: dict[tuple[int, int], asyncio.Semaphore] = {}


def _slots(n: int) -> asyncio.Semaphore:
    key = (id(asyncio.get_running_loop()), n)
    if key not in _SLOTS:
        _SLOTS[key] = asyncio.Semaphore(n)
    return _SLOTS[key]


def _prune(settings: Settings) -> None:
    now = time.monotonic()
    for jid, j in list(_JOBS.items()):
        if j.finished is not None and now - j.finished > settings.job_keep_s:
            del _JOBS[jid]


def start(
    settings: Settings,
    url: str,
    run: Callable[[ProgressFn], Awaitable[RunResult]],
) -> Job:
    """Start `run` (the pipeline call, given a progress function) as a job."""
    _prune(settings)
    job = Job(id="job-" + secrets.token_hex(6), url=url)
    slots = _slots(settings.max_concurrent_runs)

    async def go() -> RunResult:
        try:
            async with slots:
                job.started = time.monotonic()
                await job.progress(0, 4, "Starting")
                return await run(job.progress)
        finally:
            job.finished = time.monotonic()
            job.waiters.clear()

    job.task = asyncio.get_running_loop().create_task(go())
    _JOBS[job.id] = job
    return job


def get(job_id: str) -> Job | None:
    return _JOBS.get(job_id)


async def wait(
    job: Job, seconds: float, progress: ProgressFn | None = None
) -> RunResult | RunPending:
    """The job's result if it ends within `seconds` (its error is raised),
    else where it is. Waiting never cancels the job."""
    assert job.task is not None
    if progress is not None and not job.task.done():
        job.waiters.append(progress)
    try:
        await asyncio.wait({job.task}, timeout=seconds)
    finally:
        if progress in job.waiters:
            job.waiters.remove(progress)
    if job.task.done():
        return job.task.result()
    return pending(job, seconds)


def pending(job: Job, wait_s: float) -> RunPending:
    now = time.monotonic()
    queued = job.started is None
    return RunPending(
        job_id=job.id,
        target=job.url,
        status="queued" if queued else "running",
        seconds_waiting=round((job.started or now) - job.created, 1),
        seconds_running=0.0 if queued else round(now - job.started, 1),
        progress=job.message,
        next_step=(
            "The run is still going on in the server; nothing is lost. Call "
            f"tobi_run_status with job_id {job.id!r} to wait for it again (each "
            f"call waits up to {int(wait_s)} s). Do not start the same run "
            "again, and do not end your turn while it runs: you would lose "
            "its result."
        ),
    )


def all_jobs(settings: Settings) -> list[Job]:
    """This session's jobs still kept, oldest first."""
    _prune(settings)
    return sorted(_JOBS.values(), key=lambda j: j.created)


def running() -> list[dict[str, Any]]:
    """Jobs not finished yet (for tests and diagnostics)."""
    return [{"id": j.id, "url": j.url} for j in _JOBS.values() if j.finished is None]
