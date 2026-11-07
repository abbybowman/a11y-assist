"""5.F (3.3.1) and 5.G (3.3.3) on custom fixtures (the Baseline Alignment
TC10.D cases are in test_baseline_cases.py). Expected outcomes and scripted
answers (what a correct agent would say) live here, never in a page."""

from __future__ import annotations

import re

import pytest

from tobi508.models import Answer, ChoiceAnswer, TestId
from tobi508.pipeline import answer_questions, run_tt_tests

from .conftest import FIXTURES
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows
from .harness_4c import assert_plain

PICK_SEND = {"J0": {"choice": "element", "element": 2}}

# name -> test -> expected outcome, instance rows, scripted answers
EXPECTED: dict[str, dict[str, dict]] = {
    "f01-native-validation": {
        "5.F": {"outcome": "PASS", "rows": ["M2", "M2", "M2"]},
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4", "N4", "N4"],
            "answers": {"J1": {"choice": "guides", "quote": "Please"}},
        },
    },
    "f02-server-side-form": {
        "5.F": {"outcome": "NEEDS_REVIEW", "rows": []},
        "5.G": {"outcome": "NEEDS_REVIEW", "rows": []},
    },
    "f03-error-summary-focused": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6", "M6", "M6", "M6"],
            "answers": {"J1": {"choice": "described", "quote": "Enter"}},
        },
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4", "N4", "N4", "N4"],
            "answers": {"J1": {"choice": "guides", "quote": "Enter"}},
        },
    },
    "f04-inline-errors-live-region": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6", "M6", "M6", "M6"],
            "answers": {"J1": {"choice": "described", "quote": ": enter"}},
        },
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4", "N4", "N4", "N4"],
            "answers": {"J1": {"choice": "guides", "quote": "like"}},
        },
    },
    "f05-aria-invalid-only": {
        "5.F": {"outcome": "FAIL", "rows": ["M3"]},
        "5.G": {"outcome": "FAIL", "rows": ["N3"]},
    },
    "f06-password-only": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6", "M6"],
            "answers": {
                "J1": {
                    "choice": "described",
                    "quote": "password you entered is incorrect",
                }
            },
        },
        "5.G": {"outcome": "DNA", "rows": ["N2", "N2"]},
    },
    "f07-save-draft-and-continue": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6"],
            "answers": {"J1": {"choice": "described", "quote": "City: enter"}},
        },
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4"],
            "answers": {"J1": {"choice": "guides", "quote": "enter the city"}},
        },
    },
    "f08-errors-on-leaving-only": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6"],
            "answers": {"J1": {"choice": "described", "quote": "must be a number"}},
        },
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4"],
            "answers": {"J1": {"choice": "guides", "quote": "like 1250"}},
        },
    },
    "f09-valid-look-only": {
        "5.F": {
            "outcome": "DNA",
            "rows": [],
            "answers": {"J2": {"choice": "not_error"}},
        },
        "5.G": {
            "outcome": "DNA",
            "rows": [],
            "answers": {"J2": {"choice": "not_error"}},
        },
    },
    "f10-no-format-given": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6", "M6"],
            "answers": {
                "J1": {"choice": "described", "quote": "Date of birth: invalid entry."}
            },
        },
        "5.G": {
            "outcome": "FAIL",
            "rows": ["N5", "N5"],
            "answers": {"J1": {"choice": "no_guidance"}},
        },
    },
    "f11-agent-picks-send": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6", "M6"],
            "answers": {
                **PICK_SEND,
                "J1": {"choice": "described", "quote": "Your email address: enter"},
            },
        },
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4", "N4"],
            "answers": {
                **PICK_SEND,
                "J1": {"choice": "guides", "quote": "like name@example.com"},
            },
        },
    },
    "f12-save-sends": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6", "M6"],
            "answers": {"J1": {"choice": "described", "quote": "Phone number: enter"}},
        },
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4", "N4"],
            "answers": {"J1": {"choice": "guides", "quote": "enter 10 digits"}},
        },
    },
    # Native date fields get a date outside their range (spec 0.6.0).
    "f13-date-after-max": {
        "5.F": {"outcome": "PASS", "rows": ["M2", "M2"]},
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4", "N4"],
            # One scripted quote for both errors: the field's label, from
            # input.instructions (the check accepts a quote from either).
            "answers": {"J1": {"choice": "guides", "quote": "Date of the change"}},
        },
    },
    "f14-birth-date-in-future": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6", "M6"],
            "answers": {"J1": {"choice": "described", "quote": "Date of birth:"}},
        },
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4", "N4"],
            "answers": {"J1": {"choice": "guides", "quote": "Date of birth:"}},
        },
    },
    # The page cancels the invalid event (no browser message) and only sets
    # aria-invalid: not M2, the field is marked with no text.
    "f15-cancelled-browser-message": {
        "5.F": {"outcome": "FAIL", "rows": ["M3", "M3"]},
        "5.G": {"outcome": "FAIL", "rows": ["N3", "N3"]},
    },
    # 1,200 paragraphs before a footer form: only text new after the press
    # is read, so its error is found however long the page is.
    "f17-long-page-footer-form": {
        "5.F": {
            "outcome": "PASS",
            "rows": ["M6", "M6"],
            "answers": {"J1": {"choice": "described", "quote": ": enter"}},
        },
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4", "N4"],
            "answers": {"J1": {"choice": "guides", "quote": "like"}},
        },
    },
    # No button: both attempts press Enter in the field (empty, then "abc").
    "f16-no-button": {
        "5.F": {"outcome": "PASS", "rows": ["M2", "M2"]},
        "5.G": {
            "outcome": "PASS",
            "rows": ["N4", "N4"],
            "answers": {"J1": {"choice": "guides", "quote": "Please"}},
        },
    },
    # Post-round 1 fix 17 (Abby, 2026-11-05): a site search accepts any
    # input, so both are Does Not Apply (A3s), though it was sent.
    "f18-site-search": {
        "5.F": {"outcome": "DNA", "rows": []},
        "5.G": {"outcome": "DNA", "rows": []},
    },
    # A required search box is not free input: empty, the browser names it
    # (M2); with "abc" it is sent, and the server's reply cannot be seen (A4).
    "f19-site-search-required": {
        "5.F": {"outcome": "NEEDS_REVIEW", "rows": []},
        "5.G": {
            "outcome": "NEEDS_REVIEW",
            "rows": [],
            "answers": {"J1": {"choice": "guides", "quote": "Please"}},
        },
    },
}


def test_every_fixture_is_listed():
    names = {p.stem for p in (FIXTURES / "5f").glob("*.html")}
    assert names == set(EXPECTED)
    for n in names:
        assert re.fullmatch(r"f\d{2}-[a-z0-9-]+", n), n


async def run_both(settings, url: str, answers: dict[str, dict]) -> dict:
    """5.F and 5.G in one call, as a client runs them: 5.G reads the error
    pass 5.F collected (one pass per call). Each test's scripted answers
    are keyed by the question ID's last part (J0, J1, J2)."""
    out = await run_tt_tests(settings, url, [TestId.T5F, TestId.T5G])
    assert out.errors == [], out.errors
    report = out.report
    for _ in range(3):
        if not report.open_questions:
            break
        sent = []
        for q in report.open_questions:
            f = (answers.get(q.test_id.value) or {}).get(
                q.question_id.rsplit("-", 1)[-1]
            )
            assert f is not None, f"{url}: no scripted answer for {q.question_id}"
            sent.append(
                Answer(
                    question_id=q.question_id,
                    choice=ChoiceAnswer(**{"reasons": "scripted test answer", **f}),
                    rationale="scripted test answer",
                    seen="scripted: the picture was not opened",
                )
            )
        res = await answer_questions(settings, out.run_id, sent)
        assert res.errors == [] and res.rejected == [], (res.errors, res.rejected)
        report = res.report
    got = {f.test_id.value: f for f in report.findings}
    for f in got.values():
        assert_plain(f.summary)
    return got


@pytest.mark.parametrize("name", sorted(EXPECTED))
async def test_outcome(name, settings, server, drafts):  # noqa: F811
    e = EXPECTED[name]
    got = await run_both(
        settings,
        f"{server.base}/5f/{name}.html",
        {tt: x.get("answers") or {} for tt, x in e.items()},
    )
    for tt, x in e.items():
        f = got[tt]
        assert (f.outcome.value, instance_rows(f)) == (x["outcome"], x["rows"]), (
            tt,
            f.rationale,
            f.summary,
        )
