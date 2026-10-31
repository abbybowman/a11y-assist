"""Judge backends."""

from __future__ import annotations

import pytest

from a11y_assist.judgment import ApiJudge, ClientJudge, get_judge
from a11y_assist.models import OpenQuestion, TestId

Q = OpenQuestion(
    question_id="q1",
    test_id=TestId.T4C,
    kind="J1",
    instance="i1",
    question="?",
    rubric="r",
    input={"text": []},
)


async def test_client_judge_defers_every_question():
    result = await ClientJudge().judge([Q])
    assert result.answers == [] and result.pending == [Q]


async def test_api_judge_is_a_stub():
    with pytest.raises(NotImplementedError):
        await ApiJudge().judge([Q])


def test_get_judge():
    assert isinstance(get_judge("client"), ClientJudge)
    assert isinstance(get_judge("api"), ApiJudge)
    with pytest.raises(ValueError):
        get_judge("other")
