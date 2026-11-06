"""Test 2.D (4.1.2-change-notify-auto), from docs/rules/2d-change-notify-auto.md
(spec 1.0.0).

Reads 2.C's pass T (motion.collect, shared in ctx.cache) and 2.C's instances;
presses no keys. Only evaluate() and the row tables decide outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from tobi508 import motion
from tobi508.checks.base import RunContext
from tobi508.checks.t2c import a2_note, applicability, content_name
from tobi508.engine import PageEvidence, Row, page_outcome
from tobi508.models import (
    REVIEW_HEAD,
    DecidedBy,
    Finding,
    Instance,
    OpenQuestion,
    Outcome,
    TestId,
)
from tobi508.motion import Change, MotionPass, Region
from tobi508.walk import KeyboardWalk


class State2D(BaseModel):
    mp: MotionPass
    j1: dict[str, dict[str, Any]] = Field(default_factory=dict)  # by instance
    j2: dict[str, dict[str, Any]] = Field(default_factory=dict)


def changes(r: Region) -> list[Change]:
    """2.D's changes (spec Terms): text, image source or children; when the
    region showed new content with none of those (slides shown by a class),
    its class and attribute changes."""
    return r.changes or r.attr_list


@dataclass
class Inst:
    id: str
    region: Region
    mp: MotionPass
    j1: dict[str, Any]
    j2: dict[str, Any]

    def unlive(self) -> list[Change]:
        return [c for c in changes(self.region) if not c.live_at_start]

    def dialog(self):
        return next((d for d in self.mp.dialogs_opened if d.keyboard), None)


INSTANCE_ROWS = [
    Row(
        "N1",
        lambda i: not changes(i.region),
        Outcome.NEEDS_REVIEW,
        "Spec rule",
    ),
    Row(
        "N2",
        lambda i: not i.unlive(),
        Outcome.PASS,
        "p. 17 ER 3; DHS FAQ",
    ),
    Row("N3", lambda i: i.dialog() is not None, None, "p. 16 ER 1"),  # J2
    Row("N4", lambda i: bool(i.region.focus_in), None, "p. 16 ER 2"),  # J1
    Row("N5", lambda i: True, Outcome.FAIL, "p. 16 ER (none of 1-3)"),
]


def instance_outcome(i: Inst) -> tuple[list[str], Outcome]:
    for row in INSTANCE_ROWS:
        if not row.when(i):
            continue
        if row.outcome is not None:
            return [row.id], row.outcome
        j = (i.j2 if row.id == "N3" else i.j1) or {}
        q = "J2" if row.id == "N3" else "J1"
        choice = j.get("choice", "")
        if choice == "sufficient":
            return [row.id, q], Outcome.PASS
        if choice == "not_sufficient":
            return [row.id, q], Outcome.FAIL
        return [row.id, "N6"], Outcome.NEEDS_REVIEW
    raise AssertionError("N5 always matches")


def _sentence(rows: list[str], r: Region, outcome: Outcome) -> str:
    c = content_name(r)
    last = rows[-1]
    if last == "N2":
        return (
            f"{c} changes by itself inside a live region, so screen readers "
            "announce the changes."
        )
    if last == "N5":
        off = (
            ' It turns its announcements off while it changes (aria-live="off"), '
            "as W3C's carousel pattern does; the test asks that each change be "
            "announced, so announcements should come on, for example while it "
            "is paused."
            if r.live_off
            else ""
        )
        return (
            f"{c} changes by itself, but screen reader users are not told: it "
            "is not in a live region, focus does not move to it, and no dialog "
            "appears. Put it in an aria-live region, or let users pause it and "
            "announce the change." + off
        )
    if last in ("J1", "J2"):
        how = "focus moves to it" if last == "J1" else "a dialog appears"
        if outcome is Outcome.PASS:
            return f"{c} changes by itself, and {how} and says what changed."
        return (
            f"{c} changes by itself, and {how}, but it does not say what "
            "changed. Say what changed there, or put the content in an "
            "aria-live region."
        )
    if last == "N1":
        return f"{c} changes by itself, but we could not read what changed."
    return (
        f"{c} changes by itself. A person should check that screen reader users "
        "are told about the change."
    )


def _notes(page) -> list[str]:
    out = []
    roles = {lr.role for lr in page.mp.live_regions}
    if roles & {"marquee", "timer"}:
        out.append(
            "A timer or marquee counts as announced here, as the test's tool "
            "(ANDI) counts it, though screen readers may not announce it."
        )
    return out


def _finding(outcome, summary, rows, refs, inst=None, rationale="") -> Finding:
    f = Finding(
        test_id=TestId.T2D,
        test_name=TestId.T2D.tt_name,
        outcome=outcome,
        summary=summary,
        rationale=rationale or f"Spec {rows[-1]}.",
        decided_by=DecidedBy.RULE,
        rows=rows,
        instances=inst or [],
        evidence_refs=refs,
    )
    if outcome is Outcome.NEEDS_REVIEW:
        f.note = "This test could not be performed"
    return f


def _instances(st: State2D, page) -> list[Inst]:
    return [
        Inst(n, r, st.mp, st.j1.get(n) or {}, st.j2.get(n) or {}) for n, r in page.inst
    ]


def evaluate(st: State2D, evidence_refs: list[str]) -> Finding:
    row, page = applicability(st.mp)  # 2.C section 1
    if row.id in ("A1", "A2"):
        reason = (
            st.mp.error or "pass T failed"
            if row.id == "A1"
            else a2_note(st.mp, page.hints)
        )
        f = Finding.not_performed(TestId.T2D, reason)
        f.rows, f.decided_by, f.evidence_refs = (
            ["A1", f"2.C-{row.id}", "G1"],
            DecidedBy.RULE,
            evidence_refs,
        )
        return f
    if row.id in ("A3", "A4"):
        why = (
            "Nothing on this page changed by itself while we watched"
            if row.id == "A3"
            else "The changing content is the only content on this page"
        )
        return _finding(
            Outcome.DNA,
            f"{why}, so this test does not apply.",
            ["A2", f"2.C-{row.id}", "G1"],
            evidence_refs,
        )
    trace = ["A3"]
    results, sentences, inst = [], [], []
    for i in _instances(st, page):
        rows, outcome = instance_outcome(i)
        results.append((i.id, outcome))
        trace.append(f"{i.id}:" + "/".join(rows))
        sentences.append(_sentence(rows, i.region, outcome))
        inst.append(
            Instance(
                selector=i.region.content_css,
                frame_path=[i.region.frame_url] if i.region.frame else [],
                description=f"{i.id} [{'/'.join(rows)} {outcome.value}] "
                f"{len(changes(i.region))} changes, "
                f"{len(i.unlive())} outside a live region",
            )
        )
    gid, outcome = page_outcome(
        PageEvidence(
            applicability=row, instances=results, incomplete=[], complete_for_pass=True
        )
    )
    trace.append(gid)
    head = REVIEW_HEAD if outcome is Outcome.NEEDS_REVIEW else ""
    return _finding(
        outcome,
        " ".join(s for s in [head, *sentences, *_notes(page)] if s),
        trace,
        evidence_refs,
        inst,
        f"Spec {gid}. " + "; ".join(trace[1:-1]),
    )


# ── Questions ─────────────────────────────────────────────────────────────

CHOICES = ["sufficient", "not_sufficient", "unsure"]
J1_QUESTION = (
    "While the page updated by itself, focus moved to input.focused (image A "
    "before, image B after). Does the focused content itself say what changed "
    '(for example "New message from Ana" or "Prices updated at 2:15 PM"), so a '
    "screen reader user hearing it would know? Answer sufficient, "
    "not_sufficient or unsure."
)
J1_RUBRIC = (
    "sufficient: the focused content's own words say what changed. "
    "not_sufficient: it shows the new content but does not say it changed, or "
    "says nothing a listener would understand. unsure: whenever the evidence "
    "does not settle it."
)
J2_QUESTION = (
    "While the page updated by itself, a dialog opened (input.dialog: its role, "
    "name and text; image A). Does it tell the user what changed on the page? "
    "Answer sufficient, not_sufficient or unsure."
)
J2_RUBRIC = (
    "sufficient: the dialog's text says what changed (or what is about to). "
    "not_sufficient: it is about something else, or says nothing about the "
    "change. unsure: whenever the evidence does not settle it."
)


def _shot(mp: MotionPass, t: float, after: bool) -> str | None:
    """The frame just before or just after `t`."""
    pairs = list(zip(mp.frames, mp.shots, strict=False))
    if after:
        return next((s for f, s in pairs if f >= t), pairs[-1][1] if pairs else None)
    before = [s for f, s in pairs if f < t]
    return before[-1] if before else (pairs[0][1] if pairs else None)


def _images(evidence_refs: list[str], paths: list[str | None]) -> list[str]:
    base = evidence_refs[0].rsplit("/evidence/", 1)[0] if evidence_refs else ""
    return [f"{base}/{p}" for p in paths if p]


def questions_for(st: State2D, evidence_refs: list[str]) -> list[OpenQuestion]:
    row, page = applicability(st.mp)
    if row.id != "A5":
        return []
    out = []
    for i in _instances(st, page):
        rows, _ = instance_outcome(i)
        if rows[-1] != "N6" or rows[0] not in ("N3", "N4"):
            continue
        if rows[0] == "N4":
            t = i.region.focus_in[0]
            imgs = _images(
                evidence_refs, [_shot(st.mp, t, False), _shot(st.mp, t, True)]
            )
            out.append(
                OpenQuestion(
                    question_id=f"2.D-{i.id}-J1",
                    test_id=TestId.T2D,
                    kind="choice",
                    choices=CHOICES,
                    instance=i.id,
                    question=J1_QUESTION,
                    rubric=J1_RUBRIC,
                    input={"focused": i.region.text, "images": imgs},
                    evidence_paths=evidence_refs + imgs,
                )
            )
        else:
            d = i.dialog()
            imgs = _images(evidence_refs, [_shot(st.mp, st.mp.watch_s, True)])
            out.append(
                OpenQuestion(
                    question_id=f"2.D-{i.id}-J2",
                    test_id=TestId.T2D,
                    kind="choice",
                    choices=CHOICES,
                    instance=i.id,
                    question=J2_QUESTION,
                    rubric=J2_RUBRIC,
                    input={
                        "dialog": {"role": d.role, "name": d.name, "text": d.text},
                        "changed": content_name(i.region),
                        "images": imgs,
                    },
                    evidence_paths=evidence_refs + imgs,
                )
            )
    return out


def apply_answers(st: State2D, report) -> None:
    from tobi508.judgment import current_answer

    for q in report.questions:
        if q.test_id is not TestId.T2D:
            continue
        a = current_answer(report, q.question_id)
        if a is None or a.choice is None:
            continue
        inst, j = q.question_id.removeprefix("2.D-").rsplit("-", 1)
        (st.j1 if j == "J1" else st.j2)[inst] = {
            "choice": a.choice.choice,
            "reasons": a.choice.reasons,
            "decided_by": a.decided_by.value,
        }


async def collect(ctx: RunContext, walk: KeyboardWalk | None) -> State2D:
    mp = await motion.collect(ctx)
    mp.walk_unsettled = ctx.cache.get("walk_unsettled", mp.walk_unsettled)
    return State2D(mp=mp)


class Check2D:
    """2.D as a registered check (checks/base.py)."""

    test_id = TestId.T2D
    state_type = State2D
    uses_walk = False
    uses_motion = True  # pass T, started beside the walk
    about = (
        "It watches the page for a few seconds without touching it. For each "
        "piece of content that changes by itself, it checks that screen reader "
        "users are told: the change is inside a live region, or focus moves to "
        "it, or a dialog says what changed."
    )

    def walk_extras(self) -> list:
        return []

    async def collect(self, ctx: RunContext, walk: KeyboardWalk | None) -> State2D:
        return await collect(ctx, walk)

    def evaluate(self, state: State2D, evidence_refs: list[str]) -> Finding:
        return evaluate(state, evidence_refs)

    def questions(self, state: State2D, evidence_refs: list[str]) -> list[OpenQuestion]:
        return questions_for(state, evidence_refs)

    async def resume(self, ctx: RunContext, state: State2D, report) -> list[str]:
        apply_answers(state, report)
        return []


__all__ = ["Check2D", "State2D", "changes"]
