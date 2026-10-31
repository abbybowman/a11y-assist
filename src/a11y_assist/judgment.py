"""Judgment backends for questions a rule cannot decide on its own.

The rules spec creates OpenQuestions ("open questions" to users). A Judge
answers them now or defers them:

  ClientJudge  defers every question to the calling agent. Questions go out in
               tool output with a rubric and evidence file paths; answers come
               back through the answer_questions tool. Used because Claude Code
               does not support MCP sampling.
  ApiJudge     will call NASA's hosted model. Not implemented.

Answers are recorded as-is. Turning answers into finding outcomes is the rules
spec's job, so nothing here changes a Finding.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from a11y_assist.models import (
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


def record_answers(
    report: Report, answers: list[Answer]
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
        elif (q.kind == "J1") != (answer.j1 is not None) or (q.kind == "J2") != (
            answer.j2 is not None
        ):
            errors.append(f"{tag}: a {q.kind} question needs a {q.kind.lower()} answer")
        else:
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
