"""Data model invariants."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tobi508.models import Finding, Outcome, Report, TestId, Versions


def _versions() -> Versions:
    return Versions(
        tobi508="0",
        andi="29.2.2",
        jquery="3.7.1",
        playwright="1.63.0",
        browser_channel="chrome",
        browser=None,
        os="test",
        python="3",
        rules_spec={"4.C": "1.0.0"},
        judging_model="none",
    )


def test_test_ids_are_the_active_tt_conditions_with_names() -> None:
    ids = [t.value for t in TestId]
    assert len(ids) == 61 and ids[:2] == ["1.A", "1.B"] and ids[-1] == "20.A"
    assert "5.E" not in ids and "6.B" not in ids  # obsolete and removed
    assert TestId.T4C.tt_name == "2.1.2-no-keyboard-trap"
    assert TestId.T4D.wcag_sc == "2.4.7 Focus Visible"


def test_finding_defaults_to_needs_review() -> None:
    f = Finding(test_id=TestId.T4A, test_name=TestId.T4A.tt_name)
    assert f.outcome is Outcome.NEEDS_REVIEW
    assert f.decided_by is None


def test_report_cannot_claim_certification() -> None:
    kwargs = dict(
        run_id="r",
        target="https://nasa.gov",
        started_at=datetime.now(timezone.utc),
        versions=_versions(),
        evidence_dir="x",
    )
    report = Report(**kwargs)
    assert report.certified is False
    assert "NOT a certified" in report.disclaimer
    with pytest.raises(ValidationError):
        Report(**kwargs, certified=True)


def test_a_finding_is_one_line_in_tool_output():
    """Post-round 1 fix 6b, then agent follow-through change 2b: a page
    with 96 failing fields gave a 21k character summary. Tool output keeps
    the first sentence, says tobi_explain has more, and leaves out rows and
    links; the finding itself keeps everything."""
    from tobi508.models import (
        SUMMARY_VIEW_MAX,
        Finding,
        FindingView,
        Outcome,
        TestId,
    )

    sentence = "When we filled in a box, the page went to another address. "
    f = Finding(
        test_id=TestId.T5D,
        test_name=TestId.T5D.tt_name,
        outcome=Outcome.FAIL,
        summary="Some fields change the page. " + sentence * 96,
        rows=["A3"] + [f"f{n}:M9" for n in range(96)] + ["G2"],
    )
    v = FindingView.of(f.model_copy(update={"outcome": Outcome.NEEDS_REVIEW}))
    assert v.summary == "Some fields change the page. (More: tobi_explain.)"
    fail = FindingView.of(f)  # a FAIL keeps its summary, up to a cap
    assert fail.summary.startswith("Some fields change the page. When we filled")
    assert len(fail.summary) < 1600 and fail.summary.endswith("(More: tobi_explain.)")
    assert fail.confirmed is True and "rows" not in v.model_dump()
    review = f.model_copy(update={"outcome": Outcome.NEEDS_REVIEW})
    long = FindingView.of(review.model_copy(update={"summary": "word " * 200}))
    assert len(long.summary) < SUMMARY_VIEW_MAX + 40 and "..." in long.summary
    short = FindingView.of(review.model_copy(update={"summary": "All good."}))
    assert short.summary == "All good."
    assert len(f.summary) > 5000 and len(f.rows) == 98  # the report keeps them


def test_a_fail_names_confirmed_and_unconfirmed_instances_apart():
    """Fourth development run debrief: the agent asked which failures were
    confirmed and which still waited for answers. Tool output says both."""
    from tobi508.models import Finding, FindingView, OpenQuestion

    report = Report(
        run_id="r",
        target="https://nasa.gov",
        started_at=datetime.now(timezone.utc),
        versions=_versions(),
        evidence_dir="x",
        open_questions=[
            OpenQuestion(
                question_id=f"q{n}",
                test_id=TestId.T4D,
                kind="choice",
                instance=f"stop {n}",
                question="?",
                rubric="?",
                input={},
            )
            for n in range(2)
        ],
    )
    fail = Finding(test_id=TestId.T4D, test_name="x", outcome=Outcome.FAIL)
    v = FindingView.of(fail, report)
    assert v.confirmed and v.unconfirmed == 2
    other = FindingView.of(Finding(test_id=TestId.T4A, test_name="x"), report)
    assert other.confirmed is None and other.unconfirmed == 0


def test_results_say_incomplete_while_work_is_left():
    """Agent follow-through plan, change 2: whether work is left is in the
    data (work, remaining, waiting_on), not only in next_step's prose."""
    from tobi508.models import Finding, FindingView, OpenQuestion, Remaining

    report = Report(
        run_id="r",
        target="https://nasa.gov",
        started_at=datetime.now(timezone.utc),
        versions=_versions(),
        evidence_dir="x",
    )
    assert Remaining.of(report).work == "complete"
    report.follow_up_calls = [{"url": "https://nasa.gov", "tests": ["19.A"]}]
    report.open_questions = [
        OpenQuestion(
            question_id="q",
            test_id=TestId.T4D,
            kind="choice",
            instance="x",
            question="?",
            rubric="?",
            input={},
        )
    ]
    r = Remaining.of(report)
    assert r.work == "incomplete" and r.tests_waiting == ["4.D", "19.A"]
    v = FindingView.of(Finding(test_id=TestId.T19A, test_name="x"), report)
    assert v.waiting_on == ["1 follow-up call(s) in follow_up_calls"]
    v = FindingView.of(Finding(test_id=TestId.T5A, test_name="x"), report)
    assert v.waiting_on == []


def test_an_answer_to_a_picture_question_must_say_what_it_shows():
    """Agent follow-through plan, change 3: development run 5's agent answered
    visual questions without opening a picture. An answer needs `seen`, or
    `picture_error` with unsure (kept, marked not viewed, for a person)."""
    from tobi508.judgment import record_answers
    from tobi508.models import Answer, ChoiceAnswer, OpenQuestion

    def q(qid, image):
        return OpenQuestion(
            question_id=qid,
            test_id=TestId.T4D,
            kind="choice",
            choices=["visible", "not_visible", "unsure"],
            instance="x",
            question="?",
            rubric="?",
            input={"image_a": "run://r/a.png"} if image else {},
        )

    report = Report(
        run_id="r",
        target="https://nasa.gov",
        started_at=datetime.now(timezone.utc),
        versions=_versions(),
        evidence_dir="x",
        open_questions=[q("a", True), q("b", True), q("c", True), q("d", False)],
    )

    def a(qid, choice, seen=""):
        return Answer(
            question_id=qid,
            choice=ChoiceAnswer(choice=choice),
            rationale="r",
            seen=seen,
        )

    def err(qid, choice, error):
        x = a(qid, choice)
        return x.model_copy(update={"picture_error": error})

    report.open_questions.append(q("e", True))
    report.open_questions.append(q("f", True))
    ok, errors = record_answers(
        report,
        [
            a("a", "visible"),
            a("b", "visible", seen="a blue outline round Search"),
            a("c", "unsure"),
            a("d", "visible"),
            err("e", "unsure", "the picture is blank"),
            err("f", "visible", "the picture is blank"),
        ],
    )
    assert ok == ["b", "d", "e"]
    assert [e.split(":")[0] for e in errors] == ["a", "c", "f"]
    assert errors[0].startswith("a: this question names a picture")
    assert "can only be unsure" in errors[2]
    assert [q.question_id for q in report.open_questions] == ["a", "c", "f"]
    by = {r.answer.question_id: r.answer for r in report.answers}
    assert by["e"].not_viewed and not by["b"].not_viewed and not by["d"].not_viewed


def test_open_questions_come_ten_at_a_time():
    """Agent follow-through plan, change 2b (2): a result shows at most 10
    open questions; its to-do list and next_step say the rest follow."""
    from tobi508.models import OpenQuestion
    from tobi508.pipeline import QUESTION_PAGE, next_step, todo

    report = Report(
        run_id="r",
        target="https://nasa.gov",
        started_at=datetime.now(timezone.utc),
        versions=_versions(),
        evidence_dir="x",
        open_questions=[
            OpenQuestion(
                question_id=f"q{n}",
                test_id=TestId.T4D,
                kind="choice",
                instance="x",
                question="?",
                rubric="?",
                input={"image_a": "run://r/a.png"} if n < 3 else {},
            )
            for n in range(12)
        ],
    )
    assert QUESTION_PAGE == 10
    [first, *_] = todo(report)
    assert first.startswith("[ ] Answer the 10 open question(s)")
    assert "3 name a picture" in first and "2 more come with the answer result" in first
    assert "10 are in open_questions now" in next_step(report)


def test_picture_error_is_refused_for_a_picture_that_was_attached():
    """Abby, 2026-11-07: development run 10 gave picture_error ("not
    inspected") for pictures it had been sent. For a picture attached to a
    result the answer needs `seen`; picture_error stays for one that could
    not be opened."""
    from tobi508.judgment import record_answers
    from tobi508.models import Answer, ChoiceAnswer, OpenQuestion

    def q(qid, link):
        return OpenQuestion(
            question_id=qid,
            test_id=TestId.T4F,
            kind="choice",
            choices=["preserves", "unsure"],
            instance="x",
            question="?",
            rubric="?",
            input={"image_a_order": link},
        )

    report = Report(
        run_id="r",
        target="https://nasa.gov",
        started_at=datetime.now(timezone.utc),
        versions=_versions(),
        evidence_dir="x",
        open_questions=[q("sent", "run://r/a.png"), q("not_sent", "run://r/b.png")],
    )
    err = [
        Answer(
            question_id=i,
            choice=ChoiceAnswer(choice="unsure"),
            rationale="r",
            picture_error="not inspected",
        )
        for i in ("sent", "not_sent")
    ]
    ok, errors = record_answers(report, err, {"run://r/a.png"})
    assert ok == ["not_sent"]
    assert errors[0].startswith("sent: this question's picture was attached")
