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
5. The result links the full report (`report_uri`, a run:// resource) for the
   user to save; the run folder is kept only for `run_ttl_hours`, to finish
   open questions and serve evidence.

Nothing here decides an outcome: checks do, from their specs.
"""

from __future__ import annotations

import asyncio
import math
import shutil
import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from playwright.async_api import Browser, async_playwright

from a11y_assist.browser import NavigationBlocked, launch_browser
from a11y_assist.capture import record, replay_context
from a11y_assist.checks import REGISTRY, RunContext
from a11y_assist.checks.base import PageRef
from a11y_assist.config import Settings
from a11y_assist.egress import EgressProxy
from a11y_assist.judgment import get_judge, record_answers
from a11y_assist.models import (
    REVIEW_HEAD,
    Answer,
    AnswerResult,
    Finding,
    FindingView,
    OtherPage,
    Outcome,
    Report,
    RunResult,
    TestId,
    utcnow,
    waiting_head,
)
from a11y_assist.policy import check_url
from a11y_assist.redact import safe_error
from a11y_assist.resources.runs import run_uri
from a11y_assist.runlog import RunRecorder, expires_at, prune_runs
from a11y_assist.traverse import Pace, ReplayPlan, TooManyItems, WalkTooLong, metered
from a11y_assist.versions import collect_versions
from a11y_assist.walk import KeyboardWalk, walk_page

NO_SPEC_REASON = "No rules exist for this test yet, so it was not run."

# The run limit (4.C spec section 2, Run limits). Checks stop starting new work
# RESERVE_S before the limit; a phase still running HARD_MARGIN_S before it is
# cancelled (its tests are NEEDS REVIEW), leaving time to write the report.
RESERVE_S = 10
HARD_MARGIN_S = 2
TIME_NOTE = (
    "The run reached its time limit ({limit} s) before every test finished; "
    "what was not finished is NEEDS REVIEW. To finish it, run again with "
    "no_time_limit=true (the call can then take several minutes)."
)

Progress = Callable[[float, float | None, str], Awaitable[None]]

# Other pages of the same site a caller may name (9.A-9.C; Abby, 2026-11-02).
OTHER_PAGES_MAX = 5


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


def _context(
    settings: Settings,
    run: RunRecorder,
    get_browser,
    final_url: str,
    deadline: float,
):
    return RunContext(
        new_page=_opener(
            get_browser, settings, run.evidence_dir / "page.har.zip", final_url, run
        ),
        quiet_ms=settings.settle_quiet_ms,
        deadline=deadline,
        shots=run.evidence_dir / "shots",
        rel=run.dir,
        third_party=settings.third_party_dir,
    )


def _soft_deadline(
    start: float, settings: Settings, no_time_limit: bool, pages: int = 0
) -> float:
    if no_time_limit:
        return math.inf
    return start + _limit(settings, pages) - RESERVE_S


def _limit(settings: Settings, pages: int) -> int:
    """The run limit: `run_limit_s`, plus `other_page_s` for each other page
    recorded (Abby, 2026-11-02: the limit is set per page)."""
    return settings.run_limit_s + pages * settings.other_page_s


def uses_pages(check) -> bool:
    return bool(getattr(check, "uses_pages", False))


def needs_walk(check, ctx: RunContext) -> bool:
    """A check that compares pages needs nothing (not even the walk) when no
    other pages were given: it is not performed."""
    return check.uses_walk and not (uses_pages(check) and not ctx.pages)


def _site(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    return parts.scheme.lower(), (parts.hostname or "").lower().rstrip(".")


def _same_site(a: str, b: str) -> bool:
    """Same host (and both file:// in dev mode), the rule for other pages."""
    sa, sb = _site(a), _site(b)
    if "file" in (sa[0], sb[0]):
        return sa[0] == sb[0] == "file"
    return sa[1] == sb[1] and sa[1] != ""


def check_other_pages(settings: Settings, url: str, other: list[str]) -> list[str]:
    """The caller's other pages, deduplicated in order; raises RunRefused if
    one is not allowed, not on the tested page's host, or is the page itself.
    Page content never adds to this list (CLAUDE.md principle 5)."""
    out: list[str] = []
    for u in other:
        if u not in out:
            out.append(u)
    if len(out) > OTHER_PAGES_MAX:
        raise RunRefused(f"At most {OTHER_PAGES_MAX} other pages can be compared.")
    for i, u in enumerate(out, 1):
        d = check_url(u, settings.allowed_domains, settings.dev_mode)
        if not d.allowed:
            raise RunRefused(f"Other page {i} not allowed: {d.reason}")
        if not _same_site(u, url):
            raise RunRefused(
                f"Other page {i} is not on the tested page's host; other pages "
                "must be pages of the same site."
            )
        if u.split("#")[0] == url.split("#")[0]:
            raise RunRefused(f"Other page {i} is the tested page itself.")
    return out


def _live_recorder(browser, settings, run, report, proxy, final_url, get_browser):
    """19.A's live site search (CLAUDE.md, Abby 2026-11-02): one more page
    recorded live, allowlisted on every hop and on the tested page's host."""

    async def record_live(url: str) -> PageRef:
        d = check_url(url, settings.allowed_domains, settings.dev_mode)
        if not d.allowed or not _same_site(url, final_url):
            raise ValueError("not on the tested page's host or not allowed")
        n = len(report.live_pages) + 1
        rel = f"evidence/pages/live{n}.har.zip"
        (run.dir / rel).parent.mkdir(parents=True, exist_ok=True)
        t1 = time.monotonic()
        lc = await record(browser, settings, url, run.dir / rel, run.log, proxy)
        if not _same_site(lc.final_url, final_url):
            raise ValueError("it ended on another host after redirects")
        report.live_pages.append(
            OtherPage(n=n, url=url, final_url=lc.final_url, har=rel)
        )
        run.log("captured_live", n=n, seconds=round(time.monotonic() - t1, 2))
        return PageRef(
            n=100 + n,
            url=url,
            final_url=lc.final_url,
            new_page=_opener(get_browser, settings, run.dir / rel, lc.final_url, run),
        )

    return record_live


def _page_refs(get_browser, settings: Settings, run, report: Report) -> list[PageRef]:
    return [
        PageRef(
            n=p.n,
            url=p.url,
            final_url=p.final_url or p.url,
            new_page=_opener(
                get_browser, settings, run.dir / p.har, p.final_url or p.url, run
            ),
        )
        for p in report.other_pages
    ]


async def _bounded(aw, hard: float):
    """Await `aw`, cancelling it at `hard` (TimeoutError)."""
    if hard == math.inf:
        return await aw
    left = hard - time.monotonic()
    if left <= 0:
        aw.close()
        raise TimeoutError
    return await asyncio.wait_for(aw, left)


def _too_long(exc: WalkTooLong, limit: int) -> str:
    minutes = max(1, round(exc.estimate_s / 60))
    if isinstance(exc, TooManyItems):
        c = exc.cap
        return (
            f"This page has {exc.count} {c.noun}; one call checks at most "
            f"{c.limit} for test {c.test}, so most of them would be left for a "
            f"person. Nothing was tested. To test them all, call again with "
            f"no_time_limit=true (about {minutes} min or more), or leave {c.test} "
            "out of the tests, or test a smaller page."
        )
    return (
        f"This page has about {exc.candidates} places the keyboard can reach. At "
        f"the pace of the first {exc.presses} key presses, walking it with Tab "
        f"and Shift+Tab alone would take about {minutes} min, more than one call "
        f"allows ({limit} s). Nothing was tested. To test it anyway, call again "
        "with no_time_limit=true (the call will take that long or more), or "
        "test a smaller page."
    )


class _LazyBrowser:
    """Starts Chrome only if a check needs it (resume often does not)."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pw = self._browser = self._proxy = None

    async def get(self) -> Browser:
        if self._browser is None:
            self._proxy = await EgressProxy(self.settings).__aenter__()
            self._pw = await async_playwright().start()
            self._browser = await launch_browser(self._pw, self.settings, self._proxy)
        return self._browser

    async def close(self) -> None:
        if self._browser is not None:
            await self._browser.close()
        if self._pw is not None:
            await self._pw.stop()
        if self._proxy is not None:
            await self._proxy.__aexit__(None, None, None)


def _blocked_hosts(proxy: EgressProxy) -> str:
    """Hosts the egress proxy refused for their address (host, port and
    reason only)."""
    seen: dict[str, str] = {}
    for r in proxy.refused:
        if not r["reason"].startswith("resolves to"):
            continue
        seen.setdefault(f"{r['host']}:{r['port']}", r["reason"])
    return "; ".join(f"{h} ({why})" for h, why in seen.items())


def _walk_summary(walk: KeyboardWalk) -> dict[str, Any]:
    def one(p):
        return {"end": p.end, "presses": len(p.steps), "cap": p.cap}

    return {"P1": one(walk.p1), "P2": one(walk.p2)}


def _evidence_uris(run: RunRecorder) -> list[str]:
    files = [run.report_path] + sorted(run.evidence_dir.glob("*.json"))
    files += sorted((run.evidence_dir / "shots").glob("*.png"))
    return [run_uri(run.run_id, run.rel(f)) for f in files if f.exists()]


def _shared_inputs(report: Report, states: dict[TestId, Any]) -> dict[str, Any]:
    """Evidence the open questions share, once per result (a check's optional
    `shared_inputs(state)`), limited to the keys an open question names."""
    wanted = {k for q in report.open_questions for k in q.shared}
    out: dict[str, Any] = {}
    for t in {q.test_id for q in report.open_questions}:
        check = REGISTRY.get(t)
        if check is not None and t in states and hasattr(check, "shared_inputs"):
            out.update(
                {k: v for k, v in check.shared_inputs(states[t]).items() if k in wanted}
            )
    return out


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
    no_time_limit: bool = False,
    other_pages: list[str] | None = None,
) -> RunResult:
    async def say(step: float, message: str) -> None:
        if progress is not None:
            await progress(step, 4, message)

    t_start = time.monotonic()
    decision = check_url(url, settings.allowed_domains, settings.dev_mode)
    if not decision.allowed:
        raise RunRefused(f"URL not allowed: {decision.reason}")
    others = check_other_pages(settings, url, other_pages or [])
    prune_runs(settings.runs_dir, settings.run_ttl_hours)
    run = RunRecorder(settings.runs_dir)
    selected = [t for t in TestId if t in set(tests)]
    run.log("run_start", target=url, tests=[t.value for t in selected])
    report = Report(
        run_id=run.run_id,
        target=url,
        tests=[t.value for t in selected],
        started_at=utcnow(),
        versions=collect_versions(settings, None, no_time_limit),
        judge_backend=settings.judge_backend,
        evidence_dir="evidence",
    )
    checks = [REGISTRY[t] for t in selected if t in REGISTRY]
    # Other pages are recorded only for a check that compares pages.
    if others and not any(uses_pages(c) for c in checks):
        report.errors.append(
            "The other pages were not used: none of the selected tests compares pages."
        )
        others = []
    soft = _soft_deadline(t_start, settings, no_time_limit, len(others))
    hard = (
        math.inf
        if no_time_limit
        else t_start + _limit(settings, len(others)) - HARD_MARGIN_S
    )
    # Checks whose replays others reuse (4.D's arrows, 4.F's Enter presses,
    # for 4.A) collect first; 5.A and 5.C (shares -1) collect last, after the
    # replays that may reveal fields for them. Findings keep the report's order.
    checks.sort(key=lambda c: -getattr(c, "shares", 0))
    states: dict[TestId, Any] = {}
    walk: KeyboardWalk | None = None

    async with EgressProxy(settings, log=run.log) as proxy, async_playwright() as pw:
        browser = await launch_browser(pw, settings, proxy)

        async def get_browser() -> Browser:
            return browser

        try:
            report.versions = collect_versions(settings, browser, no_time_limit)
            run.log("browser_launched", version=browser.version)
            await say(0, "Recording the page")
            har = run.evidence_dir / "page.har.zip"
            t0 = time.monotonic()
            try:
                cap = await _bounded(
                    record(browser, settings, url, har, run.log, proxy), hard
                )
            except Exception as exc:
                # The page never loaded: a tool error, and nothing is kept.
                shutil.rmtree(run.dir, ignore_errors=True)
                if isinstance(exc, TimeoutError):
                    raise RunRefused(
                        "The page could not be recorded within the time limit."
                    ) from None
                if isinstance(exc, NavigationBlocked):
                    raise RunRefused(str(exc)) from exc
                raise RunRefused(
                    f"The page could not be loaded: {safe_error(exc)}"
                ) from None
            report.final_url = cap.final_url
            pages_cut = ""
            for i, other in enumerate(others, 1):
                await say(0.5, f"Recording other page {i} of {len(others)}")
                rel = f"evidence/pages/p{i}.har.zip"
                t1 = time.monotonic()
                (run.dir / rel).parent.mkdir(parents=True, exist_ok=True)
                try:
                    # Each other page records within its own share of the
                    # limit, so a slow one cannot eat the other tests' time.
                    share = hard if no_time_limit else t1 + settings.other_page_s
                    oc = await _bounded(
                        record(browser, settings, other, run.dir / rel, run.log, proxy),
                        min(hard, share),
                    )
                except TimeoutError:
                    # The single-page tests still run; the tests that compare
                    # pages are not performed rather than run on fewer pages.
                    pages_cut = (
                        f"Other page {i} could not be recorded within its "
                        f"{settings.other_page_s} s, so the tests that compare "
                        "pages were not performed. To run them, give fewer other "
                        "pages, or run again with no_time_limit=true."
                    )
                    run.log("captured_other", "error", n=i, error="time limit")
                    report.errors.append(pages_cut)
                    report.other_pages = []
                    break
                except Exception as exc:
                    shutil.rmtree(run.dir, ignore_errors=True)
                    if isinstance(exc, NavigationBlocked):
                        raise RunRefused(f"Other page {i}: {exc}") from exc
                    raise RunRefused(
                        f"Other page {i} could not be loaded: {safe_error(exc)}"
                    ) from None
                if not _same_site(oc.final_url, cap.final_url):
                    shutil.rmtree(run.dir, ignore_errors=True)
                    raise RunRefused(
                        f"Other page {i} ended on another host after redirects; "
                        "other pages must be pages of the same site."
                    )
                report.other_pages.append(
                    OtherPage(n=i, url=other, final_url=oc.final_url, har=rel)
                )
                run.log(
                    "captured_other",
                    n=i,
                    final_url=oc.final_url,
                    seconds=round(time.monotonic() - t1, 2),
                )
            blocked = _blocked_hosts(proxy)
            if blocked:
                # The page loaded without these parts; the findings cover only
                # what loaded. A note, not an outcome.
                report.errors.append(
                    "Some page content was not loaded because its host resolves "
                    f"to a non-public address: {blocked}"
                )
            run.log(
                "captured",
                final_url=cap.final_url,
                redirects=cap.redirects,
                seconds=round(time.monotonic() - t0, 2),
            )
            ctx = _context(settings, run, get_browser, cap.final_url, soft)
            ctx.selected = frozenset(c.test_id.value for c in checks)
            ctx.pages = _page_refs(get_browser, settings, run, report)
            ctx.record_live = _live_recorder(
                browser, settings, run, report, proxy, cap.final_url, get_browser
            )
            if any(needs_walk(c, ctx) for c in checks):
                await say(1, "Walking the page with Tab and Shift+Tab")
                caps = [c.cap for c in checks if getattr(c, "cap", None)]
                pace = None if no_time_limit else Pace(soft, caps=caps)
                try:
                    with metered() as cost:
                        walk = await _bounded(
                            walk_page(
                                ctx.new_page,
                                ctx.quiet_ms,
                                ctx.deadline,
                                ctx.shots,
                                ctx.rel,
                                _walk_extras(checks),
                                pace,
                            ),
                            hard,
                        )
                except WalkTooLong as exc:
                    # Stop and say so instead of running out of time: the
                    # caller chooses no_time_limit or another page.
                    shutil.rmtree(run.dir, ignore_errors=True)
                    raise RunRefused(_too_long(exc, settings.run_limit_s)) from None
                except TimeoutError:
                    report.errors.append(
                        "The keyboard walk did not finish within the time limit."
                    )
                    run.log("walk", "error", error="time limit", cost=asdict(cost))
                if walk is not None:
                    ctx.plan = ReplayPlan.of(walk.p1, walk.p2)
                    run.write_json(run.evidence_dir / "walk.json", walk)
                    run.log("walk", **_walk_summary(walk), cost=asdict(cost))
            for c in checks:
                if pages_cut and uses_pages(c):
                    continue  # NEEDS REVIEW, not performed: pages_cut says why
                if needs_walk(c, ctx) and walk is None:
                    continue  # NEEDS REVIEW: the run did not complete (errors say why)
                await say(2, f"Checking {c.test_id.value}")
                try:
                    with metered() as cost:
                        state = await _bounded(c.collect(ctx, walk), hard)
                except TimeoutError:
                    msg = "the run reached its time limit before this test finished"
                    run.log("check_error", "error", test=c.test_id.value, error=msg)
                    report.errors.append(f"{c.test_id.value}: {msg}")
                    continue
                except Exception as exc:
                    err = safe_error(exc)
                    run.log("check_error", "error", test=c.test_id.value, error=err)
                    report.errors.append(f"{c.test_id.value}: {err}")
                    continue
                states[c.test_id] = state
                run.write_json(run.evidence_dir / evidence_name(c.test_id), state)
                run.log("collected", test=c.test_id.value, cost=asdict(cost))
            # Only when something was cut short: work that finished inside the
            # reserve needs no note.
            walk_cut = walk is not None and "time" in (walk.p1.end, walk.p2.end)
            hard_cut = any("time limit" in e for e in report.errors)
            if ctx.timed_out or walk_cut or hard_cut:
                report.errors.append(
                    TIME_NOTE.format(limit=_limit(settings, len(others)))
                )
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
        shared_inputs=_shared_inputs(report, states),
        walk=_walk_summary(walk) if walk else {},
        evidence=_evidence_uris(run),
        expires_at=expires_at(run.dir, settings.run_ttl_hours),
        report=report,
        report_uri=run_uri(run.run_id, run.rel(run.report_path)),
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
        no_limit = bool(report.versions.run_settings.get("no_time_limit"))
        ctx = _context(
            settings,
            run,
            browser.get,
            report.final_url or report.target,
            _soft_deadline(time.monotonic(), settings, no_limit),
        )
        ctx.pages = _page_refs(browser.get, settings, run, report)
        walk_path = run.evidence_dir / "walk.json"
        if walk_path.exists():
            w = KeyboardWalk.model_validate_json(walk_path.read_text("utf-8"))
            ctx.plan = ReplayPlan.of(w.p1, w.p2)
        for t, state in states.items():
            try:
                errors += await REGISTRY[t].resume(ctx, state, report)
            except Exception as exc:
                errors.append(f"{t.value}: {safe_error(exc)}")
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
        shared_inputs=_shared_inputs(report, states),
        report=report,
        report_uri=run_uri(run.run_id, run.rel(run.report_path)),
        errors=errors,
    )
