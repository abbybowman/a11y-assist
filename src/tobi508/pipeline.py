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
import json
import math
import shutil
import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from playwright.async_api import Browser, async_playwright

from tobi508 import motion, pagecache, scrt
from tobi508.browser import (
    MOTION_BROWSER,
    NavigationBlocked,
    launch_browser,
    launch_for,
    replay_browser_name,
    replay_in_full_chromium,
)
from tobi508.capture import Capture, replay_context
from tobi508.checks import REGISTRY, RunContext
from tobi508.checks.base import PageRef
from tobi508.config import Settings
from tobi508.egress import EgressProxy
from tobi508.frozen import NotFrozen, obtain
from tobi508.judgment import get_judge, has_image, record_answers
from tobi508.models import (
    REVIEW_HEAD,
    Answer,
    AnswerResult,
    Finding,
    FindingView,
    OpenQuestion,
    OtherPage,
    Outcome,
    Outstanding,
    OutstandingRun,
    Remaining,
    Report,
    RunResult,
    TestId,
    utcnow,
    waiting_head,
)
from tobi508.motion import MOTION_INIT_JS
from tobi508.policy import check_url
from tobi508.redact import safe_error
from tobi508.resources.runs import run_uri
from tobi508.runlog import RunRecorder, expires_at, prune_runs
from tobi508.traverse import Pace, ReplayPlan, TooManyItems, WalkTooLong, metered
from tobi508.versions import collect_versions, measure_display
from tobi508.walk import KeyboardWalk, walk_page

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
# The cap keeps one call within its time limit; a caller who turns the limit
# off may name more (Abby, 2026-11-03), up to a bound on the input itself.
OTHER_PAGES_MAX = 5
OTHER_PAGES_NO_LIMIT_MAX = 50


class RunRefused(Exception):
    """The page was never tested (not allowed, or it could not be loaded), or
    the run does not exist. A tool error, not a finding."""


def evidence_name(test_id: TestId) -> str:
    return test_id.value.lower().replace(".", "") + ".json"  # "4.C" -> "4c.json"


def _opener(
    get_browser,
    settings: Settings,
    har: Path,
    final_url: str,
    run,
    frames: list[str],
    init_scripts: tuple[str, ...] = (),
    autoplay: bool = False,
    ignore: SettleIgnore | None = None,
):
    """A fresh replay context and page for every load (docs/solutions/
    fresh-load-per-probe.md). A page with cross-site frames replays in full
    Chromium (browser.replay_in_full_chromium). `init_scripts`: extra hooks;
    `autoplay`: pass T's browser (full Chromium, headless, autoplay allowed;
    plan Q1 and Q11)."""
    full = autoplay or replay_in_full_chromium(settings, frames)

    async def new_page():
        browser = await get_browser(full, autoplay)
        replay = await replay_context(
            browser, settings, har, run.log, init_scripts=init_scripts
        )
        page = await replay.context.new_page()
        await replay.guard.goto(page, final_url)
        if ignore is not None:
            await ignore.join(page)
        return replay.context, page

    return new_page


class SettleIgnore:
    """Content pass T found still changing by itself (a ticker, a carousel):
    the settle rule stops waiting on its DOM changes (traverse.INIT_JS
    setIgnore; Abby, 2026-11-04, T1 (b)). Pages of the tested page join it;
    when pass T ends, the list goes to every page still open (the walk's
    included) and to each page opened after."""

    def __init__(self) -> None:
        self.sels: dict[str, list[str]] = {}
        self.pages: list = []

    async def _apply(self, page) -> None:
        for frame in page.frames:
            key = "" if frame == page.main_frame else frame.url
            sels = self.sels.get(key)
            if not sels:
                continue
            try:
                await frame.evaluate(
                    "(s) => window.__a11yLog && window.__a11yLog.setIgnore(s)", sels
                )
            except Exception:
                continue

    async def join(self, page) -> None:
        self.pages = [p for p in self.pages if not p.is_closed()]
        self.pages.append(page)
        if self.sels:
            await self._apply(page)

    async def set(self, sels: dict[str, list[str]]) -> None:
        self.sels = sels
        for page in [p for p in self.pages if not p.is_closed()]:
            await self._apply(page)


async def _watch_then_ignore(ctx, run, extend=None, keep_shots=True):
    mp = await motion.collect(ctx, keep_shots)
    sels = motion.settle_ignore(mp)
    if sels and ctx.settle_ignore is not None:
        await ctx.settle_ignore.set(sels)
        run.log("settle_ignore", regions=sum(len(v) for v in sels.values()))
    if sels and extend is not None:
        extend()
    return mp


def _context(
    settings: Settings,
    run: RunRecorder,
    get_browser,
    final_url: str,
    deadline: float,
    frames: list[str],
):
    har = run.evidence_dir / "page.har.zip"
    ignore = SettleIgnore()
    return RunContext(
        new_page=_opener(
            get_browser, settings, har, final_url, run, frames, ignore=ignore
        ),
        # Pass T (2.A-2.D) in its own browser: full Chromium, headless, with
        # autoplay allowed (plan Q1, Q11), so the walk's browser is unchanged.
        open_motion=_opener(
            get_browser,
            settings,
            har,
            final_url,
            run,
            frames,
            (MOTION_INIT_JS,),
            autoplay=True,
            ignore=ignore,
        ),
        settle_ignore=ignore,
        motion_browser=MOTION_BROWSER,
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


def check_other_pages(
    settings: Settings, url: str, other: list[str], no_time_limit: bool = False
) -> list[str]:
    """The caller's other pages, deduplicated in order; raises RunRefused if
    one is not allowed, not on the tested page's host, or is the page itself.
    Page content never adds to this list (CLAUDE.md principle 5)."""
    out: list[str] = []
    for u in other:
        if u not in out:
            out.append(u)
    if len(out) > OTHER_PAGES_NO_LIMIT_MAX:
        raise RunRefused(
            f"At most {OTHER_PAGES_NO_LIMIT_MAX} other pages can be compared in "
            "one call."
        )
    if len(out) > OTHER_PAGES_MAX and not no_time_limit:
        raise RunRefused(
            f"At most {OTHER_PAGES_MAX} other pages can be compared within the "
            "time limit. To compare more, run again with no_time_limit=true "
            f"(each page adds about {settings.other_page_s} s)."
        )
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
        # The same share a caller-named page gets, so a slow search cannot
        # take the later checks' time (19.A W4 on a timeout).
        lc = await asyncio.wait_for(
            obtain(browser, settings, url, run.dir / rel, run.log, proxy, tested=False),
            settings.other_page_s,
        )
        if not _same_site(lc.final_url, final_url):
            raise ValueError("it ended on another host after redirects")
        report.live_pages.append(
            OtherPage(
                n=n,
                url=url,
                final_url=lc.final_url,
                har=rel,
                cross_site_frames=lc.cross_site_frames,
                frozen=lc.frozen if settings.frozen_pages_dir else None,
                replay_browser=replay_browser_name(settings, lc.cross_site_frames),
            )
        )
        run.log("captured_live", n=n, seconds=round(time.monotonic() - t1, 2))
        return PageRef(
            n=100 + n,
            url=url,
            final_url=lc.final_url,
            new_page=_opener(
                get_browser,
                settings,
                run.dir / rel,
                lc.final_url,
                run,
                lc.cross_site_frames,
            ),
        )

    return record_live


def _page_refs(get_browser, settings: Settings, run, report: Report) -> list[PageRef]:
    return [
        PageRef(
            n=p.n,
            url=p.url,
            final_url=p.final_url or p.url,
            har_sha=pagecache.sha256(run.dir / p.har)
            if (run.dir / p.har).is_file()
            else None,
            new_page=_opener(
                get_browser,
                settings,
                run.dir / p.har,
                p.final_url or p.url,
                run,
                p.cross_site_frames,
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


def _cap_skipped(exc: TooManyItems) -> str:
    c = exc.cap
    minutes = max(1, round(exc.estimate_s / 60))
    return (
        f"this page has {exc.count} {c.noun}, and one call checks at "
        f"most {c.limit}. The other tests ran. To run this one too, call again "
        f'with tests ["{c.test}"] and no_time_limit=true (about {minutes} min '
        "or more; follow it with tobi_run_status), and replace its result in "
        "the saved report."
    )


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
    """Starts Chrome only if a check needs it (resume often does not); full
    Chromium only if a page with cross-site frames is replayed."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pw = self._proxy = None
        self._browsers: dict[tuple[bool, bool], Browser] = {}

    async def get(self, full: bool = False, autoplay: bool = False) -> Browser:
        if self._proxy is None:
            self._proxy = await EgressProxy(self.settings).__aenter__()
            self._pw = await async_playwright().start()
        if (full, autoplay) not in self._browsers:
            self._browsers[(full, autoplay)] = await launch_for(
                self._pw, self.settings, self._proxy, full, autoplay
            )
        return self._browsers[(full, autoplay)]

    async def close(self) -> None:
        for b in self._browsers.values():
            await b.close()
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
    """The report and the evidence files. Pictures are not listed: the
    questions and the report name the ones that matter (post-round 1 fix 6b:
    a large page's list of pictures was 13k characters)."""
    files = [run.report_path] + sorted(run.evidence_dir.glob("*.json"))
    return [run_uri(run.run_id, run.rel(f)) for f in files if f.exists()]


# Open questions shown per result (agent follow-through plan, change 2b:
# development run 7's agent skipped the pictures of results 25-70k
# characters long). The rest come with each tobi_answer_questions result.
QUESTION_PAGE = 10


def _compact(v: Any) -> Any:
    """A question input as sent: floats to one decimal, None and empty
    values left out of objects. Text is never changed."""
    if isinstance(v, float):
        r = round(v, 1)
        return int(r) if r == int(r) else r
    if isinstance(v, dict):
        return {
            k: _compact(x)
            for k, x in v.items()
            if x is not None and x != [] and x != {}
        }
    if isinstance(v, list):
        return [_compact(x) for x in v]
    return v


def _question_view(
    qs: list[OpenQuestion],
) -> tuple[list[OpenQuestion], dict[str, dict[str, str]]]:
    """Open questions for a result, with each question and rubric that
    several share given once in question_texts (post-round 1 fix 6b: 56 of
    a page's questions repeated one text). The report keeps them whole."""
    counts: dict[tuple[str, str], int] = {}
    for q in qs:
        counts[(q.question, q.rubric)] = counts.get((q.question, q.rubric), 0) + 1
    keys: dict[tuple[str, str], str] = {}
    texts: dict[str, dict[str, str]] = {}
    out = []
    for q in qs:
        # A picture already in the input is not listed again, coordinates
        # are rounded and empty fields dropped (change 2b; the report keeps
        # the input as recorded).
        named = json.dumps(q.input)
        paths = [p for p in q.evidence_paths if f'"{p}"' not in named]
        q = q.model_copy(update={"evidence_paths": paths, "input": _compact(q.input)})
        pair = (q.question, q.rubric)
        if counts[pair] < 2:
            out.append(q)
            continue
        if pair not in keys:
            base = f"{q.test_id.value}-{q.question_id.rsplit('-', 1)[-1]}"
            key, n = base, 2
            while key in texts:
                key, n = f"{base}-{n}", n + 1
            keys[pair] = key
            texts[key] = {"question": pair[0], "rubric": pair[1]}
        k = keys[pair]
        # A pointer, not an empty field: judge eval run 20's agent missed
        # question_texts when the fields were blank.
        see = f'Shared with other questions: read question_texts["{k}"]'
        view = {"question": f"{see}.question.", "rubric": f"{see}.rubric.", "texts": k}
        out.append(q.model_copy(update=view))
    return out, texts


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


def _evaluate(
    run: RunRecorder,
    report: Report,
    states: dict[TestId, Any],
    skipped: dict[TestId, str] | None = None,
) -> None:
    """Findings and questions for every selected test, from the checks' rules.
    `skipped`: tests the run left out on purpose, with the reason."""
    tests = report_tests(report)
    asked = {q.question_id for q in report.questions}
    findings: list[Finding] = []
    for t in tests:
        check = REGISTRY.get(t)
        if check is None:
            findings.append(Finding.not_performed(t, NO_SPEC_REASON))
            continue
        if t not in states and skipped and t in skipped:
            findings.append(Finding.not_performed(t, skipped[t]))
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
    if no_time_limit:
        # The user's choice also lifts the media store's cap (plan Q9).
        settings = settings.model_copy(
            update={"media_cap_mb": None, "media_cap_s": None}
        )
    decision = check_url(url, settings.allowed_domains, settings.dev_mode)
    if not decision.allowed:
        raise RunRefused(f"URL not allowed: {decision.reason}")
    others = check_other_pages(settings, url, other_pages or [], no_time_limit)
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
        frozen_pages=settings.frozen_pages_mode if settings.frozen_pages_dir else None,
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
    skipped: dict[TestId, str] = {}  # tests left out, and why (fix 12)
    walk: KeyboardWalk | None = None
    motion_task: asyncio.Task | None = None
    allowance = [0]  # T1 (a): seconds added once pass T finds moving content

    def extend() -> None:
        if no_time_limit or allowance[0]:
            return
        allowance[0] = settings.moving_allowance_s
        if ctx_ref:
            ctx_ref[0].deadline += allowance[0]
        run.log("time_allowance", seconds=allowance[0])

    ctx_ref: list = []

    async with EgressProxy(settings, log=run.log) as proxy, async_playwright() as pw:
        browser = await launch_browser(pw, settings, proxy)
        extra_browsers: dict[tuple[bool, bool], Browser] = {}  # on first need

        async def get_browser(full: bool = False, autoplay: bool = False) -> Browser:
            if not full and not autoplay:
                return browser
            if (full, autoplay) not in extra_browsers:
                extra_browsers[(full, autoplay)] = await launch_for(
                    pw, settings, proxy, full, autoplay
                )
                kind = MOTION_BROWSER if autoplay else "full Chromium"
                run.log("browser_launched", kind=kind)
            return extra_browsers[(full, autoplay)]

        try:
            report.versions = collect_versions(settings, browser, no_time_limit)
            report.versions.display = await measure_display(settings, browser)
            run.log("browser_launched", version=browser.version)
            await say(0, "Recording the page")
            har = run.evidence_dir / "page.har.zip"
            t0 = time.monotonic()
            try:
                cap = await _bounded(
                    obtain(browser, settings, url, har, run.log, proxy), hard
                )
            except Exception as exc:
                # The page never loaded: a tool error, and nothing is kept.
                shutil.rmtree(run.dir, ignore_errors=True)
                if isinstance(exc, TimeoutError):
                    raise RunRefused(
                        "The page could not be recorded within the time limit."
                    ) from None
                if isinstance(exc, (NavigationBlocked, NotFrozen)):
                    raise RunRefused(str(exc)) from exc
                raise RunRefused(
                    f"The page could not be loaded: {safe_error(exc)}"
                ) from None
            report.final_url = cap.final_url
            report.cross_site_frames = cap.cross_site_frames
            report.replay_browser = replay_browser_name(settings, cap.cross_site_frames)
            pages_cut = ""
            for i, other in enumerate(others, 1):
                await say(0.5, f"Recording other page {i} of {len(others)}")
                rel = f"evidence/pages/p{i}.har.zip"
                t1 = time.monotonic()
                (run.dir / rel).parent.mkdir(parents=True, exist_ok=True)
                hit = pagecache.reused(settings, other, run.dir / rel)
                try:
                    # Each other page records within its own share of the
                    # limit, so a slow one cannot eat the other tests' time.
                    share = hard if no_time_limit else t1 + settings.other_page_s
                    oc = (
                        Capture(
                            target_url=other,
                            final_url=hit.final_url,
                            har_path=run.dir / rel,
                            cross_site_frames=list(hit.cross_site_frames),
                            frozen=hit.frozen,
                        )
                        if hit
                        else await _bounded(
                            obtain(
                                browser,
                                settings,
                                other,
                                run.dir / rel,
                                run.log,
                                proxy,
                                tested=False,
                            ),
                            min(hard, share),
                        )
                    )
                    if hit is None:
                        pagecache.keep(
                            settings,
                            other,
                            run.dir / rel,
                            oc.final_url,
                            oc.cross_site_frames,
                            oc.frozen,
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
                    if isinstance(exc, (NavigationBlocked, NotFrozen)):
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
                    OtherPage(
                        n=i,
                        url=other,
                        final_url=oc.final_url,
                        har=rel,
                        cross_site_frames=oc.cross_site_frames,
                        frozen=oc.frozen if settings.frozen_pages_dir else None,
                        reused_from=(
                            datetime.fromtimestamp(
                                hit.recorded_at, timezone.utc
                            ).isoformat(timespec="seconds")
                            if hit
                            else None
                        ),
                        replay_browser=replay_browser_name(
                            settings, oc.cross_site_frames
                        ),
                    )
                )
                run.log(
                    "captured_other",
                    n=i,
                    reused=bool(hit),
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
            ctx = _context(
                settings, run, get_browser, cap.final_url, soft, cap.cross_site_frames
            )
            ctx_ref.append(ctx)
            ctx.selected = frozenset(c.test_id.value for c in checks)
            ctx.requested_url = url
            ctx.pages = _page_refs(get_browser, settings, run, report)
            ctx.record_live = _live_recorder(
                browser, settings, run, report, proxy, cap.final_url, get_browser
            )
            if any(getattr(c, "uses_motion", False) for c in checks) or any(
                needs_walk(c, ctx) for c in checks
            ):
                # Pass T beside the walk, in its own browser (plan Q2; no
                # measurable cost to the walk, item 18). The 2.x checks await
                # this task through motion.collect. It also runs for the walk
                # alone: what it finds still changing, the settle rule stops
                # waiting on (T1 (b)).
                motion_task = asyncio.create_task(
                    _watch_then_ignore(
                        ctx,
                        run,
                        extend,
                        # Frames are evidence for 2.x questions only.
                        any(getattr(c, "uses_motion", False) for c in checks),
                    )
                )
                ctx.cache["motion_task"] = motion_task
            while any(needs_walk(c, ctx) for c in checks):
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
                except TooManyItems as exc:
                    # Over one check's cap (5.D's form fields), found at the
                    # first load: leave that test out, say how to run it, and
                    # test the rest (post-round 1 fix 12).
                    t = TestId(exc.cap.test)
                    checks = [c for c in checks if c.test_id is not t]
                    skipped[t] = _cap_skipped(exc)
                    report.errors.append(f"{t.value} was not run: {skipped[t]}")
                    run.log("cap_skipped", test=t.value, count=exc.count)
                    continue
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
                except Exception as exc:
                    # E.g. an embed that detached mid-read (post-round 1 fix 1):
                    # the checks that need the walk are left for review, the
                    # rest still run.
                    err = safe_error(exc)
                    report.errors.append(f"The keyboard walk failed: {err}")
                    run.log("walk", "error", error=err, cost=asdict(cost))
                if walk is not None:
                    ctx.plan = ReplayPlan.of(walk.p1, walk.p2)
                    # 2.C A2's walk cross-check: steps that never settled.
                    ctx.cache["walk_unsettled"] = sum(
                        st.unsettled for p in (walk.p1, walk.p2) for st in p.steps
                    )
                    run.write_json(run.evidence_dir / "walk.json", walk)
                    run.log("walk", **_walk_summary(walk), cost=asdict(cost))
                break
            for c in checks:
                if pages_cut and uses_pages(c):
                    continue  # NEEDS REVIEW, not performed: pages_cut says why
                if needs_walk(c, ctx) and walk is None:
                    continue  # NEEDS REVIEW: the run did not complete (errors say why)
                await say(2, f"Checking {c.test_id.value}")
                try:
                    with metered() as cost:
                        state = await _bounded(
                            c.collect(ctx, walk), hard + allowance[0]
                        )
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
                    TIME_NOTE.format(limit=_limit(settings, len(others)) + allowance[0])
                )
        except RunRefused:
            raise  # its folder is already removed
        except BaseException:
            # A tool error leaves no run folder (CLAUDE.md).
            shutil.rmtree(run.dir, ignore_errors=True)
            raise
        finally:
            if motion_task is not None and not motion_task.done():
                motion_task.cancel()
            for b in (browser, *extra_browsers.values()):
                await b.close()

    await say(3, "Evaluating")
    report.findings = []
    _evaluate(run, report, states, skipped)
    result = await get_judge(settings.judge_backend).judge(report.open_questions)
    report.open_questions = result.pending
    report.finished_at = utcnow()
    report.follow_up_calls = follow_ups(report, states, skipped)
    run.write_json(run.report_path, report)
    pre_scrt = scrt.write_for_run(run.dir, run.report_path, report)
    run.log("run_end", status="error" if report.errors else "ok")
    qview = _question_view(report.open_questions[:QUESTION_PAGE])
    calls = report.follow_up_calls
    return RunResult(
        run_id=run.run_id,
        target=url,
        final_url=report.final_url,
        tests=report.tests,
        findings=[FindingView.of(f, report) for f in report.findings],
        open_questions=qview[0],
        question_texts=qview[1],
        page_text=_page_text(report, states),
        shared_inputs=_shared_inputs(report, states),
        walk=_walk_summary(walk) if walk else {},
        evidence=_evidence_uris(run),
        expires_at=expires_at(run.dir, settings.run_ttl_hours),
        report=report,
        report_uri=run_uri(run.run_id, run.rel(run.report_path)),
        pre_scrt_uri=run_uri(run.run_id, run.rel(pre_scrt)),
        errors=report.errors,
        next_step=next_step(report, calls),
        follow_up_calls=calls,
        work=Remaining.of(report).work,
        remaining=Remaining.of(report),
        todo=todo(report, calls),
        more_questions=max(0, len(report.open_questions) - QUESTION_PAGE),
    )


def follow_ups(
    report: Report, states: dict[TestId, Any], skipped: dict[TestId, str] | None
) -> list[dict]:
    """Tool calls that would let a NEEDS_REVIEW test decide: a check's own
    `follow_up` (19.A's suggested pages) and a test left out over a cap
    (5.D, with no_time_limit). For next_step; never made by the server."""
    review = {f.test_id for f in report.findings if f.outcome is Outcome.NEEDS_REVIEW}
    out: list[dict] = []
    for t in [t for t in TestId if t in review]:
        fn = getattr(REGISTRY.get(t), "follow_up", None)
        call = fn(states[t], report) if fn and t in states else None
        if call:
            out.append(call)
    for t in skipped or {}:
        out.append({"url": report.target, "tests": [t.value], "no_time_limit": True})
    return out


def _calls_text(calls: list[dict] | None) -> str:
    if not calls:
        return ""
    n = len(calls)
    user = sum(1 for c in calls if not server_may_make(c))
    ask = (
        f" {user} of them need the user's choice (no_time_limit): ask the "
        "user, then make those yourself as given."
        if user
        else ""
    )
    return (
        f" Then call tobi_run_status with finish=true: the server makes the "
        f"follow-up call{'s' if n != 1 else ''} in follow_up_calls that it may "
        "make itself, which let tests left for review decide, and waits for "
        f"them (the development runs' agents made almost none).{ask} Replace "
        "those tests' results in the saved report with the new ones."
    )


FINISH = (
    ' `work` stays "incomplete" while anything is left (`remaining`); '
    "your work is finished only when tobi_run_status with no job_id lists "
    "nothing left (the fourth development run's agent ended with questions "
    "and follow-up calls open). In a FAIL finding, `confirmed` (true) means "
    "the rules decided it and `unconfirmed` counts instances still waiting for "
    "answers: report them apart. Each finding is one line here: tobi_explain "
    "with the run_id gives the full summaries, reasons and fixes."
)


def next_step(report: Report, calls: list[dict] | None = None) -> str:
    """What the calling agent does next, in one place in every result
    (post-round 1 fixes 4, 12 and 19: agents left every question unanswered,
    decided NEEDS_REVIEW findings themselves, and opened few images)."""
    qs = report.open_questions
    review = (
        "a NEEDS_REVIEW finding is reported as needs review (a person checks "
        "it), never as a pass or a fail"
    )
    if not qs:
        return (
            f"No open questions. Relay each finding's summary; {review}."
            + _calls_text(calls)
            + " Then save the report (save_hint)."
            + FINISH
        )
    asked = {q.test_id for q in qs}
    tests = [t.value for t in TestId if t in asked]
    looks = (
        " Some questions ask what an image shows: open each run:// image they "
        "name with your MCP client's resource reader (read resource; a file "
        "reader cannot open run:// links; the pictures are also attached to "
        "this result) and look before answering. Their answers need `seen`: "
        "something the picture shows; or, if a picture cannot be opened or "
        "shows nothing, `picture_error` saying what happened, with unsure. "
        "An answer with neither is refused."
        if any(has_image(q.input) for q in qs)
        else ""
    )
    return (
        f"Not finished: {', '.join(tests)} stay NEEDS_REVIEW until you answer "
        f"the {len(qs)} open question(s)"
        + (
            f" ({QUESTION_PAGE} are in open_questions now; each answer result "
            "brings the next ones)"
            if len(qs) > QUESTION_PAGE
            else " in open_questions"
        )
        + ". Answer them now, "
        "yourself, in one tobi_answer_questions call per batch, each by its rubric; "
        "answer unsure only when the evidence does not settle it (only those go "
        f"to a person).{looks} Until then, {review}." + _calls_text(calls) + FINISH
    )


def todo(report: Report, calls: list[dict] | None = None) -> list[str]:
    """A short to-do list put last in every result (agent follow-through plan,
    change 2b: development run 7's agent said the instructions were "buried
    in 25-70k-character outputs" and asked for a short list at the end)."""
    out: list[str] = []
    qs = report.open_questions
    if qs:
        shown = qs[:QUESTION_PAGE]
        pics = sum(1 for q in shown if has_image(q.input))
        pic = (
            f"; {pics} name a picture: look and give `seen`, or "
            "`picture_error` with unsure"
            if pics
            else ""
        )
        more = (
            f" {len(qs) - len(shown)} more come with the answer result: "
            "answer those too, the same way, until none are left."
            if len(qs) > len(shown)
            else ""
        )
        out.append(
            f"[ ] Answer the {len(shown)} open question(s) in open_questions in "
            f"one tobi_answer_questions call (run_id {report.run_id}){pic}.{more}"
        )
    calls = calls or []
    mine = [c for c in calls if server_may_make(c)]
    user = [c for c in calls if not server_may_make(c)]
    if mine:
        out.append(
            f"[ ] Call tobi_run_status with finish=true: the server makes {len(mine)} "
            "follow-up call(s) itself and waits for them."
        )
    if user:
        out.append(
            f"[ ] Ask the user about {len(user)} call(s) that need no_time_limit "
            "(in follow_up_calls; they can take many minutes), then make them."
        )
    out.append(
        "[ ] Before reporting: call tobi_run_status with no job_id, and repeat "
        "until it lists nothing left (it covers every run of this session)."
    )
    out.append(
        f"[ ] Before writing your report: call tobi_explain with run_id "
        f"{report.run_id} for the tests you report on (every FAIL at least): "
        "results give one line per finding; it gives the places on the page, "
        "the reasons and how to fix them."
    )
    out.append("[ ] Save report_uri and pre_scrt_uri before expires_at.")
    out.append(
        "[ ] Report NEEDS_REVIEW findings as needs review, and say which "
        "findings still wait on work (waiting_on)."
    )
    return out


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
    before = {f.test_id: (f.outcome, f.summary, f.note) for f in report.findings}
    from tobi508.inline import attached

    accepted, rejected = record_answers(report, answers, attached(run.dir))
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
            report.cross_site_frames,
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
    # A test left out over a cap (no_time_limit) stays to do after answers.
    kept = [c for c in report.follow_up_calls if c.get("no_time_limit")]
    made = [
        {k: v for k, v in c.items() if k != "job_id"} for c in report.follow_ups_made
    ]
    report.follow_up_calls = [
        c for c in follow_ups(report, states, None) if c not in made
    ] + kept
    run.write_json(run.report_path, report)
    pre_scrt = scrt.write_for_run(run.dir, run.report_path, report)
    run.log(
        "answers_recorded",
        "error" if errors else "ok",
        accepted=accepted,
        rejected=rejected,
        errors=errors,
    )
    qview = _question_view(report.open_questions[:QUESTION_PAGE])
    calls = report.follow_up_calls
    # Only the findings this answer changed (agent follow-through plan,
    # change 2b): the rest were in earlier results and are in the report.
    changed = [
        f
        for f in report.findings
        if before.get(f.test_id) != (f.outcome, f.summary, f.note)
        or any(q.test_id == f.test_id for q in report.open_questions)
    ]
    return AnswerResult(
        run_id=run_id,
        accepted=accepted,
        rejected=rejected,
        findings=[FindingView.of(f, report) for f in changed],
        unchanged=[f.test_id.value for f in report.findings if f not in changed],
        open_questions=qview[0],
        question_texts=qview[1],
        page_text=_page_text(report, states),
        shared_inputs=_shared_inputs(report, states),
        report=report,
        report_uri=run_uri(run.run_id, run.rel(run.report_path)),
        pre_scrt_uri=run_uri(run.run_id, run.rel(pre_scrt)),
        errors=errors,
        next_step=next_step(report, calls),
        follow_up_calls=calls,
        work=Remaining.of(report).work,
        remaining=Remaining.of(report),
        todo=todo(report, calls),
        more_questions=max(0, len(report.open_questions) - QUESTION_PAGE),
    )


def server_may_make(call: dict) -> bool:
    """A follow-up call the server makes by itself (agent follow-through plan,
    change 1). 19.A's suggested pages may be visited (Abby, 2026-11-06):
    they are other pages like any caller's, checked by the allowlist and the
    tested page's host before and after redirects. no_time_limit stays the
    user's choice (CLAUDE.md)."""
    return not call.get("no_time_limit")


def take_follow_ups(settings: Settings, jobs: list) -> list[tuple[str, dict]]:
    """The follow-up calls the server may make, removed from each finished
    run's report (so they are made once) and recorded there as made.
    Returns (run_id, call) pairs; the caller starts them and records each
    job id with `record_follow_up`."""
    out: list[tuple[str, dict]] = []
    for j in jobs:
        if j.task is None or not j.task.done() or j.task.cancelled():
            continue
        if j.task.exception() is not None:
            continue
        res = j.task.result()
        try:
            run = RunRecorder.open(settings.runs_dir, res.run_id)
            report = Report.model_validate_json(run.report_path.read_text("utf-8"))
        except Exception:
            continue
        mine = [c for c in report.follow_up_calls if server_may_make(c)]
        if not mine:
            continue
        report.follow_up_calls = [
            c for c in report.follow_up_calls if not server_may_make(c)
        ]
        run.write_json(run.report_path, report)
        out.extend((report.run_id, c) for c in mine)
    return out


def record_follow_up(settings: Settings, run_id: str, call: dict, job_id: str) -> None:
    run = RunRecorder.open(settings.runs_dir, run_id)
    report = Report.model_validate_json(run.report_path.read_text("utf-8"))
    report.follow_ups_made.append({**call, "job_id": job_id})
    run.write_json(run.report_path, report)
    run.log("follow_up_started", job_id=job_id, tests=call.get("tests"))


def outstanding(settings: Settings, jobs: list) -> Outstanding:
    """Open questions and follow-up calls left in this session's runs, read
    from each run's report as it is now (answers since the run included)."""
    runs, running, done = [], [], 0
    for j in jobs:
        if j.task is None or not j.task.done():
            running.append(
                {
                    "job_id": j.id,
                    "target": j.url,
                    "status": "queued" if j.started is None else "running",
                }
            )
            continue
        if j.task.cancelled() or j.task.exception() is not None:
            continue
        res = j.task.result()
        try:
            run = RunRecorder.open(settings.runs_dir, res.run_id)
            report = Report.model_validate_json(run.report_path.read_text("utf-8"))
        except Exception:
            continue  # expired or removed
        if not report.open_questions and not report.follow_up_calls:
            done += 1
            continue
        waiting = {q.test_id for q in report.open_questions}
        runs.append(
            OutstandingRun(
                run_id=report.run_id,
                target=report.target,
                open_questions=len(report.open_questions),
                tests_waiting=[t.value for t in TestId if t in waiting],
                follow_up_calls=report.follow_up_calls,
                report_uri=run_uri(run.run_id, run.rel(run.report_path)),
            )
        )
    q = sum(r.open_questions for r in runs)
    c = sum(len(r.follow_up_calls) for r in runs)
    user = [
        {"run_id": r.run_id, **call}
        for r in runs
        for call in r.follow_up_calls
        if not server_may_make(call)
    ]
    if runs or running:
        step = (
            f"Left: {q} open question(s) in {len(runs)} run(s) and {c} follow-up "
            f"call(s); {len(running)} run(s) still going. For each run, answer "
            "its open questions with tobi_answer_questions (its report_uri has "
            "them, or call tobi_run_status with the job_id of a run still "
            "going). Then call tobi_run_status with finish=true: the server "
            "makes the follow-up calls it may make itself and waits for them. "
            "Ask the user about those in for_the_user. Call this again until "
            "nothing is left, before you report to the user."
        )
    else:
        step = (
            "Nothing is left: every run of this session is finished, with no "
            "open question or follow-up call."
        )
    items: list[str] = []
    if q:
        items.append(
            f"[ ] Answer {q} open question(s) left in {len(runs)} run(s) "
            "(tobi_answer_questions, one call per run)."
        )
    if c - len(user):
        items.append(
            f"[ ] Call tobi_run_status with finish=true: {c - len(user)} "
            "follow-up call(s) the server makes itself."
        )
    if user:
        items.append(f"[ ] Ask the user about {len(user)} call(s) in for_the_user.")
    if running:
        items.append(
            f"[ ] Wait for {len(running)} run(s) still going (tobi_run_status "
            "with each job_id)."
        )
    items.append(
        "[ ] Call this again until it lists nothing left, then report."
        if items
        else "[x] Nothing left: report to the user, and save each run's report."
    )
    return Outstanding(
        runs=runs,
        running=running,
        done=done,
        for_the_user=user,
        next_step=step,
        todo=items,
    )
