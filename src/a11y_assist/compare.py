"""Compare two report files test by test: a reference (a person's answer key)
and a candidate (usually the tool's pre-SCRT file).

Nothing here changes or decides an outcome: it sorts agreement and
disagreement into the categories tests/scoring.py reports, with a false
PASS (the worst error, principle 3) counted on its own.

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
from a11y_assist.scrt import PreScrt, Row, ScrtResult

_ORDER = (ScrtResult.FAIL, ScrtResult.PASS, ScrtResult.DNA, ScrtResult.NOT_TESTED)


class Verdict(str, Enum):
    AGREE = "agree"
    FALSE_PASS = "false_pass"  # candidate Pass, reference Fail
    MISSED_FAIL = "missed_fail"  # candidate Does Not Apply, reference Fail
    FALSE_FAIL = "false_fail"  # candidate Fail, reference Pass
    FAIL_NOT_APPLICABLE = "fail_vs_dna"  # candidate Fail, reference Does Not Apply
    OTHER = "other_mismatch"  # e.g. Pass vs Does Not Apply, Not Tested
    NEEDS_REVIEW = "needs_review"  # candidate blank: the tool left it to a person
    NOT_PERFORMED = "not_performed"  # the tool did not perform the test
    NOT_SCORED = "not_scored"  # reference blank: no answer to score against


# The order a report lists disagreements in: worst first.
SEVERITY = [
    Verdict.FALSE_PASS,
    Verdict.MISSED_FAIL,
    Verdict.FALSE_FAIL,
    Verdict.FAIL_NOT_APPLICABLE,
    Verdict.OTHER,
]


def summary(rows: list[Row]) -> ScrtResult | None:
    got = {r.TestResult for r in rows}
    return next((r for r in _ORDER if r in got), None)


class TestComparison(BaseModel):
    __test__ = False  # not a pytest test class

    test_id: str
    test_name: str
    verdict: Verdict
    reference: ScrtResult | None
    candidate: ScrtResult | None
    candidate_outcome: str | None = Field(
        default=None, description="The tool's own outcome when it wrote the row."
    )
    spec_version: str | None = None
    rows: list[str] = Field(default_factory=list, description="Spec rows (audit).")
    reference_comment: str | None = None
    candidate_comment: str | None = None


class Comparison(BaseModel):
    reference_page: str | None
    candidate_page: str | None
    same_page: bool
    tests: list[TestComparison]
    counts: dict[str, int]

    def disagreements(self) -> list[TestComparison]:
        rank = {v: i for i, v in enumerate(SEVERITY)}
        bad = [t for t in self.tests if t.verdict in rank]
        return sorted(bad, key=lambda t: (rank[t.verdict], t.test_id))


def verdict(
    ref: ScrtResult | None, cand: ScrtResult | None, performed: bool
) -> Verdict:
    if ref is None:
        return Verdict.NOT_SCORED
    if not performed:
        return Verdict.NOT_PERFORMED
    if cand is None:
        return Verdict.NEEDS_REVIEW
    if cand == ref:
        return Verdict.AGREE
    if ref is ScrtResult.FAIL:
        if cand is ScrtResult.PASS:
            return Verdict.FALSE_PASS
        if cand is ScrtResult.DNA:
            return Verdict.MISSED_FAIL
    if cand is ScrtResult.FAIL:
        if ref is ScrtResult.PASS:
            return Verdict.FALSE_FAIL
        if ref is ScrtResult.DNA:
            return Verdict.FAIL_NOT_APPLICABLE
    return Verdict.OTHER


def page_key(url: str | None) -> str | None:
    """Scheme-less host and path, no trailing slash, no query or fragment."""
    if not url or not url.strip():
        return None
    url = url.strip()
    # Testers type "www.dhs.gov/page" in SCRT; without "//" it parses as a path.
    u = urlsplit(url if "://" in url else "//" + url)
    return (u.netloc.lower().removeprefix("www.") + u.path.rstrip("/")) or None


def compare(reference: PreScrt, candidate: PreScrt) -> Comparison:
    ref_rows, cand_rows = reference.results(), candidate.results()
    tests: list[TestComparison] = []
    for tid in catalog.active_ids():
        rr, cr = ref_rows.get(tid, []), cand_rows.get(tid, [])
        src = cr[0].source if cr else None
        performed = bool(cr) and all(r.source.performed for r in cr)
        ref, cand = summary(rr), summary(cr)
        tests.append(
            TestComparison(
                test_id=tid,
                test_name=catalog.tests()[tid]["name"],
                verdict=verdict(ref, cand, performed),
                reference=ref,
                candidate=cand,
                candidate_outcome=src.outcome if src else None,
                spec_version=src.spec_version if src else None,
                rows=src.rows if src else [],
                reference_comment=rr[0].TesterComment if rr else None,
                candidate_comment=cr[0].TesterComment if cr else None,
            )
        )
    counts = {v.value: 0 for v in Verdict}
    for t in tests:
        counts[t.verdict.value] += 1
    rp, cp = reference.Product.P_Location, candidate.Product.P_Location
    return Comparison(
        reference_page=rp,
        candidate_page=cp,
        same_page=page_key(rp) == page_key(cp),
        tests=tests,
        counts=counts,
    )


def totals(comparisons: list[Comparison]) -> dict[str, int]:
    out = {v.value: 0 for v in Verdict}
    for c in comparisons:
        for k, n in c.counts.items():
            out[k] += n
    return out


def rates(counts: dict[str, int]) -> dict[str, str]:
    """Plain figures: scored tests are those with a reference answer that the
    tool performed."""
    scored = sum(
        counts[v.value]
        for v in Verdict
        if v not in (Verdict.NOT_SCORED, Verdict.NOT_PERFORMED)
    )
    decided = scored - counts[Verdict.NEEDS_REVIEW.value]
    agree = counts[Verdict.AGREE.value]
    return {
        "scored": str(scored),
        "agreement (of decided)": f"{agree}/{decided}",
        "needs review (of scored)": f"{counts[Verdict.NEEDS_REVIEW.value]}/{scored}",
        "false PASS": str(counts[Verdict.FALSE_PASS.value]),
        "missed fail (Does Not Apply)": str(counts[Verdict.MISSED_FAIL.value]),
        "false FAIL": str(counts[Verdict.FALSE_FAIL.value]),
        "Fail vs Does Not Apply": str(counts[Verdict.FAIL_NOT_APPLICABLE.value]),
        "other mismatch": str(counts[Verdict.OTHER.value]),
        "not performed by the tool": str(counts[Verdict.NOT_PERFORMED.value]),
        "no reference answer": str(counts[Verdict.NOT_SCORED.value]),
    }
