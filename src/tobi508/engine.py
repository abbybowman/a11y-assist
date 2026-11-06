"""Shared rules machinery: first-match tables and the template's page outcome.

Every rules spec (docs/rules/_template.md) has the same shape: applicability
rows, instance rows (first match wins) and page rows G1-G5. This module runs
those tables; the rows themselves, with their conditions, live in each test's
module (e.g. t4c.py) and come from its spec. Nothing here decides an outcome
on its own.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tobi508.models import Outcome


@dataclass(frozen=True)
class Row:
    id: str
    when: Callable[[Any], bool]
    outcome: Outcome | None  # None: not decisive, continue down the table
    source: str = ""


def first_match(rows: list[Row], evidence: Any) -> Row | None:
    """The first row whose condition holds and that gives an outcome. Rows with
    outcome None that match are skipped (e.g. M5 "not an exit; continue")."""
    for row in rows:
        if row.outcome is not None and row.when(evidence):
            return row
    return None


@dataclass
class PageEvidence:
    """Inputs to the template's table 3b."""

    applicability: Row  # the matched section 1 row
    instances: list[tuple[str, Outcome]]  # (instance id, outcome)
    incomplete: list[str]  # reasons evidence is incomplete
    complete_for_pass: bool  # the test's G4 completeness condition


PAGE_ROWS = [
    Row(
        "G1",
        lambda e: e.applicability.outcome in (Outcome.DNA, Outcome.NEEDS_REVIEW),
        None,
    ),
    Row("G2", lambda e: any(o is Outcome.FAIL for _, o in e.instances), Outcome.FAIL),
    Row(
        "G3",
        lambda e: (
            bool(e.incomplete) or any(o is Outcome.NEEDS_REVIEW for _, o in e.instances)
        ),
        Outcome.NEEDS_REVIEW,
    ),
    Row(
        "G4",
        lambda e: (
            e.complete_for_pass and all(o is Outcome.PASS for _, o in e.instances)
        ),
        Outcome.PASS,
    ),
    Row("G5", lambda e: True, Outcome.NEEDS_REVIEW),
]


def page_outcome(e: PageEvidence) -> tuple[str, Outcome]:
    """Table 3b, first match wins. G1 returns section 1's outcome."""
    if PAGE_ROWS[0].when(e):
        return "G1", e.applicability.outcome  # type: ignore[return-value]
    row = first_match(PAGE_ROWS[1:], e)
    assert row is not None  # G5 always matches
    return row.id, row.outcome  # type: ignore[return-value]
