"""Test 2.B (2.2.2-blinking-moving-scrolling), from
docs/rules/2b-blinking-moving-scrolling.md (spec 1.0.0).

Reads pass T (motion.py) and the mechanism probe (mechanism.probe_shared,
one probe per content shared with 2.C). Uses 2.C's instance rows with 2.B's
meaning of stopped ("slowed" is no effect) and its own C1 row. Only
evaluate() and the row tables decide outcomes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from a11y_assist import mechanism, motion
from a11y_assist.checks import t2c
from a11y_assist.checks.base import RunContext
from a11y_assist.checks.t2c import (
    E_ROWS,
    INSTANCE_ROWS,
    J2_CHOICES,
    J2_QUESTION,
    J2_RUBRIC,
    POSITION,
    Inst,
    _images,
    _works,
    changed,
    instance_outcome,
)
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
from a11y_assist.motion import MotionPass, Probe, Region
from a11y_assist.walk import KeyboardWalk

STILL_MOVING_S = 5.0  # TT: "more than 5 seconds"
MIN_CHANGES = 3  # over the watch: one late change is not motion


class State2B(BaseModel):
    mp: MotionPass
    probes: dict[str, Probe] = Field(default_factory=dict)  # by instance id
    j1: dict[str, dict[str, Any]] = Field(default_factory=dict)  # essential, "m1"
    j2: dict[str, dict[str, Any]] = Field(default_factory=dict)  # evident, "m1"
    j3: dict[str, dict[str, Any]] = Field(default_factory=dict)  # text, "m1-e3"
    selected: list[str] = Field(default_factory=list)


# ── Terms ─────────────────────────────────────────────────────────────────


def still_moving(r: Region) -> bool:
    """A moving region (spec Terms, 0.2.0): it changes after 5 s, and in at
    least three frames over the watch; or the reads showed motion the frames
    could not (a long animation, a marquee, a playing video). 0.1.0 also
    asked that no gap be longer than its period plus 1 s, which random
    colours that repeat for two seconds broke (ACT efbfc7 inapplicable 3)."""
    if r.source == "dom":
        return False  # content that changes off screen: not seen to move
    if r.source != "pixels":
        return True
    t = r.changed_at
    return bool(t) and t[-1] >= STILL_MOVING_S and len(t) >= MIN_CHANGES


def moving(mp: MotionPass) -> list[tuple[str, Region]]:
    """Moving regions with ids m1, m2, ...: kind moving, or auto-updating
    with children that move, and still moving."""
    rs = [
        r
        for r in mp.regions
        if ("moving" in r.kinds or r.children_moved) and still_moving(r)
    ]
    return [(f"m{n}", r) for n, r in enumerate(rs, 1)]


MEDIA_TAGS = {"canvas", "img", "video", "svg", "iframe", "marquee", "object", "embed"}


def color_only(r: Region) -> bool:
    """A colour-only change (spec Terms): text, image sources, boxes and
    transforms stay the same while its pixels change, in content that is
    not drawn (a canvas, image, video or SVG changes pixels on its own), with
    a sign of styling: colours that differ between reads, style changes, or
    a running animation. Three reads alone missed a cycle that came back to
    its first colour on the reads."""
    same = lambda xs: len({x for x in xs if x is not None}) <= 1  # noqa: E731
    styled = (
        len({c for c in r.colors if c is not None}) > 1
        or r.attr_changes > 0
        or bool(r.animations)
    )
    return (
        r.source == "pixels"
        and r.tag not in MEDIA_TAGS
        and not r.children_moved
        and same(r.sigs)
        and same(r.transforms)
        and styled
    )


def video_failed(mp: MotionPass) -> list[str]:
    return sorted({m.css for m in mp.media if m.tag == "video" and m.error})


# ── Section 1 ─────────────────────────────────────────────────────────────

LOADING = re.compile(r"\bload", re.IGNORECASE)


def essential(st: State2B, n: str, r: Region) -> str:
    """J1's answer, with the spec's guard: content still moving at the end
    of the watch, on a page with controls, is not a loading animation."""
    a = st.j1.get(n) or {}
    choice = a.get("choice", "")
    if choice == "essential":
        late = r.source != "pixels" or (r.changed_at and r.changed_at[-1] >= 6.0)
        usable = any(e.kind == "control" for e in st.mp.elements)
        why = a.get("reasons", "")
        if (
            late
            and usable
            and LOADING.search(why)
            and not re.search(r"game|simulat|video|demonstrat", why, re.I)
        ):
            return "unsure"
    return choice


@dataclass
class Page:
    mp: MotionPass
    regions: list[tuple[str, Region]]  # moving
    applies: list[tuple[str, Region]]  # moving and not essential
    pending: list[str]  # J1 unsure or unanswered
    failed_video: list[str]


def page_of(st: State2B) -> Page:
    regs = moving(st.mp)
    applies, pending = [], []
    for n, r in regs:
        c = essential(st, n, r)
        if c == "not_essential":
            applies.append((n, r))
        elif c != "essential":
            pending.append(n)
    return Page(st.mp, regs, applies, pending, video_failed(st.mp))


def _only(p: Page) -> bool:
    mp = p.mp
    if not p.regions or not mp.elements or mp.elements_truncated:
        return False
    return all(any(changed(e, r) for _, r in p.regions) for e in mp.elements)


APPLICABILITY = [
    Row(
        "A1",
        lambda p: not p.mp.ok or bool(p.failed_video),
        Outcome.NEEDS_REVIEW,
        "p. 5",
    ),
    Row("A2", lambda p: not p.regions, Outcome.DNA, "p. 14 Applicability"),
    Row("A3", _only, Outcome.DNA, "p. 14 Applicability"),
    Row(
        "A4",
        lambda p: not p.applies and not p.pending,
        Outcome.DNA,
        "p. 14 EXCLUDE essential",
    ),
    Row(
        "A5", lambda p: not p.applies and bool(p.pending), Outcome.NEEDS_REVIEW, "Rule"
    ),
    Row("A6", lambda p: True, Outcome.PASS, "applies"),  # PASS here: "go on"
]


# ── Section 3: 2.C's rows with 2.B's stopped, and C1 before K6 ─────────────


def _c1(i: Inst) -> bool:
    k6 = next(r for r in INSTANCE_ROWS if r.id == "K6")
    return color_only(i.region) and i.region.states >= 3 and k6.when(i)


ROWS = [r for r in INSTANCE_ROWS if r.id != "K6"]
ROWS.insert(
    [r.id for r in ROWS].index("K7"),
    Row("C1", _c1, Outcome.NEEDS_REVIEW, "Abby, 2026-11-03; WCAG blinking"),
)
ROWS.insert(
    [r.id for r in ROWS].index("K7"),
    next(r for r in INSTANCE_ROWS if r.id == "K6"),
)


def _inst(st: State2B, n: str, r: Region) -> Inst:
    return Inst(
        id=n,
        region=r,
        probe=st.probes.get(n) or Probe(),
        elements=st.mp.elements,
        j1=st.j2.get(n) or {},  # 2.C's J1 (evident) is 2.B's J2
        j2=st.j3,
        slowed_counts=False,  # 2.B: stopped only
    )


# ── Plain language ────────────────────────────────────────────────────────


def name(r: Region) -> str:
    if r.source == "video" or r.tag == "video":
        return "A video"
    if r.source == "marquee" or r.tag == "marquee":
        return "Scrolling text"
    text = r.text.strip()
    return f'The content "{text[:60]}"' if text else "Some content"


def _sentence(row: str, r: Region, e: dict) -> str:
    c = name(r)
    mech = f'"{e["mech"].name}"' if e.get("mech") and e["mech"].name else "a control"
    if row == "E1":
        return (
            f"{mech} stops it, but it is not clear that it does (its name or "
            'icon does not say so). Give it a clear name like "Pause".'
        )
    if row == "E2":
        return f"{c} moves by itself for more than 5 seconds, and {mech} lets users stop it."
    if row == "E3":
        tests = ", ".join(e["missing"])
        return (
            f"{c} moves by itself, and {mech} stops it when pressed with the "
            f"keyboard. A person still needs to check {mech} for tests {tests}, "
            "which this tool does not test yet."
        )
    if row == "K6":
        return (
            f"{c} keeps moving for more than 5 seconds, and we found no way to "
            "stop or hide it in the three items before it, the three after it, "
            "or the first three on the page. Add a pause button next to it."
        )
    if row == "C1":
        return (
            f"{c} keeps changing color by itself, and we found no way to stop "
            "it. WCAG defines blinking as switching back and forth between two "
            f"visual states to draw attention. This cycles through {r.states} "
            "looks, so whether it counts as blinking is a call for a person: if "
            "it draws attention the way blinking does, it needs a pause control."
        )
    if row == "K2":
        return (
            f"{c} stops while a control has focus, which may be a pause-on-focus "
            "rather than a real pause. A person should check that the control "
            "itself stops it."
        )
    if row == "K5":
        return f"{c} moves by itself; a person should check its pause control."
    return (
        f"{c} moves by itself. A person should check that a control near it, "
        "or at the top of the page, can stop or hide it."
    )


def _finding(outcome, summary, rows, refs, inst=None, rationale="") -> Finding:
    f = Finding(
        test_id=TestId.T2B,
        test_name=TestId.T2B.tt_name,
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


def _notes(mp: MotionPass) -> list[str]:
    if mp.blink_markup:
        return [
            "This page marks some text to blink (an old HTML feature); it does "
            "not blink in Chrome, the browser we test with, but other browsers "
            "may differ."
        ]
    return []


def evaluate(st: State2B, evidence_refs: list[str]) -> Finding:
    p = page_of(st)
    row = next(r for r in APPLICABILITY if r.when(p))
    notes = _notes(st.mp)
    if row.id == "A1":
        why = st.mp.error or (
            "a video on the page could not play from the recording, so we "
            "could not see whether it moves"
        )
        f = Finding.not_performed(TestId.T2B, why)
        f.rows, f.decided_by, f.evidence_refs = (
            ["A1", "G1"],
            DecidedBy.RULE,
            evidence_refs,
        )
        return f
    if row.id == "A2":
        return _finding(
            Outcome.DNA,
            " ".join(
                [
                    f"We watched this page for {st.mp.watch_s:g} seconds. Nothing "
                    "on it moved, blinked or scrolled for more than 5 seconds, so "
                    "this test does not apply.",
                    *notes,
                ]
            ),
            ["A2", "G1"],
            evidence_refs,
        )
    if row.id == "A3":
        return _finding(
            Outcome.DNA,
            "The moving content is the only content on this page, so this test "
            "does not apply.",
            ["A3", "G1"],
            evidence_refs,
        )
    if row.id == "A4":
        names = "; ".join(name(r) for _, r in p.regions)
        return _finding(
            Outcome.DNA,
            f"{names} moves, but the movement is essential (it is what the "
            "content is, or it shows only while nothing can be used yet), so "
            "it does not need a pause, and this test does not apply.",
            ["A4", "G1"],
            evidence_refs,
        )
    if row.id == "A5":
        f = Finding.not_performed(
            TestId.T2B,
            "something on this page moves by itself, and whether the movement "
            "is essential is not settled yet.",
        )
        f.rows, f.decided_by, f.evidence_refs = (
            ["A5", "G1"],
            DecidedBy.RULE,
            evidence_refs,
        )
        return f
    trace = ["A6"]
    results, sentences, inst = [], [], []
    for n, r in p.applies:
        i = _inst(st, n, r)
        rows, outcome, e = instance_outcome(i, st.selected, ROWS)
        results.append((n, outcome))
        trace.append(f"{n}:" + "/".join(rows))
        sentences.append(_sentence(rows[-1], r, e))
        inst.append(
            Instance(
                selector=r.content_css,
                frame_path=[r.frame_url] if r.frame else [],
                description=f"{n} [{'/'.join(rows)} {outcome.value}] {r.source}"
                + (f" ({r.source_detail})" if r.source_detail else "")
                + (f", changed at {r.changed_at[:6]} s" if r.changed_at else ""),
            )
        )
    incomplete = (
        ["whether some moving content is essential is not settled"] if p.pending else []
    )
    gid, outcome = page_outcome(
        PageEvidence(
            applicability=row,
            instances=results,
            incomplete=incomplete,
            complete_for_pass=True,
        )
    )
    trace.append(gid)
    head = REVIEW_HEAD if outcome is Outcome.NEEDS_REVIEW else ""
    return _finding(
        outcome,
        " ".join(s for s in [head, *sentences, *notes] if s),
        trace,
        evidence_refs,
        inst,
        f"Spec {gid}. " + "; ".join(trace[1:-1]),
    )


# ── Questions ─────────────────────────────────────────────────────────────

J1_CHOICES = ["essential", "not_essential", "unsure"]
J1_QUESTION = (
    "input.content moves by itself (images A and B, about 1 s apart; the "
    "content is at input.box, x, y, width, height; input.timing). Would "
    "removing the movement fundamentally change what the content is or does, "
    "for example a loading animation shown while nothing on the page can be "
    "used yet, or a game or simulation whose motion is the point? Decorative "
    "motion, carousels, tickers, banners and background video are not "
    "essential. Answer essential, not_essential or unsure."
)
J1_RUBRIC = (
    "essential: the motion is the point (a game, a simulation, a "
    "demonstration of movement), or it is a loading indicator shown only "
    "while nothing can be used yet. not_essential: decoration, a carousel, a "
    "ticker, a banner, a background video, an animated image. unsure: "
    "whenever the images do not settle it. A false essential hides a real "
    "problem, so when in doubt answer unsure."
)
J2_EVIDENT_QUESTION = (
    "Pressing input.mechanism stopped the moving content in input.content. "
    "Image A (input.images) is the page as it loaded; the control is at "
    "input.box (x, y, width, height in that image), and input.position says "
    "where it is relative to the content. Would a user looking at the page "
    "recognize this control as a way to pause, stop or hide the moving "
    "content? Answer evident, not_evident or unsure."
)


def _two_frames(mp: MotionPass) -> list[str]:
    pairs = list(zip(mp.frames, mp.shots, strict=False))
    if not pairs:
        return []
    a = min(pairs, key=lambda p: abs(p[0] - 5.0))
    b = min(pairs, key=lambda p: abs(p[0] - 6.0))
    return [a[1], b[1]] if a != b else [a[1]]


def questions_for(st: State2B, evidence_refs: list[str]) -> list[OpenQuestion]:
    p = page_of(st)
    out: list[OpenQuestion] = []
    if not st.mp.ok or p.failed_video or not p.regions or _only(p):
        return out
    frames = _images(evidence_refs, _two_frames(st.mp))
    for n, r in p.regions:
        if n in st.j1:
            continue
        timing = r.source_detail or (
            f"changed at {r.changed_at[:8]} s, about every {r.period_s} s"
            if r.changed_at
            else ""
        )
        out.append(
            OpenQuestion(
                question_id=f"2.B-{n}-J1",
                test_id=TestId.T2B,
                kind="choice",
                choices=J1_CHOICES,
                instance=n,
                question=J1_QUESTION,
                rubric=J1_RUBRIC,
                input={
                    "content": name(r),
                    "box": r.box,
                    "timing": timing,
                    "images": frames,
                },
                evidence_paths=evidence_refs + frames,
            )
        )
    first = _images(evidence_refs, st.mp.shots[:1])
    for n, r in p.applies:
        i = _inst(st, n, r)
        for c in i.texts():
            qid = f"{n}-e{c.element}"
            if qid in st.j3 or i.j2_choice(c) == "no":
                continue
            out.append(
                OpenQuestion(
                    question_id=f"2.B-{qid}-J3",
                    test_id=TestId.T2B,
                    kind="choice",
                    choices=J2_CHOICES,
                    instance=n,
                    question=J2_QUESTION,
                    rubric=J2_RUBRIC,
                    input={
                        "text": st.mp.elements[c.element].name,
                        "position": POSITION[c.window],
                    },
                    evidence_paths=evidence_refs,
                )
            )
        mech = _works(i)
        if mech is not None and n not in st.j2:
            el = st.mp.elements[mech.element]
            out.append(
                OpenQuestion(
                    question_id=f"2.B-{n}-J2",
                    test_id=TestId.T2B,
                    kind="choice",
                    choices=t2c.J1_CHOICES,
                    instance=n,
                    question=J2_EVIDENT_QUESTION,
                    rubric=t2c.J1_RUBRIC,
                    input={
                        "mechanism": {"name": el.name, "role": el.role},
                        "box": el.box,
                        "content": name(r),
                        "position": POSITION[mech.window],
                        "images": first,
                    },
                    evidence_paths=evidence_refs + first,
                )
            )
    return out


def apply_answers(st: State2B, report) -> None:
    from a11y_assist.judgment import current_answer

    for q in report.questions:
        if q.test_id is not TestId.T2B:
            continue
        a = current_answer(report, q.question_id)
        if a is None or a.choice is None:
            continue
        key, j = q.question_id.removeprefix("2.B-").rsplit("-", 1)
        rec = {
            "choice": a.choice.choice,
            "key": a.choice.key,
            "reasons": a.choice.reasons,
            "decided_by": a.decided_by.value,
        }
        {"J1": st.j1, "J2": st.j2, "J3": st.j3}[j][key] = rec


async def collect(ctx: RunContext, walk: KeyboardWalk | None) -> State2B:
    """Pass T, then the probe for every moving region (up to three), before
    J1: J1 only excludes, so the probe never waits for an answer."""
    mp = await motion.collect(ctx)
    st = State2B(mp=mp, selected=sorted(ctx.selected))
    p = page_of(st)
    if not mp.ok or p.failed_video or _only(p):
        return st
    for k, (n, r) in enumerate(p.regions):
        if k >= mechanism.MAX_INSTANCES or ctx.out_of_time() or ctx.open_motion is None:
            continue  # not probed: K7
        st.probes[n] = await mechanism.probe_shared(ctx, mp, walk, r)
    return st


class Check2B:
    """2.B as a registered check (checks/base.py)."""

    test_id = TestId.T2B
    state_type = State2B
    uses_walk = True  # the probe reaches controls with the walk's Tab presses
    uses_motion = True
    about = (
        "It watches the page for a few seconds without touching it, and finds "
        "content that moves, blinks or scrolls by itself for more than 5 "
        "seconds, like animations, scrolling text and videos. It asks whether "
        "the movement is essential, then tries the controls near the content "
        "and at the top of the page with the keyboard, and checks that it "
        "stops."
    )

    def walk_extras(self) -> list:
        return []

    async def collect(self, ctx: RunContext, walk: KeyboardWalk | None) -> State2B:
        return await collect(ctx, walk)

    def evaluate(self, state: State2B, evidence_refs: list[str]) -> Finding:
        return evaluate(state, evidence_refs)

    def questions(self, state: State2B, evidence_refs: list[str]) -> list[OpenQuestion]:
        return questions_for(state, evidence_refs)

    async def resume(self, ctx: RunContext, state: State2B, report) -> list[str]:
        """Answers in force, then J3's key (once per run, shared with 2.C)."""
        apply_answers(state, report)
        p = page_of(state)
        await mechanism.press_answered(
            ctx, state.mp, state.j3, state.probes, dict(p.applies)
        )
        return []


__all__ = ["Check2B", "State2B", "moving", "still_moving", "color_only", "E_ROWS"]
