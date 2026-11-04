"""Score the tool's file against a person's answer key, test by test.

Evaluation methodology, layered on the neutral comparison in
src/a11y_assist/compare.py: compare(key, tool_file) gives what each file says;
this decides which disagreements are errors and how bad. A false PASS (the
worst error, principle 3) is counted on its own. Shared by the judging rounds
(evals/judging.py) and, later, the agent eval, so both score one way.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from a11y_assist.compare import Comparison, TestComparison
from a11y_assist.scrt import ScrtResult


class Verdict(str, Enum):
    AGREE = "agree"
    FALSE_PASS = "false_pass"  # tool Pass, key Fail
    MISSED_FAIL = "missed_fail"  # tool Does Not Apply, key Fail
    FALSE_FAIL = "false_fail"  # tool Fail, key Pass
    FAIL_NOT_APPLICABLE = "fail_vs_dna"  # tool Fail, key Does Not Apply
    OTHER = "other_mismatch"  # e.g. Pass vs Does Not Apply, Not Tested
    NEEDS_REVIEW = "needs_review"  # tool blank: left to a person
    NOT_PERFORMED = "not_performed"  # the tool did not perform the test
    NOT_SCORED = "not_scored"  # key blank: no answer to score against
    NO_ANSWER = "no_answer"  # an agent's RESULT line lacks it, or is malformed


# The order a report lists disagreements in: worst first.
SEVERITY = [
    Verdict.FALSE_PASS,
    Verdict.MISSED_FAIL,
    Verdict.FALSE_FAIL,
    Verdict.FAIL_NOT_APPLICABLE,
    Verdict.NO_ANSWER,
    Verdict.OTHER,
]

# The agent eval's weights (docs/plans/2026-10-31-agent-eval.md section 8),
# fixed before any run. A Does Not Apply where the key fails reports no
# problem, as a false PASS does; an answer missing from the RESULT line
# scores as wrong.
WEIGHTS = {
    Verdict.AGREE: 1,
    Verdict.NEEDS_REVIEW: 0,
    Verdict.FALSE_FAIL: -1,
    Verdict.FAIL_NOT_APPLICABLE: -1,
    Verdict.OTHER: -1,
    Verdict.NO_ANSWER: -1,
    Verdict.MISSED_FAIL: -3,
    Verdict.FALSE_PASS: -3,
}


def weighted(counts: dict[str, int]) -> int:
    return sum(WEIGHTS[v] * counts.get(v.value, 0) for v in WEIGHTS)


def rollup(results: list[ScrtResult | None]) -> ScrtResult | None:
    """TT outcomes under one WCAG criterion, as one result: Fail if any
    fails; otherwise blank (needs review) if any is blank, not performed or
    Not Tested; otherwise Pass if any passes; otherwise Does Not Apply.
    Eval code: it decides no outcome of the tool."""
    if ScrtResult.FAIL in results:
        return ScrtResult.FAIL
    if not results or any(r in (None, ScrtResult.NOT_TESTED) for r in results):
        return None
    if ScrtResult.PASS in results:
        return ScrtResult.PASS
    return ScrtResult.DNA


def verdict(
    key: ScrtResult | None, tool: ScrtResult | None, performed: bool
) -> Verdict:
    if key is None:
        return Verdict.NOT_SCORED
    if not performed:
        return Verdict.NOT_PERFORMED
    if tool is None:
        return Verdict.NEEDS_REVIEW
    if tool == key:
        return Verdict.AGREE
    if key is ScrtResult.FAIL:
        if tool is ScrtResult.PASS:
            return Verdict.FALSE_PASS
        if tool is ScrtResult.DNA:
            return Verdict.MISSED_FAIL
    if tool is ScrtResult.FAIL:
        if key is ScrtResult.PASS:
            return Verdict.FALSE_FAIL
        if key is ScrtResult.DNA:
            return Verdict.FAIL_NOT_APPLICABLE
    return Verdict.OTHER


class ScoredTest(BaseModel):
    test: TestComparison
    verdict: Verdict


class Score(BaseModel):
    """One page: the key is the comparison's first file, the tool's the second."""

    comparison: Comparison
    tests: list[ScoredTest]
    counts: dict[str, int]

    def disagreements(self) -> list[ScoredTest]:
        rank = {v: i for i, v in enumerate(SEVERITY)}
        bad = [t for t in self.tests if t.verdict in rank]
        return sorted(bad, key=lambda t: (rank[t.verdict], t.test.test_id))


def score(c: Comparison) -> Score:
    tests = [
        ScoredTest(
            test=t, verdict=verdict(t.first.result, t.second.result, t.second.performed)
        )
        for t in c.tests
    ]
    counts = {v.value: 0 for v in Verdict}
    for t in tests:
        counts[t.verdict.value] += 1
    return Score(comparison=c, tests=tests, counts=counts)


def totals(scores: list[Score]) -> dict[str, int]:
    out = {v.value: 0 for v in Verdict}
    for s in scores:
        for k, n in s.counts.items():
            out[k] += n
    return out


def rates(counts: dict[str, int]) -> dict[str, str]:
    """Plain figures: scored tests are those with a key answer that the tool
    performed."""
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
        "no answer given": str(counts[Verdict.NO_ANSWER.value]),
        "not performed by the tool": str(counts[Verdict.NOT_PERFORMED.value]),
        "no reference answer": str(counts[Verdict.NOT_SCORED.value]),
    }
