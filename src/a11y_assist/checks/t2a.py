"""Test 2.A (1.4.2-audio-control), from docs/rules/2a-audio-control.md
(draft: tests/drafts.py only).

Reads pass T (motion.py: media state at each read, loudness from the
recorded bytes, Web Audio, the media store) and the mechanism probe with the
top window only and 2.A's meaning of stopped (mechanism.audio_watch). No
"evident" question: ER 1 does not ask for it. Only evaluate() and the row
tables decide outcomes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from a11y_assist import mechanism, motion
from a11y_assist.checks.base import RunContext
from a11y_assist.checks.t2c import (
    INSTANCE_ROWS,
    J2_CHOICES,
    POSITION,
    Inst,
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
from a11y_assist.motion import Media, MotionPass, Probe, Region
from a11y_assist.walk import KeyboardWalk

AUDIBLE_DB = -40.0  # spec Terms: samples above -40 dBFS
MORE_THAN_S = 3.0  # TT: "for more than 3 seconds"
READ_AT = 3.5  # the read that decides "auto-playing" (spec Terms)
STREAMING = re.compile(
    r"^https?://(www\.)?(youtube(-nocookie)?\.com/embed|player\.vimeo\.com)/.*autoplay=1",
    re.IGNORECASE,
)

TAB_MUTE_NOTE = (
    "Chrome can mute a tab, but the test asks for a control within the first "
    "three items of the page, so a tab mute does not count here."
)


class Audio(BaseModel):
    """One auto-playing audio (spec Terms): a media element or Web Audio."""

    id: str  # a1, a2, ...
    kind: str  # media | webaudio
    frame: int = 0
    frame_url: str = ""
    css: str = ""
    src: str = ""
    duration: float | None = None
    loop: bool = False
    loudness: float | None = None
    measured: bool = True
    why: str = ""  # why it could not be measured (A2)


class State2A(BaseModel):
    mp: MotionPass
    audio: list[Audio] = Field(default_factory=list)
    probes: dict[str, Probe] = Field(default_factory=dict)  # by audio id
    j2: dict[str, dict[str, Any]] = Field(default_factory=dict)  # "a1-e0"
    selected: list[str] = Field(default_factory=list)


# ── Terms: what plays by itself ───────────────────────────────────────────


def _reads(mp: MotionPass) -> dict[tuple[int, str], list[Media]]:
    out: dict[tuple[int, str], list[Media]] = {}
    for m in mp.media:
        out.setdefault((m.frame, m.css), []).append(m)
    return out


def find_audio(mp: MotionPass) -> list[Audio]:
    """Auto-playing audio at the 3.5 s read, with no key pressed, and audio
    that would play but cannot be measured (A2)."""
    over = {m["url"] for m in mp.media_store if m.get("over_cap")}
    out: list[Audio] = []
    for (frame, css), reads in _reads(mp).items():
        first, at = reads[0], min(reads, key=lambda m: abs(m.at - READ_AT))
        a = Audio(
            id="",
            kind="media",
            frame=frame,
            css=css,
            src=at.src,
            duration=at.duration,
            loop=at.loop,
            loudness=mp.loudness.get(at.src),
        )
        if at.error:
            a.measured, a.why = False, "it reported an error while playing"
        elif at.src.startswith("blob:") and not at.paused:
            a.measured, a.why = False, "it streams its media"
        elif at.src.split("#", 1)[0] in over and (at.paused or at.time <= first.time):
            a.measured, a.why = False, "its file is larger than we record"
        if a.measured:
            playing = (
                not at.paused
                and not at.muted
                and at.volume > 0
                and at.time > first.time
            )
            if not playing:
                continue
            left = None if at.duration is None else at.duration - first.time
            if not (at.loop or left is None or left > MORE_THAN_S):
                continue  # stops within 3 s (G60): not an instance
            if a.loudness is None:
                a.measured, a.why = False, "we could not measure how loud it is"
            elif a.loudness <= AUDIBLE_DB:
                continue  # silent (ACT 80f0bf inapplicable 2)
        out.append(a)
    for src in mp.iframes:
        if STREAMING.match(src):
            out.append(
                Audio(
                    id="",
                    kind="media",
                    src=src[:200],
                    measured=False,
                    why="it is a streaming video player that we cannot play "
                    "from a recording",
                )
            )
    if "running" in mp.audio_states:
        out.append(
            Audio(
                id="",
                kind="webaudio",
                measured=False,
                why="it makes sound with Web Audio, which we cannot measure",
            )
        )
    for n, a in enumerate(out, 1):
        a.id = f"a{n}"
    return out


def region_of(a: Audio, mp: MotionPass) -> Region:
    """The probe's handle on the audio (mechanism.audio_watch)."""
    return Region(
        key=f"audio|{a.frame}|{a.css}",
        frame=a.frame,
        frame_url=a.frame_url,
        css=a.css,
        tag="audiocontext" if a.kind == "webaudio" else "media",
        content_css=a.css,
        source="audio",
    )


# ── Rows ──────────────────────────────────────────────────────────────────


@dataclass
class Page:
    mp: MotionPass
    audio: list[Audio] = field(default_factory=list)

    @property
    def measured(self) -> list[Audio]:
        return [a for a in self.audio if a.measured]


APPLICABILITY = [
    Row("A1", lambda p: not p.mp.ok, Outcome.NEEDS_REVIEW, "p. 5"),
    Row(
        "A2",
        lambda p: bool(p.audio) and not p.measured,
        Outcome.NEEDS_REVIEW,
        "plan items 13-14, 17",
    ),
    Row("A3", lambda p: not p.audio, Outcome.DNA, "p. 13 Applicability"),
    Row("A4", lambda p: True, Outcome.PASS, "applies"),  # PASS here: "go on"
]

# 2.A asks no "evident" question (ER 1 does not say evident).
E_ROWS = [
    Row("E2", lambda e: not e["missing"], Outcome.PASS, "p. 13 ER 1-3"),
    Row("E3", lambda e: True, Outcome.NEEDS_REVIEW, "p. 13 ER 3; plan Q4"),
]


def _inst(st: State2A, a: Audio) -> Inst:
    return Inst(
        id=a.id,
        region=region_of(a, st.mp),
        probe=st.probes.get(a.id) or Probe(),
        elements=st.mp.elements,
        j1={},
        j2=st.j2,
        slowed_counts=False,
    )


def _what(a: Audio) -> str:
    return "Web Audio" if a.kind == "webaudio" else "Audio"


def _sentence(row: str, a: Audio, e: dict) -> str:
    mech = f'"{e["mech"].name}"' if e.get("mech") and e["mech"].name else "a control"
    w = _what(a)
    if row == "E2":
        return f"{w} plays by itself when the page loads, and {mech}, near the top of the page, stops it."
    if row == "E3":
        tests = ", ".join(e["missing"])
        return (
            f"{w} plays by itself, and {mech} stops it when pressed with the "
            f"keyboard. A person still needs to check {mech} for tests {tests}, "
            "which this tool does not test yet."
        )
    if row == "K6":
        return (
            f"{w} plays by itself for more than 3 seconds, and nothing among the "
            "first three items on the page stops it or turns it down. Screen "
            "reader users hear it over their screen reader. Put a pause or mute "
            "button first on the page, or do not start the audio until the user "
            "asks."
        )
    if row == "U1":
        return f"{w} on this page would play by itself, but {a.why}. A person should load the page and listen."
    if row == "K2":
        return (
            f"{w} stops while a control has focus, which may be a pause on "
            "focus rather than a real control. A person should check it."
        )
    return (
        f"{w} plays by itself. A person should check that one of the first "
        "three items on the page can pause it, stop it or turn it down."
    )


def _finding(outcome, summary, rows, refs, inst=None, rationale="") -> Finding:
    f = Finding(
        test_id=TestId.T2A,
        test_name=TestId.T2A.tt_name,
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


def evaluate(st: State2A, evidence_refs: list[str]) -> Finding:
    p = Page(st.mp, st.audio)
    row = next(r for r in APPLICABILITY if r.when(p))
    if row.id == "A1":
        f = Finding.not_performed(TestId.T2A, st.mp.error or "pass T failed")
        f.rows, f.decided_by, f.evidence_refs = (
            ["A1", "G1"],
            DecidedBy.RULE,
            evidence_refs,
        )
        return f
    if row.id == "A2":
        whys = "; ".join(sorted({a.why for a in p.audio}))
        f = Finding.not_performed(
            TestId.T2A,
            f"this page has audio we could not play or measure from our "
            f"recording ({whys}). A person should load the page and listen.",
        )
        f.rows, f.decided_by, f.evidence_refs = (
            ["A2", "G1"],
            DecidedBy.RULE,
            evidence_refs,
        )
        return f
    if row.id == "A3":
        return _finding(
            Outcome.DNA,
            f"We watched this page for {st.mp.watch_s:g} seconds with autoplay "
            "allowed. No audio played by itself for more than 3 seconds, so "
            "this test does not apply.",
            ["A3", "G1"],
            evidence_refs,
        )
    trace = ["A4"]
    results, sentences, inst = [], [], []
    for a in p.audio:
        if not a.measured:
            rows, outcome, e = ["U1"], Outcome.NEEDS_REVIEW, {}
        else:
            rows, outcome, e = instance_outcome(
                _inst(st, a), st.selected, INSTANCE_ROWS, E_ROWS
            )
        results.append((a.id, outcome))
        trace.append(f"{a.id}:" + "/".join(rows))
        sentences.append(_sentence(rows[-1], a, e))
        inst.append(
            Instance(
                selector=a.css or None,
                description=f"{a.id} [{'/'.join(rows)} {outcome.value}] {a.kind}"
                + (f" {a.src[:120]}" if a.src else "")
                + (f", peak {a.loudness} dBFS" if a.loudness is not None else ""),
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
        " ".join(s for s in [head, *sentences, TAB_MUTE_NOTE] if s),
        trace,
        evidence_refs,
        inst,
        f"Spec {gid}. " + "; ".join(trace[1:-1]),
    )


# ── Questions: 2.C's J2 for text in the top window ──────────────────────────


# 2.C's J2 in 2.A's words: ER 1 counts pausing, stopping, or controlling the
# volume of the audio (muting included), not hiding or slowing.
J2_AUDIO_QUESTION = (
    "input.text is page text among the first three items on the page "
    "(input.position). Audio on this page plays by itself when it loads. Does "
    "the text tell users how to pause or stop that audio, or turn its volume "
    "down or mute it? If it names a key combination, put it in key exactly as "
    "written. Answer describes, no or unsure."
)
J2_AUDIO_RUBRIC = (
    "describes: the text says how to pause, stop, mute or turn down the "
    "audio (a key, a button it names, a setting). no: it says nothing about "
    "that. unsure: whenever the text does not settle it."
)


def questions_for(st: State2A, evidence_refs: list[str]) -> list[OpenQuestion]:
    out = []
    if not st.mp.ok:
        return out
    for a in st.audio:
        if not a.measured:
            continue
        i = _inst(st, a)
        for c in i.texts():
            qid = f"{a.id}-e{c.element}"
            if qid in st.j2 or i.j2_choice(c) == "no":
                continue
            out.append(
                OpenQuestion(
                    question_id=f"2.A-{qid}-J2",
                    test_id=TestId.T2A,
                    kind="choice",
                    choices=J2_CHOICES,
                    instance=a.id,
                    question=J2_AUDIO_QUESTION,
                    rubric=J2_AUDIO_RUBRIC,
                    input={
                        "text": st.mp.elements[c.element].name,
                        "position": POSITION[c.window],
                    },
                    evidence_paths=evidence_refs,
                )
            )
    return out


def apply_answers(st: State2A, report) -> None:
    from a11y_assist.judgment import current_answer

    for q in report.questions:
        if q.test_id is not TestId.T2A:
            continue
        a = current_answer(report, q.question_id)
        if a is None or a.choice is None:
            continue
        key = q.question_id.removeprefix("2.A-").rsplit("-", 1)[0]
        st.j2[key] = {
            "choice": a.choice.choice,
            "key": a.choice.key,
            "reasons": a.choice.reasons,
            "decided_by": a.decided_by.value,
        }


async def collect(ctx: RunContext, walk: KeyboardWalk | None) -> State2A:
    mp = await motion.collect(ctx)
    st = State2A(mp=mp, selected=sorted(ctx.selected))
    if not mp.ok:
        return st
    st.audio = find_audio(mp)
    for a in st.audio:
        if not a.measured or ctx.out_of_time() or ctx.open_motion is None:
            continue
        st.probes[a.id] = await mechanism.probe_shared(ctx, mp, walk, region_of(a, mp))
    return st


class Check2A:
    """2.A as a draft check (tests/drafts.py) until its spec reaches 1.0.0."""

    test_id = TestId.T2A
    state_type = State2A
    uses_walk = True  # the probe reaches controls with the walk's Tab presses
    uses_motion = True
    about = (
        "It opens the page with autoplay allowed and listens for a few "
        "seconds without touching it. If audio plays by itself for more than "
        "3 seconds, it tries the first three items on the page with the "
        "keyboard and checks that one of them pauses, stops or mutes it."
    )

    def walk_extras(self) -> list:
        return []

    async def collect(self, ctx: RunContext, walk: KeyboardWalk | None) -> State2A:
        return await collect(ctx, walk)

    def evaluate(self, state: State2A, evidence_refs: list[str]) -> Finding:
        return evaluate(state, evidence_refs)

    def questions(self, state: State2A, evidence_refs: list[str]) -> list[OpenQuestion]:
        return questions_for(state, evidence_refs)

    async def resume(self, ctx: RunContext, state: State2A, report) -> list[str]:
        apply_answers(state, report)
        regions = {a.id: region_of(a, state.mp) for a in state.audio if a.measured}
        await mechanism.press_answered(ctx, state.mp, state.j2, state.probes, regions)
        return []


__all__ = ["Check2A", "State2A", "find_audio"]
