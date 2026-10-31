"""Test 4.C (2.1.2-no-keyboard-trap): rows from docs/rules/4c-no-keyboard-trap.md.

Implemented: section 1 (A1-A3) and table 3b. Instance rows M1-M14 and passes
P3-P6 are not implemented yet, so an applicable page is NEEDS_REVIEW with the
note "This test could not be performed" (G3).
"""

from __future__ import annotations

from dataclasses import dataclass

from a11y_assist.engine import PageEvidence, Row, first_match, page_outcome
from a11y_assist.models import DecidedBy, Finding, Outcome, PassResult, TestId

SPEC = "4c-no-keyboard-trap.md"


@dataclass
class Evidence4C:
    p1: PassResult
    p2: PassResult

    @property
    def stops(self) -> int:
        return sum(
            s.stop.kind == "element" for p in (self.p1, self.p2) for s in p.steps
        )

    @property
    def inventory(self) -> int:
        return max(self.p1.inventory, self.p2.inventory)


# Section 1. A4 (mouse-only content, nothing focusable) is covered by A1: the
# keyboard finds nothing either way, and the gap belongs to 4.A.
APPLICABILITY = [
    Row(
        "A1",
        lambda e: e.stops == 0 and e.inventory == 0,
        Outcome.DNA,
        "p. 21 Applicability",
    ),
    Row(
        "A2",
        lambda e: e.stops == 0 and e.inventory > 0,
        Outcome.NEEDS_REVIEW,
        "Spec rule",
    ),
    Row("A3", lambda e: e.stops > 0, Outcome.PASS, "p. 21 Applicability"),  # applies
]


def evaluate(ev: Evidence4C, evidence_refs: list[str]) -> Finding:
    applicability = first_match(APPLICABILITY, ev)
    assert applicability is not None
    incomplete = [f"{p.name} ended: {p.end}" for p in (ev.p1, ev.p2) if not p.complete]
    if applicability.id == "A3":
        incomplete.append(
            "instance rules M1-M14 and passes P3-P6 are not implemented yet"
        )
    g, outcome = page_outcome(
        PageEvidence(
            applicability, instances=[], incomplete=incomplete, complete_for_pass=False
        )
    )
    rows = [applicability.id, g]
    if outcome is Outcome.NEEDS_REVIEW and g in ("G3", "G5"):
        f = Finding.not_performed(
            TestId.T4C,
            f"Spec {g}. " + "; ".join(incomplete),
            DecidedBy.RULE,
            evidence_refs,
        )
    else:
        reason = {
            "A1": "No component can receive keyboard focus: both passes reached no "
            "stop and the DOM inventory found no tabbable element.",
            "A2": "Both passes reached no stop, but the DOM inventory found "
            f"{ev.inventory} tabbable element(s): a traversal or inventory fault.",
        }.get(applicability.id, "")
        f = Finding(
            test_id=TestId.T4C,
            test_name=TestId.T4C.tt_name,
            outcome=outcome,
            rationale=f"Spec {applicability.id}. {reason}",
            decided_by=DecidedBy.RULE,
            evidence_refs=evidence_refs,
        )
    f.rows = rows
    return f
