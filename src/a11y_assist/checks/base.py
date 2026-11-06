"""What every TT check module provides, and the context a run gives it.

One module per TT test (e.g. checks/t4c.py), registered in checks/__init__.py.
A check never decides an outcome outside its rules spec (CLAUDE.md principle
2): `evaluate` applies the spec's rows to the evidence, and nothing else does.

Adding a check (4.D, 4.E, 4.F and 5.D were built this way; copy t4e.py, the
smallest, t5d.py for a form test, or t9b.py for a multi-page test):
  1. Research first (CLAUDE.md): the TT text, W3C Understanding and its
     techniques, ACT rules and DHS's verdicts, the ICT Testing Baseline
     test and its Baseline Alignment cases; read the vendored pages before
     writing rules (5.D's TC10.C-3-fail-2 changed a rule). Then draft
     docs/rules/<id>-<name>.md from _template.md at 0.1.0: only what the TT
     PDF asks a tester to do; reuse the walk, walk extras and the existing
     collectors (observe.py, ctx.replay, stop.control) before adding passes;
     one plain sentence per row; cite the sources; mark OPEN only what they
     leave open.
  2. Ask Abby the open points as multiple-choice questions; write each
     answer into the rule it decides. No decision log.
  3. Fixtures: vendored ACT cases first (tests/fixtures/act/sync_act.py),
     custom pages in tests/fixtures/<id>/ only for gaps; expected outcomes
     in the test file or manifest, never in a page. Rows no page triggers
     reliably get unit tests on hand-built state.
  4. Write checks/t<id>.py: a Check below, walk extras as StepHooks, rows
     as engine.Row tables copied from the spec. While the spec is a draft,
     register it only in tests/drafts.py (a draft gives no outcome from the
     server); move it to checks/__init__.py at 1.0.0. Run it with
     tests/harness.py run_check(). Use ctx.replay for replays and
     ctx.out_of_time() before each one; a page whose items exceed a cap the
     check declares (`cap`) is refused at the first load.
     A test that compares pages sets `uses_pages = True` and reads
     `site.site_read(ctx)` (each page once, cached) and `ctx.pages`;
     without other pages it is not performed and costs nothing (9.A-9.C).
     Open questions: link files as run:// (never run-folder paths), put
     evidence several questions share in shared_inputs(state), and give the
     agent what its rubric asks about (an eval found a rubric judged on half
     the evidence).
  5. Run the judge eval on the fixtures that ask questions (evals/README.md):
     one fresh agent answers them from the tool output alone. Fix every
     mismatch in the question or its evidence before trusting the rows.
  6. When fixtures pass, make the spec match the code exactly (every row
     the code has, the spec has), set spec_version 1.0.0, trim
     <id>-build-tasks.md to what is left, and add any lesson that cost
     time to docs/solutions/.
  7. The pipeline, tools, report, explain prompt and resume path need no
     changes; the tool description lists the new test from the registry.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Protocol

from pydantic import BaseModel

from a11y_assist.models import Finding, OpenQuestion, Report, TestId
from a11y_assist.traverse import NewPage, ReplayPlan, Session, replay
from a11y_assist.walk import ExtraFactory, KeyboardWalk


@dataclass
class PageRef:
    """Another page of the same site (9.A-9.C): a fresh load of its own HAR
    per call to `new_page`."""

    n: int  # 1-based, in the caller's order
    url: str
    final_url: str
    new_page: NewPage
    har_sha: str | None = None  # its recording's SHA-256 (pagecache reads)


@dataclass
class RunContext:
    """What a check may use while collecting evidence for one page."""

    new_page: NewPage  # a fresh load of the recorded page per call
    quiet_ms: int  # settle rule quiet window
    deadline: float  # time.monotonic() limit for the whole run
    shots: Path  # screenshot folder
    rel: Path  # run folder (evidence paths are relative to it)
    plan: ReplayPlan | None = None  # from the walk, once it has run
    timed_out: bool = False  # a check stopped work for the run limit
    # Evidence one check collects for another in the same call (5.F's error
    # pass, which 5.G reads): keyed by the collector's name.
    cache: dict[str, Any] = field(default_factory=dict)
    third_party: Path | None = None  # vendored ANDI (andi.install_andi_routes)
    selected: frozenset[str] = frozenset()  # TT test IDs in this call ("5.A")
    requested_url: str = ""  # the URL the caller gave, before redirects (19.A)
    # Other pages of the same site the caller named (empty: none given). Only
    # recorded when a selected check compares pages (`uses_pages`).
    pages: list[PageRef] = field(default_factory=list)
    # Record one more live page on the tested page's host (19.A's site search
    # only; CLAUDE.md). Returns its PageRef; raises ValueError if refused.
    # None when resuming (no live loads then).
    record_live: Any = None
    # A fresh load with pass T's hooks (motion.MOTION_INIT_JS) before page
    # scripts, for 2.A-2.D (motion.collect). None when not available.
    open_motion: NewPage | None = None
    motion_browser: str = ""  # what runs those loads, for the evidence
    # Content pass T found still changing, which the settle rule stops
    # waiting on once pass T ends (pipeline.SettleIgnore; T1 (b)).
    settle_ignore: Any = None

    def out_of_time(self) -> bool:
        """Past the checks' deadline (4.C spec section 2, Run limits). Use it
        before every replay; a True answer is recorded, so the result says
        the run limit cut something short."""
        if time.monotonic() > self.deadline:
            self.timed_out = True
            return True
        return False

    async def replay(
        self, keys: list[str], shots: bool = False, hooks: list | None = None
    ) -> Session:
        """A fresh load with `keys` pressed. Use it for every replay to a walk
        stop: prefix presses the walk saw quiet skip the quiet window, and the
        replay is redone fully settled if focus does not end where the walk
        had it (traverse.replay; 4.C spec section 2)."""
        return await replay(
            self.new_page,
            self.quiet_ms,
            keys,
            self.plan,
            self.shots if shots else None,
            self.rel if shots else None,
            hooks,
        )


class Check(Protocol):
    test_id: ClassVar[TestId]
    state_type: ClassVar[type[BaseModel]]
    uses_walk: ClassVar[bool]  # needs the shared keyboard walk
    # Plain words for users: what the tool does for this test automatically,
    # and what it leaves to a person (explain.py shows it before a run).
    about: ClassVar[str]

    def walk_extras(self) -> list[ExtraFactory]:
        """Per-step evidence this check needs from the shared walk (empty for
        most checks). The pipeline passes the union, deduplicated by hook
        name, so running other checks alone collects none of it."""
        ...

    async def collect(
        self, ctx: RunContext, walk: KeyboardWalk | None
    ) -> BaseModel: ...

    def evaluate(self, state: Any, evidence_refs: list[str]) -> Finding: ...

    def questions(self, state: Any, evidence_refs: list[str]) -> list[OpenQuestion]: ...

    async def resume(self, ctx: RunContext, state: Any, report: Report) -> list[str]:
        """Apply answers in force to the state (pressing keys if needed).
        Returns error messages."""
        ...

    # Optional: `follow_up(state, report) -> dict | None`, the tool call that
    # would let this test decide (19.A: the same page with the pages it
    # suggests). The pipeline names it in the result's next_step; it never
    # makes the call itself (post-round 1 fix 18).
