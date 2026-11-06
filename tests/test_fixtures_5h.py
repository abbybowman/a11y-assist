"""5.H (3.3.4) on custom fixtures (tests/fixtures/5h/); the Baseline TC10.G
cases are in test_baseline_cases.py. Expected outcomes and scripted
answers (what a correct agent would say) live here, never in a page."""

from __future__ import annotations

import pytest

from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import run_tests

MULTI = {"choice": "multi_step", "element": 1}

# fixture -> (expected outcome, rows, answers)
EXPECTED: dict[str, tuple[str, list[str], dict]] = {
    "f01-checks-input": ("PASS", ["A6", "f1:M1", "G4"], {"J1": MULTI}),
    "f02-no-review": (
        "FAIL",
        ["A6", "f1:M3", "G2"],
        {"J1": MULTI, "J2": {"choice": "none"}},
    ),
    "f03-cancel-period": (
        "PASS",
        ["A6", "f1:M2", "G4"],
        {"J1": MULTI, "J2": {"choice": "reversible"}},
    ),
    "f04-server-step": (
        "NEEDS_REVIEW",
        ["A6", "f1:M4", "G3"],
        {"J1": MULTI, "J2": {"choice": "unsure"}},
    ),
    "f05-newsletter": ("DNA", ["A3", "G1"], {}),
    # G168 and G155: a confirmation before the final payment.
    "f06-confirm-dialog": (
        "PASS",
        ["A6", "f1:M2", "G4"],
        {"J1": MULTI, "J2": {"choice": "review_step"}},
    ),
    "f07-confirm-checkbox": (
        "PASS",
        ["A6", "f1:M2", "G4"],
        {"J1": MULTI, "J2": {"choice": "review_step"}},
    ),
}


@pytest.mark.parametrize("name", sorted(EXPECTED))
async def test_fixture(name, settings, server, drafts):  # noqa: F811
    outcome, rows, answers = EXPECTED[name]
    got = await run_tests(
        settings, f"{server.base}/5h/{name}.html", ["5.H"], {"5.H": answers}
    )
    f = got["5.H"]
    assert f.outcome.value == outcome, (f.rows, f.summary)
    assert f.rows == rows, f.rows


def test_an_incomplete_pass_is_never_dna():
    """5.H 1.1.0: forms or text the error pass did not read may hold the
    hint, so no hint plus an incomplete pass is NEEDS REVIEW (A2), not DNA."""
    from tobi508.checks.t5h import Form5H, State5H, evaluate

    form = Form5H(n=1, id="form1", fields=["Name"], buttons=["Send"])
    done = evaluate(State5H(forms=[form]), [])
    assert (done.outcome.value, done.rows[0]) == ("DNA", "A3")
    cut = evaluate(State5H(forms=[form], incomplete=["A form is inside a frame."]), [])
    assert (cut.outcome.value, cut.rows[0]) == ("NEEDS_REVIEW", "A2")
