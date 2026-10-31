"""Pydantic data model for evidence, findings, open questions and reports.

Nothing here decides an outcome. Outcomes come only from the rules specs in
docs/rules/. Answers to open questions (from a model or a human) are recorded
with `decided_by`; the spec decides what they mean.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

NOT_CERTIFIED_DISCLAIMER = (
    "Agent-assisted findings only. This is NOT a certified DHS Trusted Tester "
    "result and must not be reported as one."
)


# The note a finding carries when its test was not performed (TT 5.1.3 p. 5).
# The PDF allows NOT TESTED only where a test names it (p. 6), so a test the
# tool could not perform is NEEDS_REVIEW with this note and a reason.
TEST_NOT_PERFORMED_NOTE = "This test could not be performed"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Outcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    DNA = "DNA"  # Does Not Apply
    # Only for tests whose TT text names NOT TESTED (p. 6); none in scope do.
    NOT_TESTED = "NOT_TESTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class TestId(str, Enum):
    """Trusted Tester 5.1.3 test IDs in scope (Test 4: Keyboard Access and Focus).

    Test 4 has six tests, 4.A to 4.F. Names are checked against the TT 5.1.3
    PDF, pp. 19-23.
    """

    __test__ = False  # not a pytest test class

    T4A = "4.A"
    T4B = "4.B"
    T4C = "4.C"
    T4D = "4.D"
    T4E = "4.E"
    T4F = "4.F"

    @property
    def tt_name(self) -> str:
        return TT_TEST_NAMES[self]

    @property
    def wcag_sc(self) -> str:
        return TT_WCAG_SC[self]


TT_TEST_NAMES: dict[TestId, str] = {
    TestId.T4A: "2.1.1-keyboard-access",
    TestId.T4B: "2.1.1-no-keystroke-timing",
    TestId.T4C: "2.1.2-no-keyboard-trap",
    TestId.T4D: "2.4.7-focus-visible",
    TestId.T4E: "3.2.1-on-focus",
    TestId.T4F: "2.4.3-focus-order-meaning",
}

TT_WCAG_SC: dict[TestId, str] = {
    TestId.T4A: "2.1.1 Keyboard",
    TestId.T4B: "2.1.1 Keyboard",
    TestId.T4C: "2.1.2 No Keyboard Trap",
    TestId.T4D: "2.4.7 Focus Visible",
    TestId.T4E: "3.2.1 On Focus",
    TestId.T4F: "2.4.3 Focus Order",
}


class DecidedBy(str, Enum):
    RULE = "rule"
    MODEL = "model"
    HUMAN = "human"


# ── Evidence ─────────────────────────────────────────────────────────────────


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Stop(BaseModel):
    """Where focus is after a key press.

    kind "element": the deepest focused element, followed through frames and
    open and closed shadow roots. "BODY": focus fell to the document body while
    the page kept focus. "OUT": focus left the page for the browser UI.
    """

    kind: Literal["element", "BODY", "OUT"]
    key: str = Field(
        description="Identity within one page load: '<CDP frame ID>:<backend node "
        "ID>', or 'BODY' / 'OUT'."
    )
    frame_chain: list[str] = Field(
        default_factory=list, description="CSS paths of the iframes, top first."
    )
    css_path: str | None = None
    tag: str | None = None
    role: str | None = None
    name: str | None = None
    bounding_box: BoundingBox | None = None
    in_viewport: bool | None = None
    frame_url: str | None = None
    unresolved: bool = False

    @property
    def path_key(self) -> str:
        """Identity that survives a reload: frame chain plus CSS path."""
        return " >> ".join([*self.frame_chain, self.css_path or self.kind])


class Step(BaseModel):
    n: int = Field(description="1-based press number within the pass.")
    key: str
    stop: Stop
    top_url: str
    top_has_focus: bool
    open_pages: int
    mutations: int = Field(description="DOM mutations since the previous step.")
    focus_events: list[dict[str, Any]] = Field(default_factory=list)
    screenshot: str | None = Field(default=None, description="Relative to the run.")
    unsettled: bool = False
    rerun: bool = Field(
        default=False,
        description="A focus change after the settle window was seen, so the step "
        "was re-read with the 1,000 ms window.",
    )


class PassResult(BaseModel):
    name: str = Field(description='e.g. "P1", "P2", "P3 #2 Escape+Tab".')
    keys: list[str] = Field(default_factory=list, description="Prefix keys replayed.")
    steps: list[Step] = Field(default_factory=list)
    end: Literal["wrap", "stuck", "loop", "navigation", "cap", "error", "done"]
    trap: list[str] = Field(
        default_factory=list, description="Stop keys of the stuck element or loop."
    )
    cap: int
    inventory: int
    error: str | None = None

    @property
    def complete(self) -> bool:
        return self.end not in ("cap", "error")


# ── Findings and open questions ──────────────────────────────────────────────


class Instance(BaseModel):
    """One place on the page a finding applies to."""

    selector: str | None = None
    frame_path: list[str] = Field(default_factory=list)
    description: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    test_id: TestId
    test_name: str
    outcome: Outcome = Outcome.NEEDS_REVIEW
    instances: list[Instance] = Field(default_factory=list)
    evidence_refs: list[str] = Field(
        default_factory=list, description="Paths relative to the run folder."
    )
    rationale: str = ""
    note: str | None = Field(
        default=None,
        description=f'"{TEST_NOT_PERFORMED_NOTE}" when the test was not performed; '
        "the rationale then gives the reason.",
    )
    decided_by: DecidedBy | None = None
    rows: list[str] = Field(
        default_factory=list, description="Spec rows that produced the outcome."
    )
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @classmethod
    def needs_review(cls, test_id: TestId, rationale: str) -> Finding:
        return cls(
            test_id=test_id,
            test_name=test_id.tt_name,
            outcome=Outcome.NEEDS_REVIEW,
            rationale=rationale,
        )

    @classmethod
    def not_performed(
        cls,
        test_id: TestId,
        reason: str,
        decided_by: DecidedBy | None = None,
        evidence_refs: list[str] | None = None,
    ) -> Finding:
        return cls(
            test_id=test_id,
            test_name=test_id.tt_name,
            outcome=Outcome.NEEDS_REVIEW,
            note=TEST_NOT_PERFORMED_NOTE,
            rationale=reason,
            decided_by=decided_by,
            evidence_refs=evidence_refs or [],
        )


class OpenQuestion(BaseModel):
    question_id: str
    test_id: TestId
    question: str
    rubric: str = Field(description="How to answer; from the rules spec.")
    allowed_outcomes: list[Outcome]
    evidence_paths: list[str] = Field(description="Absolute file paths to inspect.")


class Answer(BaseModel):
    question_id: str
    outcome: Outcome
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    decided_by: DecidedBy = DecidedBy.MODEL


class RecordedAnswer(BaseModel):
    """An answered question. The rules spec maps these to finding outcomes."""

    question: OpenQuestion
    answer: Answer
    recorded_at: datetime


# ── Run records ──────────────────────────────────────────────────────────────


class StepLog(BaseModel):
    """One line of the run's JSONL step log."""

    ts: datetime = Field(default_factory=utcnow)
    step: str
    status: str = Field(description='"ok", "error", "blocked" or "info".')
    detail: dict[str, Any] = Field(default_factory=dict)


class Versions(BaseModel):
    a11y_assist: str
    andi: str
    jquery: str
    playwright: str
    browser_channel: str
    browser: str | None
    os: str
    python: str
    rules_spec: dict[str, str] = Field(
        description=(
            "TT test ID -> rules spec version from the spec's front matter, "
            "with the spec file's SHA-256 prefix."
        )
    )
    judging_model: str


class Report(BaseModel):
    disclaimer: str = NOT_CERTIFIED_DISCLAIMER
    certified: Literal[False] = False
    run_id: str
    target: str
    final_url: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    versions: Versions
    findings: list[Finding] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
    answers: list[RecordedAnswer] = Field(default_factory=list)
    judge_backend: str = "client"
    errors: list[str] = Field(default_factory=list)
    evidence_dir: str
