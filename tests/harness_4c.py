"""Run 4.C on a page end to end, answering open questions with scripted
answers that stand in for the calling agent. The answers are test data (what a
correct judge would say about the page), never outcomes; they live in the test
files, never in a page."""

from __future__ import annotations

import re
from typing import Any

from a11y_assist.models import Answer, J1Answer, J2Answer, TestId
from a11y_assist.pipeline import answer_questions, run_tt_tests

NO_DOCS = {"documented": "no"}


async def run_4c(
    settings,
    url: str,
    j1: dict | None = None,
    j2: dict | None = None,
    no_time_limit: bool = False,
) -> dict[str, Any]:
    out = await run_tt_tests(settings, url, [TestId.T4C], no_time_limit=no_time_limit)
    assert out.errors == [], out.errors
    report = out.report
    for _ in range(3):
        if not report.open_questions:
            break
        answers = []
        for q in report.open_questions:
            if q.kind == "J2":
                assert j2 is not None, f"{url}: J2 asked but the test gives no answer"
            answers.append(
                Answer(
                    question_id=q.question_id,
                    j1=J1Answer(**(j1 or NO_DOCS)) if q.kind == "J1" else None,
                    j2=J2Answer(**j2) if q.kind == "J2" else None,
                    rationale="scripted test answer",
                )
            )
        res = await answer_questions(settings, out.run_id, answers)
        assert res.errors == [] and res.rejected == [], (res.errors, res.rejected)
        report = res.report
    [finding] = [f for f in report.findings if f.test_id is TestId.T4C]
    assert_plain(finding.summary)
    return {"finding": finding, "open": [q.question_id for q in report.open_questions]}


def instance_rows(finding) -> list[str]:
    return sorted(r.split(":")[1] for r in finding.rows if ":" in r)


# Spec codes and jargon that must never reach the plain-language summary
# (CLAUDE.md principle 8). Row IDs stay in Finding.rows and the rationale.
SPEC_CODES = re.compile(r"\b(?:[AGM]\d{1,2}|J[12]|P[1-6]|V\d{1,2}|Spec|DNA|HtT)\b")


def assert_plain(summary: str) -> None:
    assert summary, "every finding needs a plain-language summary"
    # Quoted text is the page's own (element names, page instructions).
    found = SPEC_CODES.findall(re.sub(r'"[^"]*"', '""', summary))
    assert not found, (found, summary)
