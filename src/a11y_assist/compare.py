"""Compare two report files test by test: what each file says, and whether
it changed. Neutral on purpose (Abby, 2026-11-02): either file may be the
earlier one (before and after a fix), and neither is taken as the truth.
Scoring one file against an answer key is evaluation methodology and lives
on top of this, in evals/scoring.py.

Nothing here changes or decides an outcome.

A test with several rows (a parent and child issues) is summarized once:
Fail if any row fails, else Pass if any row passes, else Does Not Apply,
else Not Tested; blank when every row is blank. That is how a file's rows
are read, not a TT rule.
"""

from __future__ import annotations

from enum import Enum
from urllib.parse import urlsplit

from pydantic import BaseModel, Field

from a11y_assist import catalog
from a11y_assist.scrt import PreScrt, Row, ScrtResult, Source

_ORDER = (ScrtResult.FAIL, ScrtResult.PASS, ScrtResult.DNA, ScrtResult.NOT_TESTED)


class Change(str, Enum):
    SAME = "same"  # both files give the same result
    CHANGED = "changed"  # both give a result, and they differ
    ONLY_FIRST = "only_first"  # the second file leaves it blank
    ONLY_SECOND = "only_second"  # the first file leaves it blank
    NEITHER = "neither"  # both leave it blank


def summary(rows: list[Row]) -> ScrtResult | None:
    got = {r.TestResult for r in rows}
    return next((r for r in _ORDER if r in got), None)


def change(first: ScrtResult | None, second: ScrtResult | None) -> Change:
    if first is None and second is None:
        return Change.NEITHER
    if first is None:
        return Change.ONLY_SECOND
    if second is None:
        return Change.ONLY_FIRST
    return Change.SAME if first == second else Change.CHANGED


class Side(BaseModel):
    """One file's answer for one test."""

    result: ScrtResult | None
    rows: int = Field(description="Rows for this test (a parent plus child issues).")
    performed: bool = Field(
        description="False when the file's maker (the tool) did not perform it."
    )
    needs_review: bool = Field(
        description="A blank the tool left for a person (pre-SCRT files)."
    )
    comment: str | None = None
    source: Source | None = None


class TestComparison(BaseModel):
    __test__ = False  # not a pytest test class

    test_id: str
    test_name: str
    change: Change
    first: Side
    second: Side


class Comparison(BaseModel):
    first_page: str | None
    second_page: str | None
    same_page: bool
    tests: list[TestComparison]
    counts: dict[str, int]

    def changes(self) -> list[TestComparison]:
        """Tests whose result differs between the files, in catalog order."""
        return [t for t in self.tests if t.change not in (Change.SAME, Change.NEITHER)]


def page_key(url: str | None) -> str | None:
    """Scheme-less host and path, no trailing slash, no fragment. The query
    is kept: "/?search=artemis" is another page than "/" (post-round 1 fix
    13: round 1's search page scored as the home page's key)."""
    if not url or not url.strip():
        return None
    url = url.strip()
    # Testers type "www.dhs.gov/page" in SCRT; without "//" it parses as a path.
    u = urlsplit(url if "://" in url else "//" + url)
    key = u.netloc.lower().removeprefix("www.") + u.path.rstrip("/")
    return (key + (f"?{u.query}" if u.query else "")) or None


def _side(rows: list[Row]) -> Side:
    return Side(
        result=summary(rows),
        rows=len(rows),
        performed=bool(rows) and all(r.source.performed for r in rows),
        needs_review=any(r.needs_review for r in rows),
        comment=rows[0].TesterComment if rows else None,
        source=rows[0].source if rows else None,
    )


def compare(first: PreScrt, second: PreScrt) -> Comparison:
    a_rows, b_rows = first.results(), second.results()
    tests: list[TestComparison] = []
    for tid in catalog.active_ids():
        a, b = _side(a_rows.get(tid, [])), _side(b_rows.get(tid, []))
        tests.append(
            TestComparison(
                test_id=tid,
                test_name=catalog.tests()[tid]["name"],
                change=change(a.result, b.result),
                first=a,
                second=b,
            )
        )
    counts = {c.value: 0 for c in Change}
    for t in tests:
        counts[t.change.value] += 1
    ap, bp = first.Product.P_Location, second.Product.P_Location
    return Comparison(
        first_page=ap,
        second_page=bp,
        same_page=page_key(ap) is not None and page_key(ap) == page_key(bp),
        tests=tests,
        counts=counts,
    )
