"""Data model invariants."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tobi508.models import Finding, Outcome, Report, TestId, Versions


def _versions() -> Versions:
    return Versions(
        tobi508="0",
        andi="29.2.2",
        jquery="3.7.1",
        playwright="1.63.0",
        browser_channel="chrome",
        browser=None,
        os="test",
        python="3",
        rules_spec={"4.C": "1.0.0"},
        judging_model="none",
    )


def test_test_ids_are_the_active_tt_conditions_with_names() -> None:
    ids = [t.value for t in TestId]
    assert len(ids) == 61 and ids[:2] == ["1.A", "1.B"] and ids[-1] == "20.A"
    assert "5.E" not in ids and "6.B" not in ids  # obsolete and removed
    assert TestId.T4C.tt_name == "2.1.2-no-keyboard-trap"
    assert TestId.T4D.wcag_sc == "2.4.7 Focus Visible"


def test_finding_defaults_to_needs_review() -> None:
    f = Finding(test_id=TestId.T4A, test_name=TestId.T4A.tt_name)
    assert f.outcome is Outcome.NEEDS_REVIEW
    assert f.decided_by is None


def test_report_cannot_claim_certification() -> None:
    kwargs = dict(
        run_id="r",
        target="https://nasa.gov",
        started_at=datetime.now(timezone.utc),
        versions=_versions(),
        evidence_dir="x",
    )
    report = Report(**kwargs)
    assert report.certified is False
    assert "NOT a certified" in report.disclaimer
    with pytest.raises(ValidationError):
        Report(**kwargs, certified=True)
