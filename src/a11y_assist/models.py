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


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Outcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    DNA = "DNA"  # Does Not Apply
    NOT_TESTED = "NOT_TESTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class TestId(str, Enum):
    """Trusted Tester 5.x test IDs in scope (Test 4: Keyboard Access and Focus).

    Names are from https://section508coordinators.github.io/TrustedTester/
    keyboard.html. TT 5 also defines 4.G and 4.H, which are not in scope yet.
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


class FocusStop(BaseModel):
    """One element that held focus after a Tab or Shift+Tab press.

    `frame_path` lists the iframe chain from the top document, e.g.
    ["iframe#login"] for an element inside that iframe; empty for the top frame.
    """

    index: int = Field(description="0-based press number in this walk.")
    key: str = Field(description='"Tab" or "Shift+Tab".')
    selector: str | None
    tag: str | None
    role: str | None
    accessible_name: str | None
    tabindex: str | None = Field(description="Raw tabindex attribute, if any.")
    bounding_box: BoundingBox | None
    frame_path: list[str] = Field(default_factory=list)
    url: str
    screenshot: str | None = Field(description="Path relative to the run folder.")
    is_body: bool = Field(description="Focus is on <body>/document, not an element.")
    page_has_focus: bool = Field(
        description="document.hasFocus() in the focused frame. False when focus "
        "has left the page, e.g. to the browser UI after the last element."
    )


class FocusWalk(BaseModel):
    direction: str = Field(description='"forward" (Tab) or "backward" (Shift+Tab).')
    max_presses: int
    presses: int
    stops: list[FocusStop]
    stopped_because: str = Field(
        description="Why the walk ended: max_presses, returned_to_start, "
        "navigation, or error. Descriptive only; not an outcome."
    )


class KeyboardEvidence(BaseModel):
    target_url: str
    final_url: str
    har_path: str | None
    forward: FocusWalk
    backward: FocusWalk


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
    decided_by: DecidedBy | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @classmethod
    def needs_review(cls, test_id: TestId, rationale: str) -> Finding:
        return cls(
            test_id=test_id,
            test_name=test_id.tt_name,
            outcome=Outcome.NEEDS_REVIEW,
            rationale=rationale,
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
