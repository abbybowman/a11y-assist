"""Data model invariants."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from a11y_assist.models import Finding, Outcome, Report, TestId, Versions


def _versions() -> Versions:
    return Versions(
        a11y_assist="0",
        andi="29.2.2",
        jquery="3.7.1",
        playwright="1.63.0",
        browser_channel="chrome",
        browser=None,
        os="test",
        python="3",
        rules_spec="none",
        judging_model="none",
    )


def test_test_ids_cover_4a_to_4f_with_names() -> None:
    assert [t.value for t in TestId] == ["4.A", "4.B", "4.C", "4.D", "4.E", "4.F"]
    assert TestId.T4C.tt_name == "2.1.2-no-keyboard-trap"


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
