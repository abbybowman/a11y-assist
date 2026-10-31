"""run_tt_tests and answer_questions orchestration. Generic over checks.

1. Check the URL against the allowlist before launching anything; a page that
   is never tested is a RunRefused (tool error), not a finding.
2. Record the page live to evidence/page.har.zip (allowlist enforced on every
   top-level navigation and redirect hop).
3. If any selected check uses it, run the shared keyboard walk once
   (walk.py): P1 Tab and P2 Shift+Tab, each from a fresh load of the replay.
4. Each selected check (checks/REGISTRY) collects any extra evidence it needs,
   then its rules module evaluates. A selected test with no check is
   NEEDS_REVIEW "This test could not be performed" (never NOT_TESTED, p. 6).
5. The result carries the full report for the user to save; the run folder is
   kept only for `run_ttl_hours`, to finish open questions.

Nothing here decides an outcome: checks do, from their specs.
"""

from __future__ import annotations

import shutil
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, async_playwright

from a11y_assist.browser import NavigationBlocked, launch_browser
from a11y_assist.capture import record, replay_context
from a11y_assist.checks import REGISTRY, RunContext
from a11y_assist.config import Settings
from a11y_assist.judgment import get_judge, record_answers
from a11y_assist.models import (
    REVIEW_HEAD,
    Answer,
    AnswerResult,
    Finding,
    FindingView,
    Outcome,
    Report,
    RunResult,
    TestId,
    utcnow,
    waiting_head,
)
from a11y_assist.policy import check_url
from a11y_assist.resources.runs import run_uri
from a11y_assist.runlog import RunRecorder, expires_at, prune_runs
from a11y_assist.versions import collect_versions
from a11y_assist.walk import KeyboardWalk, walk_page

NO_SPEC_REASON = "No rules exist for this test yet, so it was not run."

Progress = Callable[[float, float | None, str], Awaitable[None]]


class RunRefused(Exception):
    """The page was never tested (not allowed, or it could not be loaded), or
    the run does not exist. A tool error, not a finding."""


def evidence_name(test_id: TestId) -> str:
    return test_id.value.lower().replace(".", "") + ".json"  # "4.C" -> "4c.json"


def _opener(get_browser, settings: Settings, har: Path, final_url: str, run):
    """A fresh replay context and page for every load (docs/solutions/
    fresh-load-per-probe.md)."""

    async def new_page():
        browser = await get_browser()
        replay = await replay_context(browser, settings, har, run.log)
        page = await replay.context.new_page()
        await replay.guard.goto(page, final_url)
        return replay.context, page

    return new_page


def _context(settings: Settings, run: RunRecorder, get_browser, final_url: str):
    return RunContext(
        new_page=_opener(
            get_browser, settings, run.evidence_dir / "page.har.zip", final_url, run
        ),
        quiet_ms=settings.settle_quiet_ms,
        deadline=time.monotonic() + settings.run_limit_s,
        shots=run.evidence_dir / "shots",
        rel=run.dir,
    )


class _LazyBrowser:
    """Starts Chrome only if a check needs it (resume often does not)."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pw = self._browser = None

    async def get(self) -> Browser:
        if self._browser is None:
            self._pw = await async_playwright().start()
            self._browser = await launch_browser(self._pw, self.settings)
        return self._browser

    async def close(self) -> None:
        if self._browser is not None:
            await self._browser.close()
        if self._pw is not None:
            await self._pw.stop()


def _walk_summary(walk: KeyboardWalk) -> dict[str, Any]:
    def one(p):
        return {"end": p.end, "presses": len(p.steps), "cap": p.cap}

    return {"P1": one(walk.p1), "P2": one(walk.p2)}


def _evidence_uris(run: RunRecorder) -> list[str]:
    files = [run.report_path] + sorted(run.evidence_dir.glob("*.json"))
    files += sorted((run.evidence_dir / "shots").glob("*.png"))
    return [run_uri(run.run_id, run.rel(f)) for f in files if f.exists()]


def _page_text(report: Report, states: dict[TestId, Any]) -> list[dict[str, str]]:
    asking = {q.test_id for q in report.open_questions}
    out: list[dict[str, str]] = []
    for t in asking:
        check = REGISTRY.get(t)
        if check is not None and t in states and hasattr(check, "page_text"):
            out += check.page_text(states[t])
    return out


def _load_states(run: RunRecorder) -> dict[TestId, Any]:
    states = {}
    for t, check in REGISTRY.items():
        path = run.evidence_dir / evidence_name(t)
        if path.exists():
            states[t] = check.state_type.model_validate_json(path.read_text("utf-8"))
    return states


def _evaluate(run: RunRecorder, report: Report, states: dict[TestId, Any]) -> None:
    """Findings and questions for every selected test, from the checks' rules."""
    tests = report_tests(report)
    asked = {q.question_id for q in report.questions}
    findings: list[Finding] = []
    for t in tests:
        check = REGISTRY.get(t)
        if check is None:
            findings.append(Finding.not_performed(t, NO_SPEC_REASON))
            continue
        if t not in states:
            why = "; ".join(report.errors) or "unknown error"
            findings.append(
                Finding.not_performed(t, f"The run did not complete: {why}")
            )
            continue
        rel = f"evidence/{evidence_name(t)}"
        uri = run_uri(run.run_id, rel)
        report.questions += [
            q for q in check.questions(states[t], [uri]) if q.question_id not in asked
        ]
        findings.append(check.evaluate(states[t], [rel]))
    report.findings = findings
    answered = {r.answer.question_id for r in report.answers}
    report.open_questions = [
        q for q in report.questions if q.question_id not in answered
    ]
    # Wording only: while questions are open, say so instead of "a person
    # needs to check it" (the agent usually answers them next).
    for f in report.findings:
        n = sum(q.test_id is f.test_id for q in report.open_questions)
        if (
            n
            and f.outcome is Outcome.NEEDS_REVIEW
            and f.summary.startswith(REVIEW_HEAD)
        ):
            f.summary = waiting_head(n) + f.summary[len(REVIEW_HEAD) :]


def _walk_extras(checks) -> list:
    """The union of the selected checks' walk extras, one per hook name."""
    seen: dict[str, Any] = {}
    for c in checks:
        for factory in c.walk_extras():
            name = factory("P1", None).name
            seen.setdefault(name, factory)
    return list(seen.values())


def report_tests(report: Report) -> list[TestId]:
    return [TestId(t) for t in report.tests]


async def run_tt_tests(
    settings: Settings,
    url: str,
    tests: list[TestId],
    progress: Progress | None = None,
) -> RunResult:
    async def say(step: float, message: str) -> None:
        if progress is not None:
            await progress(step, 4, message)

    decision = check_url(url, settings.allowed_domains, settings.dev_mode)
    if not decision.allowed:
        raise RunRefused(f"URL not allowed: {decision.reason}")
    prune_runs(settings.runs_dir, settings.run_ttl_hours)
    run = RunRecorder(settings.runs_dir)
    selected = [t for t in TestId if t in set(tests)]
    run.log("run_start", target=url, tests=[t.value for t in selected])
    report = Report(
        run_id=run.run_id,
        target=url,
        tests=[t.value for t in selected],
        started_at=utcnow(),
        versions=collect_versions(settings, None),
        judge_backend=settings.judge_backend,
        evidence_dir="evidence",
    )
    checks = [REGISTRY[t] for t in selected if t in REGISTRY]
    states: dict[TestId, Any] = {}
    walk: KeyboardWalk | None = None

    async with async_playwright() as pw:
        browser = await launch_browser(pw, settings)

        async def get_browser() -> Browser:
            return browser

        try:
            report.versions = collect_versions(settings, browser)
            run.log("browser_launched", version=browser.version)
            await say(0, "Recording the page")
            har = run.evidence_dir / "page.har.zip"
            try:
                cap = await record(browser, settings, url, har, run.log)
            except Exception as exc:
                # The page never loaded: a tool error, and nothing is kept.
                shutil.rmtree(run.dir, ignore_errors=True)
                if isinstance(exc, NavigationBlocked):
                    raise RunRefused(str(exc)) from exc
                raise RunRefused(
                    f"The page could not be loaded: {type(exc).__name__}: {exc}"
                ) from exc
            report.final_url = cap.final_url
            run.log("captured", final_url=cap.final_url, redirects=cap.redirects)
            ctx = _context(settings, run, get_browser, cap.final_url)
            if any(c.uses_walk for c in checks):
                await say(1, "Walking the page with Tab and Shift+Tab")
                walk = await walk_page(
                    ctx.new_page,
                    ctx.quiet_ms,
                    ctx.deadline,
                    ctx.shots,
                    ctx.rel,
                    _walk_extras(checks),
                )
                run.write_json(run.evidence_dir / "walk.json", walk)
                run.log("walk", **_walk_summary(walk))
            for c in checks:
                await say(2, f"Checking {c.test_id.value}")
                try:
                    state = await c.collect(ctx, walk)
                except Exception as exc:
                    run.log(
                        "check_error", "error", test=c.test_id.value, error=repr(exc)
                    )
                    report.errors.append(
                        f"{c.test_id.value}: {type(exc).__name__}: {exc}"
                    )
                    continue
                states[c.test_id] = state
                run.write_json(run.evidence_dir / evidence_name(c.test_id), state)
                run.log("collected", test=c.test_id.value)
        finally:
            await browser.close()

    await say(3, "Evaluating")
    report.findings = []
    _evaluate(run, report, states)
    result = await get_judge(settings.judge_backend).judge(report.open_questions)
    report.open_questions = result.pending
    report.finished_at = utcnow()
    run.write_json(run.report_path, report)
    run.log("run_end", status="error" if report.errors else "ok")
    return RunResult(
        run_id=run.run_id,
        target=url,
        final_url=report.final_url,
        tests=report.tests,
        findings=[FindingView.of(f) for f in report.findings],
        open_questions=report.open_questions,
        page_text=_page_text(report, states),
        walk=_walk_summary(walk) if walk else {},
        evidence=_evidence_uris(run),
        expires_at=expires_at(run.dir, settings.run_ttl_hours),
        report=report,
        errors=report.errors,
    )


async def answer_questions(
    settings: Settings, run_id: str, answers: list[Answer]
) -> AnswerResult:
    """Record answers, apply them (pressing documented keys in the recorded
    page where a check needs it), and re-evaluate."""
    try:
        run = RunRecorder.open(settings.runs_dir, run_id)
    except FileNotFoundError as exc:
        raise RunRefused(str(exc)) from exc
    report = Report.model_validate_json(run.report_path.read_text("utf-8"))
    accepted, rejected = record_answers(report, answers)
    states = _load_states(run)
    errors: list[str] = []
    browser = _LazyBrowser(settings)
    try:
        ctx = _context(settings, run, browser.get, report.final_url or report.target)
        for t, state in states.items():
            try:
                errors += await REGISTRY[t].resume(ctx, state, report)
            except Exception as exc:
                errors.append(f"{t.value}: {type(exc).__name__}: {exc}")
            run.write_json(run.evidence_dir / evidence_name(t), state)
    finally:
        await browser.close()
    _evaluate(run, report, states)
    run.write_json(run.report_path, report)
    run.log(
        "answers_recorded",
        "error" if errors else "ok",
        accepted=accepted,
        rejected=rejected,
        errors=errors,
    )
    return AnswerResult(
        run_id=run_id,
        accepted=accepted,
        rejected=rejected,
        findings=[FindingView.of(f) for f in report.findings],
        open_questions=report.open_questions,
        page_text=_page_text(report, states),
        report=report,
        errors=errors,
    )
