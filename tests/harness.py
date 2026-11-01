"""Run one TT check on a page end to end, answering its open questions with
scripted answers that stand in for the calling agent. Answers are test data
(what a correct judge would say), never outcomes, and live in test files,
never in a page."""

from __future__ import annotations

from typing import Any

from a11y_assist.models import Answer, ChoiceAnswer, TestId
from a11y_assist.pipeline import answer_questions, run_tt_tests

from .harness_4c import assert_plain


async def run_check(
    settings,
    url: str,
    test: TestId,
    choice: str | dict[str, dict[str, Any]] | None = None,
    reasons: str = "scripted test answer",
) -> dict[str, Any]:
    """`choice` answers every "choice" question the run asks: one choice for
    all, or a dict from the question ID's last part ("J1", "J2") to
    ChoiceAnswer fields (choice, element, key, duration_ms, presses)."""
    out = await run_tt_tests(settings, url, [test])
    assert out.errors == [], out.errors
    report = out.report
    for _ in range(3):
        open_qs = [q for q in report.open_questions if q.test_id is test]
        if not open_qs:
            break
        assert choice is not None, f"{url}: a question was asked: {open_qs[0].question}"

        def fields(q) -> dict[str, Any]:
            if isinstance(choice, dict):
                f = choice.get(q.question_id.rsplit("-", 1)[-1])
                assert f is not None, f"{url}: no scripted answer for {q.question_id}"
                return {"reasons": reasons, **f}
            return {"choice": choice, "reasons": reasons}

        answers = [
            Answer(
                question_id=q.question_id,
                choice=ChoiceAnswer(**fields(q)),
                rationale="scripted test answer",
            )
            for q in open_qs
        ]
        res = await answer_questions(settings, out.run_id, answers)
        assert res.errors == [] and res.rejected == [], (res.errors, res.rejected)
        report = res.report
    [finding] = [f for f in report.findings if f.test_id is test]
    assert_plain(finding.summary)
    return {"finding": finding, "report": report, "run_id": out.run_id}


def instance_rows(finding) -> list[str]:
    return sorted(r.split(":")[1] for r in finding.rows if ":" in r)
