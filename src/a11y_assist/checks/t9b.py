"""Test 9.B (3.2.3-consistent-navigation), from docs/rules/9b-consistent-navigation.md.

Reads the site read (`site.py`) and compares the order of the components the
tested page shares with each other page: source order and visual order. No
key is pressed (HtT 1: "Do not initiate changes"). Only evaluate() and the
row tables decide outcomes.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from a11y_assist.checks.base import RunContext
from a11y_assist.engine import Row, first_match
from a11y_assist.models import (
    REVIEW_HEAD,
    DecidedBy,
    Finding,
    Instance,
    OpenQuestion,
    Outcome,
    TestId,
)
from a11y_assist.site import (
    PageRead,
    Unit,
    before,
    norm_href,
    page_label,
    pair_in_order,
    site_read,
)
from a11y_assist.walk import KeyboardWalk

SHOWN_MAX = 5  # pairs out of order named per page


class Item(BaseModel):
    key: str
    name: str
    pos: int
    css: str
    box: list[int] = Field(default_factory=list)


class Cmp(BaseModel):
    """The tested page compared with one other page (an instance)."""

    n: int
    url: str
    incomplete: bool = False
    matched: int = 0
    source: list[list[str]] = Field(default_factory=list)  # [a, b]: a before b here
    visual: list[list[str]] = Field(default_factory=list)
    only_here: list[str] = Field(default_factory=list)  # region keys
    only_there: list[str] = Field(default_factory=list)


class State9B(BaseModel):
    no_pages: bool = False
    read_errors: list[str] = Field(default_factory=list)
    cmps: list[Cmp] = Field(default_factory=list)


def _has_main(p: PageRead) -> bool:
    return any(r.role == "main" for r in p.regions)


def items(p: PageRead) -> list[Item]:
    """Navigation components (spec Terms): controls outside main, and
    regions other than main, keyed for matching."""
    out: list[Item] = []
    leave_main = _has_main(p)
    for u in p.units:
        if u.kind != "control" or (leave_main and u.in_main) or not u.name:
            continue
        out.append(
            Item(
                key=_key(u, p.url),
                name=u.name[:80],
                pos=u.i,
                css=u.css,
                box=u.box,
            )
        )
    for k, r in enumerate(p.regions):
        if r.role == "main":
            continue
        out.append(
            Item(
                key="region:" + r.key, name=r.key, pos=100_000 + k, css=r.css, box=r.box
            )
        )
    return out


def _key(u: Unit, page_url: str) -> str:
    dest = norm_href(u.href, page_url) if u.role == "link" else ""
    return f"{u.region_role}|{u.role}|{u.name.lower()}|{dest}"


def compare(main: PageRead, other: PageRead) -> Cmp:
    a, b = items(main), items(other)
    c = Cmp(n=other.n, url=other.url, incomplete=other.truncated or main.truncated)
    pairs = pair_in_order(
        [(x.key, k) for k, x in enumerate(a)], [(y.key, k) for k, y in enumerate(b)]
    )
    c.matched = len(pairs)
    for i, (ka, kb) in enumerate(pairs):
        for la, lb in pairs[i + 1 :]:
            x, y = a[ka], a[la]
            # Source order: within controls, and within regions (not across).
            same_kind = (x.pos >= 100_000) == (y.pos >= 100_000)
            if same_kind and (x.pos < y.pos) != (b[kb].pos < b[lb].pos):
                c.source.append([x.name, y.name])
            if x.pos < 100_000 and y.pos < 100_000:
                if before(x.box, y.box) and before(b[lb].box, b[kb].box):
                    c.visual.append([x.name, y.name])
                elif before(y.box, x.box) and before(b[kb].box, b[lb].box):
                    c.visual.append([y.name, x.name])
    here = {r.key for r in main.regions if r.role != "main"}
    there = {r.key for r in other.regions if r.role != "main"}
    c.only_here, c.only_there = sorted(here - there), sorted(there - here)
    return c


async def collect(ctx: RunContext, walk: KeyboardWalk | None) -> State9B:
    if not ctx.pages:
        return State9B(no_pages=True)
    site = await site_read(ctx)
    st = State9B(read_errors=site.errors)
    if st.read_errors:
        return st
    st.cmps = [compare(site.main, p) for p in site.others]
    return st


INSTANCE_ROWS = [
    Row("N1", lambda c: c.incomplete, Outcome.NEEDS_REVIEW, "Spec rule"),
    Row("N3", lambda c: bool(c.source), Outcome.FAIL, "p. 43 ER 1; F66"),
    Row("N4", lambda c: bool(c.visual), Outcome.FAIL, "F66; Understanding 3.2.3"),
    Row("N5", lambda c: c.matched == 1, Outcome.NEEDS_REVIEW, "Spec rule"),
    Row("N6", lambda c: True, Outcome.PASS, "p. 43 ER 1, Note"),
]


def _finding(outcome, summary, rows, refs, inst=None, rationale="", note=False):
    f = Finding(
        test_id=TestId.T9B,
        test_name=TestId.T9B.tt_name,
        outcome=outcome,
        summary=summary,
        rationale=rationale or f"Spec {rows[-1]}.",
        decided_by=DecidedBy.RULE,
        rows=rows,
        instances=inst or [],
        evidence_refs=refs,
    )
    if note:
        f.note = "This test could not be performed"
    return f


def _short(name: str) -> str:
    return name.split("|", 1)[-1] if "|" in name else name


def evaluate(st: State9B, evidence_refs: list[str]) -> Finding:
    if st.no_pages:
        f = Finding.not_performed(
            TestId.T9B,
            "it needs other pages of the same site to compare. Run it again with other_pages.",
        )
        f.rows, f.decided_by, f.evidence_refs = (
            ["A1", "G1"],
            DecidedBy.RULE,
            evidence_refs,
        )
        return f
    if st.read_errors:
        f = Finding.not_performed(TestId.T9B, " ".join(st.read_errors))
        f.rows = ["A2", "G1"]
        return f
    compared = [c for c in st.cmps if c.matched > 0]  # N2: not compared
    if not compared:
        return _finding(
            Outcome.DNA,
            "No navigation on this page appears on the other pages you gave, so this test does not apply.",
            ["A3", "G1"],
            evidence_refs,
        )
    trace = ["A4"]
    results = []
    sentences = []
    inst = []
    for c in compared:
        row = first_match(INSTANCE_ROWS, c)
        assert row is not None
        results.append(row.outcome)
        trace.append(f"p{c.n}:{row.id}")
        page = f"other page {c.n}"
        if row.id in ("N3", "N4"):
            pairs = (c.source if row.id == "N3" else c.visual)[:SHOWN_MAX]
            how = "" if row.id == "N3" else " on screen"
            for a, b in pairs:
                sentences.append(
                    f'"{_short(a)}" comes before "{_short(b)}"{how} here but after it on {page}.'
                )
        elif row.id == "N5":
            sentences.append(
                f"Only one link or control is shared with {page}, so there is no order to compare. A person should check the navigation."
            )
        elif row.id == "N1":
            sentences.append(f"Not all of {page} could be read.")
        inst.append(
            Instance(
                description=f"p{c.n} [{row.id} {row.outcome.value}] {c.url}: {c.matched} shared",
            )
        )
    if any(o is Outcome.FAIL for o in results):
        gid, outcome = "G2", Outcome.FAIL
        head = "Some navigation appears in a different order on another page:"
        tail = ["Keep repeated navigation in the same order on every page."]
    elif any(o is Outcome.NEEDS_REVIEW for o in results):
        gid, outcome, head, tail = "G3", Outcome.NEEDS_REVIEW, REVIEW_HEAD, []
    else:
        gid, outcome = "G4", Outcome.PASS
        head = "The navigation this page shares with the other pages you gave appears in the same order on each of them."
        tail = []
    trace.append(gid)
    return _finding(
        outcome,
        " ".join([head, *sentences, *tail]),
        trace,
        evidence_refs,
        inst,
        f"Spec {gid}. " + "; ".join(trace[1:-1]),
        note=outcome is Outcome.NEEDS_REVIEW,
    )


class Check9B:
    """9.B as a registered check (checks/base.py)."""

    test_id = TestId.T9B
    state_type = State9B
    uses_walk = False
    uses_pages = True
    shares = 2
    about = (
        "It compares this page with the other pages of the same site you give. "
        "Links, buttons and areas such as the menu, header and footer that "
        "appear on both are checked for the same order, in the page's code and "
        "on screen. Items added or missing on one page are allowed."
    )

    def walk_extras(self) -> list:
        return []

    async def collect(self, ctx: RunContext, walk: KeyboardWalk | None) -> State9B:
        return await collect(ctx, walk)

    def evaluate(self, state: State9B, evidence_refs: list[str]) -> Finding:
        return evaluate(state, evidence_refs)

    def questions(self, state: State9B, evidence_refs: list[str]) -> list[OpenQuestion]:
        return []

    async def resume(self, ctx: RunContext, state: Any, report) -> list[str]:
        return []


__all__ = ["Check9B", "compare", "items", "page_label"]
