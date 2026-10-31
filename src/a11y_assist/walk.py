"""The shared keyboard walk: one forward (Tab) and one backward (Shift+Tab)
pass per page, each from a fresh load of the recorded page.

TT 5.1.3 chains its keyboard tests: 4.D "Continue from Test 4.C", 4.E
"Continue from Test 4.D" (p. 22) and 4.F "Use the tab key to move focus through
the page" (p. 23). So the walk runs once per page and every check reads it.
Collect once, evaluate many. The walk records facts only; what a stop means
for an outcome is decided by each check's rules module.

Pass end conditions, the press cap and the settle rule are defined in the 4.C
spec (section 2), which the other keyboard specs use by reference.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from a11y_assist.models import PassResult
from a11y_assist.traverse import NewPage, run_pass


class KeyboardWalk(BaseModel):
    p1: PassResult  # forward, Tab
    p2: PassResult  # backward, Shift+Tab

    @property
    def stops(self) -> int:
        return sum(
            s.stop.kind == "element" for p in (self.p1, self.p2) for s in p.steps
        )

    @property
    def inventory(self) -> int:
        return max(self.p1.inventory, self.p2.inventory)


async def walk_page(
    new_page: NewPage,
    quiet_ms: int,
    deadline: float | None,
    shots: Path | None = None,
    rel: Path | None = None,
) -> KeyboardWalk:
    p1 = await run_pass("P1", new_page, "Tab", quiet_ms, deadline, shots, rel)
    p2 = await run_pass("P2", new_page, "Shift+Tab", quiet_ms, deadline, shots, rel)
    return KeyboardWalk(p1=p1, p2=p2)
