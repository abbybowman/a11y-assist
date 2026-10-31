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
    """Move answered questions from report.open_questions to report.answers.

    Returns (accepted question ids, error messages). An answer is rejected if
    its question is not pending or its outcome is not allowed for it.
    """
    pending = {q.question_id: q for q in report.open_questions}
    accepted, errors = [], []
    for answer in answers:
        question = pending.get(answer.question_id)
        if question is None:
            errors.append(f"{answer.question_id}: no pending question with this id")
            continue
        if answer.outcome not in question.allowed_outcomes:
            allowed = ", ".join(o.value for o in question.allowed_outcomes)
            errors.append(
                f"{answer.question_id}: outcome {answer.outcome.value} not allowed "
                f"(allowed: {allowed})"
            )
            continue
        report.answers.append(
            RecordedAnswer(question=question, answer=answer, recorded_at=utcnow())
        )
        del pending[answer.question_id]
        accepted.append(answer.question_id)
    report.open_questions = list(pending.values())
    return accepted, errors
