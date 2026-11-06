"""5.A (3.3.2) and 5.C (1.3.1, 4.1.2) on custom fixtures (the Baseline
Alignment TC10.A and TC10.E cases are in test_baseline_cases.py). Expected
outcomes and scripted answers (what a correct agent would say) live here,
never in a page."""

from __future__ import annotations

import re

import pytest

from a11y_assist.models import Answer, ChoiceAnswer, TestId
from a11y_assist.pipeline import answer_questions, run_tt_tests

from .conftest import FIXTURES
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows
from .harness_4c import assert_plain


def labeled(q: str) -> dict:
    return {"J1": {"choice": "labeled", "quote": q}}


NOT_LABELED = {"J1": {"choice": "not_labeled"}}
COMPLETE = {"J1": {"choice": "complete"}}


def missing(q: str) -> dict:
    return {"J1": {"choice": "missing", "quote": q}}


# name -> test -> expected outcome, instance rows (non-PASS rows are listed
# in the finding; PASS rows too, as instance_rows reads the trace), answers.
EXPECTED: dict[str, dict] = {
    "f01-visually-hidden-label": {
        "5.A": {"outcome": "FAIL", "rows": ["M5"], "answers": NOT_LABELED},
        "5.C": {"outcome": "PASS", "rows": ["M5", "M5"]},
    },
    "f02-aria-label-only": {
        "5.A": {"outcome": "FAIL", "rows": ["M5"], "answers": NOT_LABELED},
        "5.C": {"outcome": "PASS", "rows": ["M5", "M5"]},
    },
    "f03-date-format-outside-label": {
        "5.A": {"outcome": "PASS", "rows": ["M2"]},
        "5.C": {
            "outcome": "FAIL",
            "rows": ["M5", "M7"],
            "answers": missing("MM/DD/YYYY"),
        },
    },
    "f04-required-marker-not-announced": {
        "5.A": {"outcome": "PASS", "rows": ["M2"]},
        "5.C": {"outcome": "FAIL", "rows": ["M5", "M7"], "answers": missing("*")},
    },
    "f05-radio-question-not-grouped": {
        "5.A": {"outcome": "PASS", "rows": ["M2", "M2"]},
        "5.C": {
            "outcome": "FAIL",
            "rows": ["M5", "M7", "M7"],
            "answers": missing("Are you a veteran?"),
        },
    },
    "f06-radio-question-grouped": {
        "5.A": {"outcome": "PASS", "rows": ["M2", "M2"]},
        "5.C": {"outcome": "PASS", "rows": ["M5", "M5", "M5"]},
    },
    "f07-phone-parts-unnamed": {
        "5.A": {
            "outcome": "PASS",
            "rows": ["M2", "M4", "M4"],
            "answers": labeled("Phone number"),
        },
        "5.C": {"outcome": "FAIL", "rows": ["M3", "M3", "M5", "M5"]},
    },
    "f08-table-column-headers": {
        "5.A": {
            "outcome": "PASS",
            "rows": ["M4", "M4"],
            "answers": labeled("Full name"),
        },
        "5.C": {"outcome": "PASS", "rows": ["M5", "M6", "M6"], "answers": COMPLETE},
    },
    "f09-icon-search-box": {
        "5.A": {
            "outcome": "PASS",
            "rows": ["M4"],
            "answers": {"J1": {"choice": "graphic", "reasons": "a magnifier icon"}},
        },
        "5.C": {"outcome": "PASS", "rows": ["M5", "M5"]},
    },
    "f10-floating-label-focus-tip": {
        "5.A": {"outcome": "PASS", "rows": ["M2"]},
        "5.C": {
            "outcome": "FAIL",
            "rows": ["M5", "M7"],
            "answers": missing("Use 5 digits"),
        },
    },
    "f11-unnamed-buttons": {
        "5.A": {"outcome": "PASS", "rows": ["M2"]},
        "5.C": {"outcome": "FAIL", "rows": ["M3", "M3", "M5"]},
    },
    # Its image must be taken after scrolling (viewport clip coordinates).
    "f13-field-below-the-fold": {
        "5.A": {"outcome": "PASS", "rows": ["M2"]},
        "5.C": {"outcome": "PASS", "rows": ["M5", "M5"]},
    },
    # Pass R (4.F) opens the disclosure; the "Other" field it reveals is read
    # on that replay.
    "f12-revealed-other-field": {
        "with": ["4.F"],
        "5.A": {"outcome": "PASS", "rows": ["M2", "M4"], "answers": labeled("Other:")},
        "5.C": {"outcome": "FAIL", "rows": ["M3", "M5", "M5", "M5"]},
    },
    # Two options under one legend, nothing beside either: the legend asks
    # the question and labels neither answer.
    "f14-blank-options-under-legend": {
        "5.A": {"outcome": "FAIL", "rows": ["M2o", "M2o"]},
        "5.C": {"outcome": "FAIL", "rows": ["M3o", "M3o", "M5"]},
    },
    # A single option: its legend is its label.
    "f15-single-checkbox-under-legend": {
        "5.A": {"outcome": "PASS", "rows": ["M2"]},
        "5.C": {"outcome": "PASS", "rows": ["M5", "M5"]},
    },
    # The button beside the box labels it (G167): J1, not M3.
    "f16-search-button-beside-box": {
        "5.A": {"outcome": "PASS", "rows": ["M4"], "answers": labeled("Search")},
        "5.C": {"outcome": "PASS", "rows": ["M5", "M5"]},
    },
    # Post-round 1 fix 10: a header's menu button beside a placeholder-only
    # search box does not label it (5.A 1.2.0): M3, no question. Its name
    # comes from a hidden <label>, so screen readers announce "Search".
    "f18-header-menu-beside-search": {
        "5.A": {"outcome": "FAIL", "rows": ["M3"]},
        "5.C": {"outcome": "PASS", "rows": ["M5", "M5", "M5"]},
    },
    # Post-round 1 (5.C 1.2.0): three filter boxes whose only gap is the
    # set's question (a heading, not announced): one J1 for the set, its
    # answer recorded for each box. Judge eval run 22's agent answered
    # missing "Mission status": the heading is the set's question (TT 5.C
    # Note 4), and since 1.3.0 a quote from the heading over an option
    # passes M7's check (Abby, 2026-11-06).
    "f19-filter-boxes-under-heading": {
        "5.A": {"outcome": "PASS", "rows": ["M2", "M2", "M2"]},
        "5.C": {
            "outcome": "FAIL",
            "rows": ["M7", "M7", "M7"],
            "answers": missing("Mission status"),
        },
    },
    # 5.C 1.3.0 (Abby, 2026-11-06; NASA's Missions filters): two groups of
    # boxes under two headings share one field name and no group label, so
    # screen readers hear one flat list: FAIL without a question (M3s).
    "f20-filter-groups-one-name": {
        "5.A": {"outcome": "PASS", "rows": ["M2", "M2", "M2", "M2"]},
        "5.C": {"outcome": "FAIL", "rows": ["M3s", "M3s", "M3s", "M3s"]},
    },
    # Each option's words are beside it but not connected: a person looks
    # (5.A J1); screen readers announce only the question (5.C).
    "f17-option-text-not-connected": {
        "5.A": {
            "outcome": "PASS",
            "rows": ["M4", "M4"],
            "answers": {"J1": {"choice": "labeled", "quote": "Email"}},
        },
        "5.C": {"outcome": "FAIL", "rows": ["M3o", "M3o", "M5"]},
    },
}


def test_every_fixture_is_listed():
    names = {p.stem for p in (FIXTURES / "5a").glob("*.html")}
    assert names == set(EXPECTED)
    for n in names:
        assert re.fullmatch(r"f\d{2}-[a-z0-9-]+", n), n


async def run_both(settings, url: str, answers: dict[str, dict], extra) -> dict:
    """5.A and 5.C in one call (they share pass L), plus any test that
    reveals fields for them. Only 5.A and 5.C questions are answered."""
    tests = [TestId(t) for t in extra] + [TestId.T5A, TestId.T5C]
    out = await run_tt_tests(settings, url, tests)
    assert out.errors == [], out.errors
    report = out.report
    for _ in range(3):
        qs = [q for q in report.open_questions if q.test_id.value in ("5.A", "5.C")]
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
    got = {f.test_id.value: f for f in report.findings}
    for t in ("5.A", "5.C"):
        assert_plain(got[t].summary)
    return got


@pytest.mark.parametrize("name", sorted(EXPECTED))
async def test_outcome(name, settings, server, drafts):  # noqa: F811
    e = EXPECTED[name]
    got = await run_both(
        settings,
        f"{server.base}/5a/{name}.html",
        {t: e[t].get("answers") or {} for t in ("5.A", "5.C")},
        e.get("with", []),
    )
    for t in ("5.A", "5.C"):
        f = got[t]
        assert (f.outcome.value, instance_rows(f)) == (
            e[t]["outcome"],
            e[t]["rows"],
        ), (t, f.rationale, f.summary)


async def test_options_of_one_set_are_asked_about_once(settings, server, drafts):  # noqa: F811
    """5.C 1.2.0 (post-round 1: a NASA page asked 56 alike questions, one
    per filter box, and the agent answered none of them)."""
    out = await run_tt_tests(
        settings,
        f"{server.base}/5a/f19-filter-boxes-under-heading.html",
        [TestId.T5C],
    )
    qs = [q for q in out.report.open_questions if q.test_id is TestId.T5C]
    assert len(qs) == 1, [q.question_id for q in qs]
    [q] = qs
    assert len(q.also_instances) == 2
    assert [c["visible"] for c in q.input["components"]] == [
        ["Active"],
        ["Future"],
        ["Past"],
    ]
