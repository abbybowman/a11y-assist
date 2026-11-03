"""SCRT and pre-SCRT files: reading, writing from a report, and comparing.

The SCRT sample was made by SCRT itself (tests/fixtures/scrt/make_sample.py);
what it holds is asserted here, never written into the file.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from a11y_assist import catalog, scrt
from a11y_assist.compare import Change, change, compare, summary
from a11y_assist.models import (
    NOT_CERTIFIED_DISCLAIMER,
    TEST_NOT_PERFORMED_NOTE,
    DecidedBy,
    Finding,
    Instance,
    Outcome,
    Report,
    TestId,
    Versions,
)
from a11y_assist.scrt import NotAReport
from a11y_assist.scrt import ScrtResult as R

from .conftest import FIXTURES

SAMPLE = FIXTURES / "scrt" / "sample-scrt.json"
SHOT = FIXTURES / "scrt" / "shot.png"


def test_template_rows_are_the_catalog_tests_in_order():
    ids = [r.TestID for r in scrt.template_rows()]
    assert ids == catalog.active_ids()  # 61; SCRT writes "7. D", " 1.A"
    one = scrt.template_rows()[0]
    assert one.DisabilityImpact[:2] == ["Without Vision", "With Limited Vision"]
    assert all(r.TestResult is None for r in scrt.template_rows())


def test_scrt_sample_reads_as_a_persons_results():
    doc = scrt.parse(SAMPLE.read_text())
    assert doc.origin == "scrt" and doc.certified is False
    assert doc.Product.P_Name == "Sample product"
    assert (doc.Tester.T_fstnm, doc.Tester.T_lstnm) == ("Sam", "Tester")
    assert doc.Tester.T_ID is None  # " " in the file
    assert doc.Tester.T_eval == "Trusted Tester"
    assert len(doc.Criteria) == 62  # 61 tests + one child issue
    assert all(r.source.by == "person" for r in doc.Criteria)
    rows = doc.results()
    parent, child = rows["1.A"]
    assert (parent.TestResult, child.TestResult) == (R.FAIL, R.FAIL)
    # SCRT saves a newline as a literal " \n ".
    assert parent.TesterComment == 'Says "hello"\nsecond line'
    assert (parent.location, parent.GlobalIssue) == ("Header logo", "Yes")
    assert parent.ImageSrc.startswith("data:image/png;base64,")
    assert (child.parent, child.location, child.ImageSrc) == (0, "Footer", None)
    assert rows["2.A"][0].TestResult is R.DNA
    assert rows["3.A"][0].TestResult is R.NOT_TESTED
    assert (rows["4.A"][0].TestResult, rows["4.A"][0].GlobalIssue) == (R.PASS, "No")
    assert rows["4.B"][0].TestResult is None  # never chosen: saved as ""


@pytest.mark.parametrize(
    "text, message",
    [
        ("not json", "Not JSON"),
        ("{}", "Not a pre-SCRT file"),
        ('{"format": "pre-scrt/9"}', "Not a pre-SCRT file"),
        ("[1, 2]", "Not an SCRT or pre-SCRT file"),
        ('[{"Criteria": [{"TestID": "99.Z"}]}]', "Unknown TT 5.1.3 test ID"),
        ('[{"Criteria": [{"TestID": "1.A", "TestResult": "Maybe"}]}]', "Unknown SCRT"),
    ],
)
def test_other_files_are_refused(text, message):
    with pytest.raises(NotAReport, match=message):
        scrt.parse(text)


def test_no_selection_and_placeholders_are_blank():
    d = json.dumps(
        [
            {
                "Criteria": [
                    {
                        "TestID": " 7. D",
                        "TestResult": "No Selection",
                        "GlobalIssue": "None",
                        "location": " ",
                    }
                ]
            }
        ]
    )
    [row] = scrt.parse(d).Criteria
    assert (row.TestID, row.TestResult, row.GlobalIssue, row.location) == (
        "7.D",
        None,
        None,
        None,
    )


# ── Writing from a report ────────────────────────────────────────────────────


def _report(findings: list[Finding]) -> Report:
    t = datetime(2026, 11, 2, tzinfo=timezone.utc)
    return Report(
        run_id="r1",
        target="https://example.gov/form",
        final_url="https://example.gov/form",
        tests=[f.test_id.value for f in findings],
        started_at=t,
        finished_at=t,
        versions=Versions(
            a11y_assist="0",
            andi="29.2.2",
            jquery="3.7.1",
            playwright="1",
            browser_channel="chromium",
            browser="140",
            os="test",
            python="3",
            rules_spec={"4.C": "1.0.0", "5.A": "1.2.0"},
            judging_model="none",
        ),
        findings=findings,
        evidence_dir="evidence",
    )


def _run_dir(tmp_path: Path) -> Path:
    (tmp_path / "evidence" / "shots").mkdir(parents=True)
    (tmp_path / "evidence" / "shots" / "a.png").write_bytes(SHOT.read_bytes())
    (tmp_path / "evidence" / "shots" / "b.png").write_bytes(SHOT.read_bytes())
    return tmp_path


def test_report_becomes_61_rows_with_sources(tmp_path):
    fail = Finding(
        test_id=TestId.T5A,
        test_name="x",
        outcome=Outcome.FAIL,
        summary="Two fields have no visible label.",
        rows=["B2"],
        decided_by=DecidedBy.RULE,
        instances=[
            Instance(description="Email field", evidence_refs=["evidence/shots/a.png"]),
            Instance(selector="#phone", evidence_refs=["evidence/shots/b.png"]),
        ],
    )
    review = Finding(
        test_id=TestId.T4C,
        test_name="x",
        outcome=Outcome.NEEDS_REVIEW,
        summary="A person needs to check this.",
        rows=["J1"],
        evidence_refs=["evidence/walk.json", "evidence/shots/a.png"],
    )
    doc = scrt.from_report(_report([fail, review]), _run_dir(tmp_path), "abc")
    assert doc.format == "pre-scrt/1" and doc.certified is False
    assert doc.Product.P_Notes == NOT_CERTIFIED_DISCLAIMER
    assert doc.Tester.T_eval == scrt.AGENT_EVAL and doc.Tester.T_fstnm is None
    assert doc.runs[0].report_sha256 == "abc"
    rows = doc.results()
    assert list(rows) == catalog.active_ids()
    assert len(doc.Criteria) == 62  # 5.A has a child row

    p, c = rows["5.A"]
    assert (p.TestResult, c.TestResult) == (R.FAIL, R.FAIL)
    assert (p.location, c.location) == ("Email field", "#phone")
    assert p.TesterComment == "Two fields have no visible label."
    assert c.parent == doc.Criteria.index(p)
    assert p.ImageSrc.startswith("data:image/png;base64,") and c.ImageSrc
    assert p.source.by == "tool" and p.source.spec_version == "1.2.0"
    assert (p.source.rows, p.source.decided_by, p.source.outcome) == (
        ["B2"],
        "rule",
        "FAIL",
    )

    [r] = rows["4.C"]
    assert r.TestResult is None and r.needs_review
    assert r.ImageSrc  # the first screenshot among its evidence
    assert r.source.performed and r.source.outcome == "NEEDS_REVIEW"

    [n] = rows["1.A"]  # not in the run
    assert n.TestResult is None and n.needs_review and not n.source.performed
    assert n.TesterComment.startswith(TEST_NOT_PERFORMED_NOTE)
    assert n.TestCondition and n.DisabilityImpact  # SCRT's text kept


def test_screenshots_past_the_cap_become_a_note(tmp_path, monkeypatch):
    monkeypatch.setattr(scrt, "MAX_IMAGE_BYTES", SHOT.stat().st_size)  # room for one
    fail = Finding(
        test_id=TestId.T5A,
        test_name="x",
        outcome=Outcome.FAIL,
        summary="s",
        instances=[
            Instance(description="a", evidence_refs=["evidence/shots/a.png"]),
            Instance(description="b", evidence_refs=["evidence/shots/b.png"]),
        ],
    )
    p, c = scrt.from_report(_report([fail]), _run_dir(tmp_path)).results()["5.A"]
    assert p.ImageSrc and c.ImageSrc is None
    assert "run://r1/evidence/shots/b.png" in c.TesterComment


def test_screenshot_paths_stay_inside_the_run(tmp_path):
    fail = Finding(
        test_id=TestId.T5A,
        test_name="x",
        outcome=Outcome.FAIL,
        summary="s",
        instances=[Instance(evidence_refs=["../outside.png"])],
    )
    (tmp_path / "outside.png").write_bytes(SHOT.read_bytes())
    run = tmp_path / "run"
    run.mkdir()
    [p] = scrt.from_report(_report([fail]), run).results()["5.A"]
    assert p.ImageSrc is None


def test_pre_scrt_round_trips(tmp_path):
    doc = scrt.from_report(_report([]), _run_dir(tmp_path))
    again = scrt.parse(scrt.dump(doc))
    assert again == doc
    assert isinstance(json.loads(scrt.dump(doc)), dict)  # not SCRT's array


# ── Comparing ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "first, second, expected",
    [
        (None, None, Change.NEITHER),
        (None, R.PASS, Change.ONLY_SECOND),
        (R.FAIL, None, Change.ONLY_FIRST),
        (R.PASS, R.PASS, Change.SAME),
        (R.FAIL, R.PASS, Change.CHANGED),
        (R.PASS, R.FAIL, Change.CHANGED),
    ],
)
def test_changes(first, second, expected):
    assert change(first, second) is expected


def test_child_rows_summarize_fail_first():
    rows = scrt.parse(SAMPLE.read_text()).results()
    assert summary(rows["1.A"]) is R.FAIL and summary(rows["4.B"]) is None


def test_compare_is_neutral_before_and_after_a_fix(tmp_path):
    # A person's report (Fail on 1.A, Pass on 4.A), then the tool's after a
    # fix: the comparison says what changed, never that a file was wrong.
    before = scrt.parse(SAMPLE.read_text())
    before.Product.P_Location = "https://www.example.gov/form/"
    findings = [
        Finding(test_id=TestId.T1A, test_name="x", outcome=Outcome.PASS),
        Finding(test_id=TestId.T2A, test_name="x", outcome=Outcome.DNA),
        Finding(test_id=TestId.T4A, test_name="x", outcome=Outcome.FAIL),
    ]
    after = scrt.from_report(_report(findings), _run_dir(tmp_path))
    c = compare(before, after)
    assert c.same_page  # www., trailing slash and scheme ignored
    by = {t.test_id: t for t in c.tests}
    assert by["1.A"].change is Change.CHANGED
    assert (by["1.A"].first.result, by["1.A"].second.result) == (R.FAIL, R.PASS)
    assert by["2.A"].change is Change.SAME
    assert by["3.A"].change is Change.ONLY_FIRST  # the run did not include it
    assert not by["3.A"].second.performed
    assert by["4.B"].change is Change.NEITHER
    assert [t.test_id for t in c.changes()] == ["1.A", "3.A", "4.A"]
    assert sum(c.counts.values()) == 61
    assert "false_pass" not in c.model_dump_json()  # no verdict words
