"""4.F (2.4.3-focus-order-meaning) on custom fixtures (no ACT rule covers
2.4.3). Expected outcomes and scripted J1 answers live here, never in a page."""

from __future__ import annotations

import pytest

from a11y_assist.models import TestId

from .conftest import FIXTURES
from .harness import instance_rows, run_check

# "choice" is what a correct judge answers where J1 is asked (test data).
EXPECTED: dict[str, dict] = {
    "f01-logical-order": {"outcome": "PASS", "rows": ["M4"]},
    "f02-address-form-interleaved": {
        "outcome": "FAIL",
        "choice": "does_not_preserve",
        "signals": {"S1", "S5"},
    },
    "f03-footer-first-tabindex": {
        "outcome": "FAIL",
        "choice": "does_not_preserve",
        "signals": {"S1"},
    },
    "f04-independent-columns-reordered": {
        "outcome": "PASS",
        "choice": "preserves",
        "signals": {"S3"},
    },
    "f05-nav-after-main": {"outcome": "PASS", "choice": "preserves", "signals": {"S3"}},
    "f06-social-icons-reordered": {
        "outcome": "DNA",
        "choice": "does_not_matter",
        "signals": {"S3"},
    },
    "f07-one-link": {"outcome": "DNA", "rows": []},
    "f08-menu-not-adjacent": {
        "outcome": "FAIL",
        "choice": "does_not_preserve",
        "signals": {"S6"},
    },
    "f09-disclosure-adjacent": {"outcome": "PASS"},
    "f10-modal-keeps-focus": {"outcome": "PASS", "rows_include": ["M3"]},
    "f11-modal-lets-focus-escape": {"outcome": "FAIL", "rows_include": ["M2"]},
    "f12-native-dialog": {"outcome": "PASS", "rows_include": ["M3"]},
    "f13-eight-accordions": {"outcome": "NEEDS_REVIEW"},
    "f14-backward-order-differs": {
        "outcome": "FAIL",
        "choice": "does_not_preserve",
        "signals": {"S4"},
    },
    "f15-columns-arbitrary": {
        "outcome": "NEEDS_REVIEW",
        "choice": "unsure",
        "signals": {"S3"},
    },
}


def test_every_fixture_is_listed():
    assert {p.stem for p in (FIXTURES / "4f").glob("*.html")} == set(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
async def test_fixture(name, settings, server):
    e = EXPECTED[name]
    got = await run_check(
        settings, f"{server.base}/4f/{name}.html", TestId.T4F, e.get("choice")
    )
    f = got["finding"]
    assert f.outcome.value == e["outcome"], (f.rows, f.summary)
    if "rows" in e:
        assert [r.split("[")[0] for r in instance_rows(f)] == e["rows"], f.rows
    if "rows_include" in e:
        assert set(e["rows_include"]) <= {r.split("[")[0] for r in instance_rows(f)}, (
            f.rows
        )
    if "signals" in e:
        found = {
            c
            for r in f.rows
            if "[" in r
            for c in r.split("[")[1].rstrip("]").split(",")
        }
        assert e["signals"] <= found, (f.rows, f.summary)
