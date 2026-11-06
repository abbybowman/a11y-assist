"""Run one TT check on a page end to end, answering its open questions with
scripted answers that stand in for the calling agent. Answers are test data
(what a correct judge would say), never outcomes, and live in test files,
never in a page."""

from __future__ import annotations

from typing import Any

from tobi508.models import (
    TEST_NOT_PERFORMED_NOTE,
    Answer,
    ChoiceAnswer,
    Outcome,
    TestId,
)
from tobi508.pipeline import answer_questions, run_tt_tests

from .harness_4c import assert_plain


def assert_note(f) -> None:
    # Principle 2 and _template.md G3: every NEEDS REVIEW says the test could
    # not be performed, and nothing else does. Every fixture checks it.
    assert (f.note == TEST_NOT_PERFORMED_NOTE) == (f.outcome is Outcome.NEEDS_REVIEW), (
        f.test_id.value,
        f.outcome.value,
        f.note,
        f.rows,
    )


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
    assert_note(finding)
    return {"finding": finding, "report": report, "run_id": out.run_id}


def instance_rows(finding) -> list[str]:
    return sorted(r.split(":")[1] for r in finding.rows if ":" in r)


async def run_tests(
    settings,
    url: str,
    tests,
    answers: dict[str, dict[str, dict[str, Any]]],
    other_pages: list[str] | None = None,
) -> dict[str, Any]:
    """Several tests in one call (tests that share a collection pass, such as
    5.A and 5.C). `answers` maps a test ID to its scripted answers, keyed by
    the question ID's last part. Returns each test's finding."""
    out = await run_tt_tests(
        settings, url, [TestId(t) for t in tests], other_pages=other_pages
    )
    assert out.errors == [], out.errors
    report = out.report
    for _ in range(3):
        qs = [q for q in report.open_questions if q.test_id.value in tests]
        if not qs:
            break
        sent = []
        for q in qs:
            f = (answers.get(q.test_id.value) or {}).get(
                q.question_id.rsplit("-", 1)[-1]
            )
            assert f is not None, f"{url}: no scripted answer for {q.question_id}"
            sent.append(
                Answer(
                    question_id=q.question_id,
                    choice=ChoiceAnswer(**{"reasons": "scripted test answer", **f}),
                    rationale="scripted test answer",
                )
            )
        res = await answer_questions(settings, out.run_id, sent)
        assert res.errors == [] and res.rejected == [], (res.errors, res.rejected)
        report = res.report
    got = {f.test_id.value: f for f in report.findings if f.test_id.value in tests}
    for f in got.values():
        assert_plain(f.summary)
        assert_note(f)
    return got
