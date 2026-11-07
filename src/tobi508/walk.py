"""The shared keyboard walk: one forward (Tab) and one backward (Shift+Tab)
pass per page, each from a fresh load of the recorded page.

TT 5.1.3 chains its keyboard tests: 4.D "Continue from Test 4.C", 4.E
"Continue from Test 4.D" (p. 22) and 4.F "Use the tab key to move focus through
the page" (p. 23). So the walk runs once per page and every check reads it.
Collect once, evaluate many. The walk records facts only; what a stop means
for an outcome is decided by each check's rules module.

Pass end conditions, the press cap and the settle rule are defined in the 4.C
spec (section 2), which the other keyboard specs use by reference.

A trap event ends a pass only when a second pass of the same key, from a
fresh load, ends in the same trap (4.C 1.9.0). Some pages differ from load to
load: Artemis III's survey dialog opens on about 1 load in 10, takes focus and
keeps it, and ended P1 after 9-13 presses on those loads while every other
walk and replay saw a page without it (docs/solutions/trap-seen-once.md).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

from tobi508.models import PassResult
from tobi508.traverse import NewPage, Pace, StepHook, run_pass

TRAP_ENDS = ("stuck", "loop")


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


# A check's walk extras: called once per pass with the pass name ("P1" or
# "P2") and P1's result when making P2's hooks (so P2 can top up only what P1
# missed). Returns a fresh hook for that pass.
ExtraFactory = Callable[[str, "PassResult | None"], StepHook]


async def walk_page(
    new_page: NewPage,
    quiet_ms: int,
    deadline: float | None,
    shots: Path | None = None,
    rel: Path | None = None,
    extras: list[ExtraFactory] | None = None,
    pace: Pace | None = None,
) -> KeyboardWalk:
    """P1 then P2. `extras` are the union of the selected checks' walk extras;
    running 4.C alone passes none. With `pace`, P1 raises WalkTooLong as soon
    as its pace shows the walk cannot finish before the deadline."""
    extras = extras or []
    p1 = await _confirmed(
        "P1",
        new_page,
        "Tab",
        quiet_ms,
        deadline,
        shots,
        rel,
        lambda: [f("P1", None) for f in extras],
        pace,
    )
    p2 = await _confirmed(
        "P2",
        new_page,
        "Shift+Tab",
        quiet_ms,
        deadline,
        shots,
        rel,
        lambda: [f("P2", p1) for f in extras],
        None,
    )
    return KeyboardWalk(p1=p1, p2=p2)


def trap_paths(p: PassResult) -> set[str]:
    """The trap's stops by frame chain plus CSS path: stop keys hold node IDs,
    which change on every load (4.C spec section 2, Stop identity)."""
    return {s.stop.path_key for s in p.steps if s.stop.key in set(p.trap)}


async def _confirmed(
    name: str,
    new_page: NewPage,
    key: str,
    quiet_ms: int,
    deadline: float | None,
    shots: Path | None,
    rel: Path | None,
    hooks: Callable[[], list[StepHook]],
    pace: Pace | None,
) -> PassResult:
    """One pass; when it ends in a trap event, a second pass from a fresh load
    (4.C spec section 2, 1.9.0). The same trap again: the first pass stands,
    confirmed. Anything else: the second pass stands, carrying the first as
    `unrepeated` (4.C row M1 leaves that trap for a person). Each pass gets
    fresh hooks: walk extras keep state per pass."""
    first = await run_pass(
        name, new_page, key, quiet_ms, deadline, shots, rel, hooks=hooks(), pace=pace
    )
    if first.end not in TRAP_ENDS:
        return first
    # The time-limit pace starts again with this pass: the first pass may
    # have stopped after a few presses.
    again_pace = Pace(pace.deadline) if pace is not None else None
    again = await run_pass(
        name,
        new_page,
        key,
        quiet_ms,
        deadline,
        shots,
        rel,
        hooks=hooks(),
        pace=again_pace,
        shot_label=f"{name}-again",
    )
    if again.end == first.end and trap_paths(again) == trap_paths(first):
        return first.model_copy(update={"confirmed": True})
    return again.model_copy(update={"unrepeated": first})
