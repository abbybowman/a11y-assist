"""Test 2.C (2.2.2-auto-updating), from docs/rules/2c-auto-updating.md
(draft: registered in tests/drafts.py only, so the server gives no outcome).

Reads pass T (motion.py, shared with 2.A, 2.B and 2.D) and the mechanism
probe's evidence (motion.Probe). The probe is not built yet, so every
instance is "not probed" (K7, NEEDS REVIEW) until it is; its rows are tested
on hand-built evidence. Only evaluate() and the row tables decide outcomes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from a11y_assist import motion
from a11y_assist.checks.base import RunContext
from a11y_assist.engine import PageEvidence, Row, page_outcome
from a11y_assist.models import (
    REVIEW_HEAD,
    DecidedBy,
    Finding,
    Instance,
    OpenQuestion,
    Outcome,
    TestId,
)
from a11y_assist.motion import Element, MotionPass, Probe, Region
from a11y_assist.walk import KeyboardWalk

# A region still changing at this time is an instance (OPEN O1 in the spec).
STILL_CHANGING_S = 5.0

# J2 is asked only for text that mentions a way to stop it (spec section 4).
MENTION = re.compile(
    r"\+|hotkey|shortcut|\bpause|\bstop|\bhide|\bfreeze|turn off", re.IGNORECASE
)


class State2C(BaseModel):
    mp: MotionPass
    probes: dict[str, Probe] = Field(default_factory=dict)  # by instance id
    j1: dict[str, dict[str, Any]] = Field(default_factory=dict)  # by instance id
    j2: dict[str, dict[str, Any]] = Field(default_factory=dict)  # "r1-e12"
    selected: list[str] = Field(default_factory=list)  # TT IDs in this call


# ── Section 1: which regions are instances, and hints ─────────────────────


def stopped_early(r: Region) -> bool:
    """Stopped changing before 5 s (a spinner replaced by content, a late
    load, or an update slower than half the watch). OPEN O1 in the spec: not
    an instance, but a hint, so never DOES NOT APPLY on it."""
    return bool(r.changed_at) and r.changed_at[-1] < STILL_CHANGING_S


def instances(mp: MotionPass) -> list[tuple[str, Region]]:
    """Auto-updating regions that are not one burst, with ids r1, r2, ..."""
    rs = [r for r in mp.regions if "updating" in r.kinds and not stopped_early(r)]
    return [(f"r{n}", r) for n, r in enumerate(rs, 1)]


def hints(mp: MotionPass) -> list[str]:
    """Signs the page updates more slowly than the watch, or with data a
    recording cannot replay (A2). Plain words; no outcome."""
    out = []
    for p in mp.polls:
        every = f" about every {p.gap_ms / 1000:.1f} s" if p.gap_ms else ""
        out.append(f"it asks its server for new data{every}")
        break
    slow = sorted({t.ms for t in mp.timers if t.ms > mp.watch_s * 1000})
    if slow:
        out.append(f"it sets a timer of {slow[0] / 1000:g} s, longer than we watched")
    moving = {f"{r.frame}|{r.content_css}" for _, r in instances(mp)}
    if any(c not in moving for c in mp.carousels):
        out.append("it has a carousel that did not change while we watched")
    if any("updating" in r.kinds and stopped_early(r) for r in mp.regions):
        out.append("some content changed soon after the page loaded, then stopped")
    return out


def only_content(mp: MotionPass, inst: list[tuple[str, Region]]) -> bool:
    """A4: the changing content covers every element of the page."""
    if not inst or not mp.elements or mp.elements_truncated:
        return False
    # Changes we could not place more closely than the whole page are not
    # "the only content" (a focus ring once made a region of <main>).
    if any(r.tag in ("html", "body", "main") for _, r in inst):
        return False
    inside = {i for _, r in inst for i in r.elements}
    return inside >= {e.i for e in mp.elements}


@dataclass
class Page:
    mp: MotionPass
    inst: list[tuple[str, Region]]
    hints: list[str]


APPLICABILITY = [
    Row("A1", lambda p: not p.mp.ok, Outcome.NEEDS_REVIEW, "p. 5; spec rule"),
    Row(
        "A2",
        lambda p: not p.inst and bool(p.hints),
        Outcome.NEEDS_REVIEW,
        "p. 15 Identify Content; plan risks 4-5",
    ),
    Row("A3", lambda p: not p.inst, Outcome.DNA, "p. 15 Applicability"),
    Row("A4", lambda p: only_content(p.mp, p.inst), Outcome.DNA, "p. 15 Applicability"),
    Row("A5", lambda p: True, Outcome.PASS, "applies"),  # PASS here: "go on"
]


def applicability(mp: MotionPass) -> tuple[Row, Page]:
    page = Page(mp, instances(mp), hints(mp))
    row = next(r for r in APPLICABILITY if r.when(page))
    return row, page


# ── Section 3: instance rows ──────────────────────────────────────────────


@dataclass
class Inst:
    id: str
    region: Region
    probe: Probe
    elements: list[Element]
    j1: dict[str, Any]
    j2: dict[str, dict[str, Any]]
    slowed_counts: bool = True  # 2.C: a frequency control counts (K3)

    def held(self, c) -> bool:
        ok = ("stopped", "slowed") if self.slowed_counts else ("stopped",)
        return c.result in ok

    def controls(self):
        return [c for c in self.probe.candidates if c.kind == "control"]

    def texts(self):
        return [c for c in self.probe.candidates if c.kind == "text"]

    def j2_choice(self, c) -> str:
        """J2 for a text candidate: "no" without asking when its text names
        no way to stop anything (spec section 4)."""
        a = self.j2.get(f"{self.id}-e{c.element}")
        if a:
            return a.get("choice", "")
        text = self.elements[c.element].name if c.element < len(self.elements) else ""
        return "" if MENTION.search(text) else "no"


def _works(i: Inst):
    """The candidate that worked (K3 or K4), or None."""
    for c in i.controls():
        if i.held(c) and c.focus_only not in (None, "stopped"):
            return c
    for c in i.texts():
        if c.key and i.held(c):
            return c
    return None


INSTANCE_ROWS = [
    Row(
        "K1",
        lambda i: (
            i.probe.reads_failed
            or (
                not any(i.held(c) for c in i.probe.candidates)
                and any(c.result == "unreliable" for c in i.probe.candidates)
            )
        ),
        Outcome.NEEDS_REVIEW,
        "Spec rule",
    ),
    Row(
        "K2",
        lambda i: any(i.held(c) and c.focus_only == "stopped" for c in i.controls()),
        Outcome.NEEDS_REVIEW,
        "Understanding 2.2.2; plan item 12",
    ),
    Row(
        "K3",
        lambda i: any(
            i.held(c) and c.focus_only not in (None, "stopped") for c in i.controls()
        ),
        None,  # works: the E rows decide
        "p. 15 HtT 1-2; G186; G4",
    ),
    Row(
        "K4",
        lambda i: any(c.key and i.held(c) for c in i.texts()),
        None,
        "p. 15 HtT 1 (DHS #114); plan Q10",
    ),
    Row("K5", lambda i: bool(i.probe.cannot_try), Outcome.NEEDS_REVIEW, "Spec rule"),
    Row(
        "K6",
        lambda i: (
            i.probe.probed
            and i.probe.untried == 0
            and all(c.result == "no_effect" for c in i.controls())
            and all(i.j2_choice(c) == "no" for c in i.texts())
        ),
        Outcome.FAIL,
        "p. 16 ER 1-2",
    ),
    Row(
        "K7",
        lambda i: (
            not i.probe.probed
            or i.probe.untried > 0
            # Text is asked about (J2), never pressed: only controls count.
            or any(c.result in ("unreachable", "untried") for c in i.controls())
        ),
        Outcome.NEEDS_REVIEW,
        "p. 5",
    ),
    Row("K8", lambda i: True, Outcome.NEEDS_REVIEW, "Spec rule"),
]


# 3c: the tests a mechanism needs (ER 3; Abby, 2026-11-03, plan Q4).
def er3_tests(mech: Element, in_frame: bool) -> list[str]:
    out = ["4.A", "4.B", "4.C"]
    if mech.stop or mech.kind == "control":
        out += ["4.D", "4.E", "4.F"]
    if mech.role in ("checkbox", "switch", "slider", "textbox", "combobox", "radio"):
        out += ["5.A", "5.B", "5.C", "5.D"]
    if mech.role in ("link", "button"):
        out.append("6.A")
    if mech.kind in ("image", "control"):
        out += ["7.A", "7.E"]  # an icon cannot be told from its name
    if in_frame:
        out.append("12.D")
    out.append("13.A")  # a state shown by color cannot be ruled out
    if mech.kind == "text":
        out.append("13.B")
    if mech.name:
        out += ["13.C", "18.A"]
    return out


def er3_missing(tests: list[str], selected: list[str]) -> list[str]:
    from a11y_assist.checks import REGISTRY

    built = {t.value for t in REGISTRY}
    return [t for t in tests if t not in built or t not in selected]


E_ROWS = [
    Row(
        "E1",
        lambda e: e["j1"] == "not_evident",
        Outcome.FAIL,
        'p. 16 ER 1 ("an evident mechanism")',
    ),
    Row(
        "E2",
        lambda e: e["j1"] == "evident" and not e["missing"],
        Outcome.PASS,
        "p. 16 ER 1-3",
    ),
    Row(
        "E3",
        lambda e: e["j1"] == "evident",
        Outcome.NEEDS_REVIEW,
        "p. 16 ER 3; plan Q4",
    ),
    Row("E4", lambda e: True, Outcome.NEEDS_REVIEW, "Spec rule"),
]


def instance_outcome(i: Inst, selected: list[str]) -> tuple[list[str], Outcome, dict]:
    """(rows, outcome, details) for one instance, first match wins."""
    for row in INSTANCE_ROWS:
        if not row.when(i):
            continue
        if row.outcome is not None:
            return [row.id], row.outcome, {}
        mech = _works(i)
        el = i.elements[mech.element]
        missing = er3_missing(er3_tests(el, i.region.frame > 0), selected)
        e = {"j1": (i.j1 or {}).get("choice", ""), "missing": missing, "mech": el}
        erow = next(r for r in E_ROWS if r.when(e))
        return [row.id, erow.id], erow.outcome, e
    raise AssertionError("K8 always matches")


# ── Plain language ────────────────────────────────────────────────────────


def content_name(r: Region) -> str:
    text = r.text.strip()
    if r.carousel:
        return f'The carousel "{text[:60]}"' if text else "A carousel"
    return f'The content "{text[:60]}"' if text else "Some content"


def _sentence(row: str, r: Region, e: dict) -> str:
    c = content_name(r)
    mech = f'"{e["mech"].name}"' if e.get("mech") and e["mech"].name else "a control"
    if row == "E1":
        return (
            f"{mech} pauses it, but it is not clear that it does (its name or "
            'icon does not say so). Give it a clear name like "Pause".'
        )
    if row == "E2":
        return f"{c} changes by itself, and {mech} lets users pause it."
    if row == "E3":
        tests = ", ".join(e["missing"])
        return (
            f"{c} changes by itself, and {mech} pauses it when pressed with the "
            f"keyboard. A person still needs to check {mech} for tests {tests}, "
            "which this tool does not test yet."
        )
    if row == "K6":
        return (
            f"{c} changes by itself, and we found no way to pause, stop or hide "
            "it in the three items before it, the three after it, or the first "
            "three on the page. Add a pause button next to it."
        )
    if row == "K2":
        return (
            f"{c} stops while a control has focus, which may be a pause-on-focus "
            "rather than a real pause. A person should check that the control "
            "itself pauses it."
        )
    if row == "K5":
        return f"{c} changes by itself; a person should check its pause control."
    if row == "K7":
        return (
            f"{c} changes by itself. A person should check that a control near "
            "it, or at the top of the page, can pause, stop or hide it."
        )
    return f"{c} changes by itself. A person should check that users can pause it."


def _finding(outcome, summary, rows, refs, inst=None, rationale="") -> Finding:
    f = Finding(
        test_id=TestId.T2C,
        test_name=TestId.T2C.tt_name,
        outcome=outcome,
        summary=summary,
        rationale=rationale or f"Spec {rows[-1]}.",
        decided_by=DecidedBy.RULE,
        rows=rows,
        instances=inst or [],
        evidence_refs=refs,
    )
    if outcome is Outcome.NEEDS_REVIEW:  # principle 2, G3
        f.note = "This test could not be performed"
    return f


def _instances(st: State2C, page: Page) -> list[Inst]:
    return [
        Inst(
            id=n,
            region=r,
            probe=st.probes.get(n) or Probe(),
            elements=st.mp.elements,
            j1=st.j1.get(n) or {},
            j2=st.j2,
        )
        for n, r in page.inst
    ]


def evaluate(st: State2C, evidence_refs: list[str]) -> Finding:
    row, page = applicability(st.mp)
    if row.id == "A1":
        f = Finding.not_performed(TestId.T2C, st.mp.error or "pass T failed")
        f.rows, f.decided_by, f.evidence_refs = (
            ["A1", "G1"],
            DecidedBy.RULE,
            evidence_refs,
        )
        return f
    if row.id == "A2":
        reason = (
            "We saw signs that this page updates by itself ("
            + "; ".join(page.hints)
            + "), but nothing changed while we watched. A person should watch "
            "the page for a minute."
        )
        f = Finding.not_performed(TestId.T2C, reason)
        f.rows, f.decided_by, f.evidence_refs = (
            ["A2", "G1"],
            DecidedBy.RULE,
            evidence_refs,
        )
        return f
    if row.id == "A3":
        return _finding(
            Outcome.DNA,
            "Nothing on this page changed by itself while we watched, so this "
            "test does not apply.",
            ["A3", "G1"],
            evidence_refs,
        )
    if row.id == "A4":
        return _finding(
            Outcome.DNA,
            "The changing content is the only content on this page, so this "
            "test does not apply.",
            ["A4", "G1"],
            evidence_refs,
        )
    trace = ["A5"]
    results, sentences, inst = [], [], []
    for i in _instances(st, page):
        rows, outcome, e = instance_outcome(i, st.selected)
        results.append((i.id, outcome))
        trace.append(f"{i.id}:" + "/".join(rows))
        sentences.append(_sentence(rows[-1], i.region, e))
        inst.append(
            Instance(
                selector=i.region.content_css,
                frame_path=[i.region.frame_url] if i.region.frame else [],
                description=f"{i.id} [{'/'.join(rows)} {outcome.value}] "
                f"changed at {i.region.changed_at[:6]} s",
            )
        )
    gid, outcome = page_outcome(
        PageEvidence(
            applicability=row,
            instances=results,
            incomplete=[],
            complete_for_pass=True,
        )
    )
    trace.append(gid)
    if page.hints:
        sentences.append(
            "We also saw signs of updates we did not see happen: "
            + "; ".join(page.hints)
            + "."
        )
    head = REVIEW_HEAD if outcome is Outcome.NEEDS_REVIEW else ""
    return _finding(
        outcome,
        " ".join([s for s in [head, *sentences] if s]),
        trace,
        evidence_refs,
        inst,
        f"Spec {gid}. " + "; ".join(trace[1:-1]),
    )


# ── Questions (J1, J2) and answers ────────────────────────────────────────

J1_CHOICES = ["evident", "not_evident", "unsure"]
J1_QUESTION = (
    "Pressing input.mechanism stopped the content in input.content (image A "
    "shows the content and the control). Would a user looking at the page "
    "recognize this control as a way to pause, stop, hide, or slow the "
    "changing content? Answer evident, not_evident or unsure."
)
J1_RUBRIC = (
    "evident: its visible name or icon says pause, stop, hide, play/pause or "
    "slower, and it is in view with the content or at the top of the page. "
    'not_evident: it says something else ("Menu", "Next"), or has no visible '
    "name or icon. unsure: whenever the image does not settle it."
)
J2_CHOICES = ["describes", "no", "unsure"]
J2_QUESTION = (
    "input.text is page text near the changing content (input.position). Does "
    "it tell users how to pause, stop, hide or slow that content? If it names "
    "a key combination, put it in key exactly as written. Answer describes, no "
    "or unsure."
)
J2_RUBRIC = (
    "describes: the text says how to pause, stop, hide or slow this content "
    "(a key, a button it names, a setting). no: it says nothing about that. "
    "unsure: whenever the text does not settle it."
)


def questions_for(st: State2C, evidence_refs: list[str]) -> list[OpenQuestion]:
    """J2 for text candidates that mention a way to stop something, J1 for a
    mechanism that worked. None until the probe gives candidates."""
    _, page = applicability(st.mp)
    out = []
    for i in _instances(st, page):
        for c in i.texts():
            qid = f"{i.id}-e{c.element}"
            if qid in st.j2 or i.j2_choice(c) == "no":
                continue
            el = st.mp.elements[c.element]
            out.append(
                OpenQuestion(
                    question_id=f"2.C-{qid}-J2",
                    test_id=TestId.T2C,
                    kind="choice",
                    choices=J2_CHOICES,
                    instance=i.id,
                    question=J2_QUESTION,
                    rubric=J2_RUBRIC,
                    input={"text": el.name, "position": c.window},
                    evidence_paths=evidence_refs,
                )
            )
        mech = _works(i)
        if mech is not None and not i.j1:
            el = st.mp.elements[mech.element]
            out.append(
                OpenQuestion(
                    question_id=f"2.C-{i.id}-J1",
                    test_id=TestId.T2C,
                    kind="choice",
                    choices=J1_CHOICES,
                    instance=i.id,
                    question=J1_QUESTION,
                    rubric=J1_RUBRIC,
                    input={
                        "mechanism": {"name": el.name, "role": el.role},
                        "content": content_name(i.region),
                        "position": mech.window,
                    },
                    evidence_paths=evidence_refs,
                )
            )
    return out


def apply_answers(st: State2C, report) -> None:
    from a11y_assist.judgment import current_answer

    for q in report.questions:
        if q.test_id is not TestId.T2C:
            continue
        a = current_answer(report, q.question_id)
        if a is None or a.choice is None:
            continue
        key = q.question_id.removeprefix("2.C-").rsplit("-", 1)
        rec = {
            "choice": a.choice.choice,
            "key": a.choice.key,
            "reasons": a.choice.reasons,
            "decided_by": a.decided_by.value,
        }
        (st.j1 if key[1] == "J1" else st.j2)[key[0]] = rec


async def collect(ctx: RunContext, walk: KeyboardWalk | None) -> State2C:
    mp = await motion.collect(ctx)
    return State2C(mp=mp, selected=sorted(ctx.selected))


class Check2C:
    """2.C as a draft check (tests/drafts.py) until its spec reaches 1.0.0."""

    test_id = TestId.T2C
    state_type = State2C
    uses_walk = False
    about = (
        "It watches the page for a few seconds without touching it, and finds "
        "content that changes by itself, like carousels, tickers and counters. "
        "For now a person must check that each one can be paused, stopped or "
        "hidden: the tool does not yet try the controls near it."
    )

    def walk_extras(self) -> list:
        return []

    async def collect(self, ctx: RunContext, walk: KeyboardWalk | None) -> State2C:
        return await collect(ctx, walk)

    def evaluate(self, state: State2C, evidence_refs: list[str]) -> Finding:
        return evaluate(state, evidence_refs)

    def questions(self, state: State2C, evidence_refs: list[str]) -> list[OpenQuestion]:
        return questions_for(state, evidence_refs)

    async def resume(self, ctx: RunContext, state: State2C, report) -> list[str]:
        apply_answers(state, report)
        return []


__all__ = ["Check2C", "State2C", "applicability", "instances", "content_name"]
