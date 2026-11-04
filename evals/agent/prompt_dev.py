"""Development prompt versions for Agent A: round 1's task (prompt.py, which
the round 1 lock covers and must not change) plus one paragraph. Runs with
these are never scored as a round (docs/plans/2026-11-04-post-round1-fixes.md
fix 9); they show what the tool does when the agent is told how to use it.

    uv run python -m evals.agent.run --route cli --arm a --prompt answers-v1 <round>
"""

from __future__ import annotations

from evals.agent import prompt as base

# Each version: the paragraph inserted before the RESULT instruction.
EXTRA = {
    # Abby, 2026-11-04: Agent A must answer every open question, and rerun
    # calls cut short by the time limit with no_time_limit.
    "answers-v1": (
        "The a11y tools may return open questions with their findings. "
        "Answering them is part of the test, not optional: answer every open "
        "question with a11y_answer_questions, following each question's "
        'rubric, before you give your results. Answer "unsure" when the '
        "evidence does not settle a question. A finding stays NEEDS_REVIEW "
        "until its questions are answered. If answering returns more "
        "questions, answer those too. If a call stops before every test "
        "finishes (a time limit, or a page refused as too large), call it "
        "again with no_time_limit set to true, so that every test finishes."
    ),
}

ANCHOR = "When you are done, end your reply"


def task(urls: list[str], version: str) -> str:
    t = base.task(urls)
    if version == base.PROMPT_VERSION:
        return t
    i = t.index(ANCHOR)
    return t[:i] + EXTRA[version] + "\n\n" + t[i:]


def versions() -> list[str]:
    return [base.PROMPT_VERSION, *EXTRA]
