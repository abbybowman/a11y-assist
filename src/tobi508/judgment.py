"""Judgment backends for questions a rule cannot decide on its own.

The rules spec creates OpenQuestions ("open questions" to users). A Judge
answers them now or defers them:

  ClientJudge  defers every question to the calling agent. Questions go out in
               tool output with a rubric and evidence file paths; answers come
               back through the tobi_answer_questions tool. Used because Claude Code
               does not support MCP sampling.
  ApiJudge     will call NASA's hosted model. Not implemented.

Answers are recorded as-is. Turning answers into finding outcomes is the rules
spec's job, so nothing here changes a Finding.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from tobi508.models import (
    Answer,
    DecidedBy,
    OpenQuestion,
    RecordedAnswer,
    Report,
    utcnow,
)


class JudgeResult(BaseModel):
    answers: list[Answer] = Field(default_factory=list)
    pending: list[OpenQuestion] = Field(default_factory=list)


class Judge(ABC):
    name: str

    @abstractmethod
    async def judge(self, questions: list[OpenQuestion]) -> JudgeResult: ...


class ClientJudge(Judge):
    name = "client"

    async def judge(self, questions: list[OpenQuestion]) -> JudgeResult:
        return JudgeResult(pending=list(questions))


class ApiJudge(Judge):
    name = "api"

    def __init__(self, endpoint: str | None = None, model: str | None = None):
        self.endpoint = endpoint
        self.model = model

    async def judge(self, questions: list[OpenQuestion]) -> JudgeResult:
        raise NotImplementedError(
            "ApiJudge is a stub; it will be wired to NASA's hosted model later."
        )


def get_judge(backend: str) -> Judge:
    if backend == "client":
        return ClientJudge()
    if backend == "api":
        return ApiJudge()
    raise ValueError(f"Unknown judge backend {backend!r}; use 'client' or 'api'.")


def has_image(value: Any) -> bool:
    """A run:// picture anywhere in a question's input or evidence."""
    if isinstance(value, str):
        return value.startswith("run://") and value.endswith(".png")
    if isinstance(value, dict):
        return any(has_image(v) for v in value.values())
    if isinstance(value, list):
        return any(has_image(v) for v in value)
    return False


def _unsure(answer: Answer) -> bool:
    if answer.choice is not None:
        return answer.choice.choice == "unsure"
    return answer.j2 is not None and answer.j2.gate == "unsure"


def _picture_links(value: Any) -> set[str]:
    if isinstance(value, str):
        return (
            {value} if value.startswith("run://") and value.endswith(".png") else set()
        )
    if isinstance(value, dict):
        return {x for v in value.values() for x in _picture_links(v)}
    if isinstance(value, list):
        return {x for v in value for x in _picture_links(v)}
    return set()


def _picture_problem(q, answer: Answer, sent: set[str] = frozenset()) -> str | None:
    """Agent follow-through plan, change 3 (Abby, 2026-11-06): development
    runs 5 and 6's agents answered every picture question without opening a
    picture, mostly "unsure". A model's answer to a question whose input
    names a picture says what it shows (`seen`), or, if the picture could
    not be opened or shows nothing, what went wrong (`picture_error`, then
    only unsure). Neither: refused."""
    if answer.decided_by is not DecidedBy.MODEL or not has_image(q.input):
        return None
    if answer.seen.strip():
        return None
    if answer.picture_error.strip():
        if _picture_links(q.input) & sent:
            # Abby, 2026-11-06: picture_error is for a picture that could not
            # be opened. One attached to a result was in front of the agent;
            # a dark or blank one is described in `seen`.
            return (
                "this question's picture was attached to a result, so it was "
                "in front of you: look at it and say in `seen` what it shows "
                "(a dark, blank or cut-off picture is described too, then "
                "answer unsure if it does not settle the question). "
                "picture_error is only for a picture you could not open"
            )
        if _unsure(answer):
            return None
        return (
            "with a picture_error the answer can only be unsure: a picture "
            "that was not seen cannot settle the question"
        )
    return (
        "this question names a picture. Open it (read the run:// resource, or "
        "look at the image attached to the result) and say in `seen` something "
        "it shows, then answer again. If it cannot be opened or shows nothing, "
        "say what happened in `picture_error` and answer unsure"
    )


def record_answers(
    report: Report, answers: list[Answer], sent: set[str] = frozenset()
) -> tuple[list[str], list[str]]:
    """Record answers to questions asked in this run. One answer closes a
    question; a later answer replaces it (a person's answer beats a model's).
    Returns (accepted question ids, error messages)."""
    asked = {q.question_id: q for q in report.questions or report.open_questions}
    accepted, errors = [], []
    for answer in answers:
        q = asked.get(answer.question_id)
        tag = answer.question_id
        if q is None:
            errors.append(f"{tag}: no question with this id in this run")
        elif (
            (q.kind == "J1") != (answer.j1 is not None)
            or (q.kind == "J2") != (answer.j2 is not None)
            or (q.kind == "choice") != (answer.choice is not None)
        ):
            field = {"J1": "j1", "J2": "j2", "choice": "choice"}[q.kind]
            errors.append(f"{tag}: a {q.kind} question needs a `{field}` answer")
        elif q.kind == "choice" and answer.choice.choice not in q.choices:
            errors.append(f"{tag}: choice must be one of {', '.join(q.choices)}")
        elif (picture := _picture_problem(q, answer, sent)) is not None:
            errors.append(f"{tag}: {picture}")
        else:
            viewed = not (
                answer.decided_by is DecidedBy.MODEL
                and has_image(q.input)
                and not answer.seen.strip()
            )
            answer = answer.model_copy(update={"not_viewed": not viewed})
            report.answers.append(
                RecordedAnswer(question=q, answer=answer, recorded_at=utcnow())
            )
            accepted.append(tag)
    done = {r.answer.question_id for r in report.answers}
    report.open_questions = [
        q for q in report.open_questions if q.question_id not in done
    ]
    return accepted, errors


def current_answer(report: Report, question_id: str) -> Answer | None:
    """The answer in force: the latest from a person, else the latest."""
    got = [r.answer for r in report.answers if r.answer.question_id == question_id]
    human = [a for a in got if a.decided_by is DecidedBy.HUMAN]
    return (human or got or [None])[-1]
