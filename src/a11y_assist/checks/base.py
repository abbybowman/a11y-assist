"""What every TT check module provides, and the context a run gives it.

One module per TT test (e.g. checks/t4c.py), registered in checks/__init__.py.
A check never decides an outcome outside its rules spec (CLAUDE.md principle
2): `evaluate` applies the spec's rows to the evidence, and nothing else does.

Adding a check:
  1. Write docs/rules/<id>-<name>.md from _template.md (with Abby's approval).
  2. Add fixtures (ACT cases first) and expected outcomes in the tests.
  3. Write checks/t<id>.py providing a `Check` (below) and register it.
  4. The pipeline, tools, report and resume path need no changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Protocol

from pydantic import BaseModel

from a11y_assist.models import Finding, OpenQuestion, Report, TestId
from a11y_assist.traverse import NewPage
from a11y_assist.walk import ExtraFactory, KeyboardWalk


@dataclass
class RunContext:
    """What a check may use while collecting evidence for one page."""

    new_page: NewPage  # a fresh load of the recorded page per call
    quiet_ms: int  # settle rule quiet window
    deadline: float  # time.monotonic() limit for the whole run
    shots: Path  # screenshot folder
    rel: Path  # run folder (evidence paths are relative to it)


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
