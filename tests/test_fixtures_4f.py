"""4.F (2.4.3-focus-order-meaning) on custom fixtures (no ACT rule covers
2.4.3). Expected outcomes and scripted J1 answers live here, never in a page."""

from __future__ import annotations

import pytest

from tobi508.models import TestId

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
    # 1.3.0: the form at the end of a long page; image A is the crop around
    # the stops the signals name (test_order_image_is_cropped_to_the_signals).
    "f19-long-report-form-interleaved": {
        "outcome": "FAIL",
        "choice": "does_not_preserve",
        "signals": {"S1"},
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
    # Focus reads "Step 3, Step 4, Step 1, Step 2": numbered steps out of
    # sequence (was "unsure"; the judge eval's agent was right, Abby 2026-10-31).
    # Post-round 1 fix 16: a site overlay (role=dialog, aria-modal) that
    # shows itself is not the dialog the menu button opened (it names its
    # list with aria-controls), so Tab leaving it is not M2. The overlay sits
    # between the button and its menu, so Tab after opening the menu lands
    # in the overlay: J1 decides (judge eval run 18: does_not_preserve, which
    # a careful tester would say too).
    "f16-site-overlay-not-the-menu": {
        "outcome": "FAIL",
        "choice": "does_not_preserve",
        "signals": {"S6"},
    },
    # Post-round 1 fix 16 (4.F 1.2.0's rubric): a card grid read row by row,
    # each card's image link then its title link, preserves meaning.
    "f17-card-grid-row-by-row": {"outcome": "PASS", "choice": "preserves"},
    # Post-round 1 fix 16 (1.2.0): filter boxes drawn apart from their
    # labels are placed by their labels, so a one-column list raises no
    # order signal.
    "f18-filter-boxes-drawn-apart": {"outcome": "PASS", "rows": ["M4"]},
    "f15-columns-arbitrary": {
        "outcome": "FAIL",
        "choice": "does_not_preserve",
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


async def test_unsure_goes_to_a_person(settings, server):
    # M9: an unsure answer is NEEDS REVIEW (f15 is the page; its right answer
    # is does_not_preserve, but any page asking J1 would do).
    got = await run_check(
        settings, f"{server.base}/4f/f15-columns-arbitrary.html", TestId.T4F, "unsure"
    )
    assert got["finding"].outcome.value == "NEEDS_REVIEW"


async def test_backward_order_is_in_the_question(settings, server):
    # Judge eval 2026-10-31: without the Shift+Tab order the agent judged only
    # the forward order on f14 and answered "preserves" (a false PASS).
    from tobi508.pipeline import run_tt_tests

    out = await run_tt_tests(
        settings, f"{server.base}/4f/f14-backward-order-differs.html", [TestId.T4F]
    )
    [q] = out.open_questions
    assert [s["name"] for s in q.input["backward"]] == ["Four", "Two", "Three", "One"]
    assert "Shift+Tab" in q.question


async def test_order_image_is_cropped_to_the_signals(settings, server):
    """1.3.0: on a long page, J1's image A is the parts of the order image
    around the stops the signals name; the full page stays evidence. A full
    page shrunk to 768 px was unreadable (development run 9)."""
    from PIL import Image

    from tobi508.pipeline import run_tt_tests

    out = await run_tt_tests(
        settings,
        f"{server.base}/4f/f19-long-report-form-interleaved.html",
        [TestId.T4F],
    )
    [q] = [q for q in out.report.open_questions if q.test_id is TestId.T4F]
    crop, full = q.input["image_a_order"], q.evidence_paths[-1]
    assert crop.endswith("4f-order-crop.png") and full.endswith("4f-order.png"), q
    assert "around the elements" in q.input["image_shows"]
    run = settings.runs_dir / out.run_id
    c = Image.open(run / crop.split(out.run_id + "/", 1)[1])
    f = Image.open(run / full.split(out.run_id + "/", 1)[1])
    assert c.height * 3 < f.height, (c.size, f.size)
