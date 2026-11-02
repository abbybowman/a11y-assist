"""5.B (2.4.6, labels) on the vendored W3C ACT cc0f0a cases; expected
outcomes are in fixtures/act/manifest.json (ours follow the visible label,
as DHS's verdicts do). Scripted answers (what a correct agent would say)
live here, never in a page. The TC10.A/TC10.E Baseline cases are in
test_baseline_cases.py."""

from __future__ import annotations

import json

import pytest

from .conftest import ACT_ROOT
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import instance_rows, run_tests
from .scoring import write_score

MANIFEST = json.loads((ACT_ROOT / "manifest.json").read_text())
CASES = {c["id"]: c for c in MANIFEST["cases"] if c["tt_test"] == "5.B"}

ALL = {"J1": {"choice": "all_descriptive"}}


def _not(*n: int) -> dict:
    return {"J1": {"choice": "some_not_descriptive", "elements": list(n)}}


ANSWERS = {
    "9b967559": _not(1),  # "Menu"
    "1e520607": _not(1),
    "fa5104f9": _not(1),
    "3ee841b7": _not(1),  # "Info:" on a date field
    "64994609": _not(1, 2, 3, 4),  # Name/Street twice, headings off screen
    "2f1d9641": _not(1),  # the field's only visible cue is "Go"
}


@pytest.mark.parametrize("case_id", sorted(CASES))
async def test_act_case(case_id, settings, act_server, drafts):  # noqa: F811
    case = CASES[case_id]
    got = await run_tests(
        settings,
        f"{act_server}/{case['path']}",
        ["5.B"],
        {"5.B": ANSWERS.get(case_id, ALL)},
    )
    f = got["5.B"]
    write_score(case_id, f.outcome.value, f.rows)
    assert f.outcome.value == case["expected"], (f.rows, f.summary)
    if case["expected"] == "FAIL":
        assert "M2" in instance_rows(f)


def test_an_option_in_a_set_does_not_take_the_legend_as_its_label():
    """5.B 1.1.0 (5.A's rule): the legend is the option's group, never its
    label. Built evidence: no ACT or Baseline 5.B case has a radio set."""
    from a11y_assist.checks.t5b import items_of
    from a11y_assist.labels import Comp, LabelsPass

    legend = {"text": "How should we contact you?", "shown": True, "group": True}

    def radio(n, own):
        shown = [legend] + (
            [{"text": own, "shown": True, "group": False}] if own else []
        )
        return Comp(
            n=n,
            css=f"#c{n}",
            type="radio",
            option=True,
            set_size=2,
            group="f:radio:contact",
            group_labels=[legend["text"]],
            label_shown=shown,
            nearby=[legend["text"], *([own] if own else [])],
            nearby_own=[own] if own else [],
        )

    items, _, no_label = items_of(
        LabelsPass(components=[radio(1, "Email"), radio(2, "")])
    )
    assert [(i.label, i.group) for i in items] == [("Email", legend["text"])]
    assert legend["text"] not in items[0].near
    assert no_label == 1  # the blank option: no label of its own (5.A M2o)


def test_an_incomplete_label_pass_is_never_dna():
    """5.B 1.1.0: when pass L stopped early, unread fields may have labels to
    judge, so no item is NEEDS REVIEW, not DNA (A2)."""
    from a11y_assist.checks.t5b import State5B, evaluate
    from a11y_assist.labels import Comp, LabelsPass

    field = Comp(n=1, css="#f", type="text")
    full = evaluate(State5B(lp=LabelsPass(components=[field])), [])
    assert (full.outcome.value, full.rows[0]) == ("DNA", "A2")
    lp = LabelsPass(
        components=[field], incomplete=["2 fields inside frames were not checked."]
    )
    cut = evaluate(State5B(lp=lp), [])
    assert cut.outcome.value == "NEEDS_REVIEW"
