"""SCRT report files: the pre-SCRT format, reading SCRT and pre-SCRT files,
and writing a pre-SCRT file from a run's report.

SCRT (DHS's Section 508 Compliance Reporting Tool, third_party/scrt/) saves
a TT 5.1.3 test record as JSON: a one-item array with Product, System and
Tester blocks and one Criteria row per test (more rows for child issues).
pre-SCRT keeps SCRT's shape and field names where they mean the same thing,
typed for Python, plus what agent-assisted results need: the disclaimer,
where each row came from, which rows need a person, and a person's review.
It is a top-level object, so SCRT (which reads `jsonData[0]`) cannot load
it as a formal report (tests/test_scrt_tool.py loads one in SCRT to check).

No outcome is decided here. A tool row copies the outcome the rules spec
produced (principle 2); a row read from an SCRT file is a person's.
Quirks of SCRT's files: docs/solutions/scrt-format.md.
"""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import re
from datetime import datetime
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from tobi508 import catalog
from tobi508.config import REPO_ROOT
from tobi508.models import (
    NOT_CERTIFIED_DISCLAIMER,
    TEST_NOT_PERFORMED_NOTE,
    Outcome,
    Report,
)

FORMAT = "pre-scrt/1"
TEMPLATE = (
    REPO_ROOT / "third_party" / "scrt" / "Resources" / "SuccessCriteriaTT5.1.3.json"
)
AGENT_EVAL = "Agent-assisted (not a Trusted Tester evaluation)"
EVAL_VERSION = "v.5.1.3"
# Inline screenshots per file, in bytes of image data. Past this, a row keeps
# a note pointing to the run's evidence instead of the image.
MAX_IMAGE_BYTES = 4_000_000
_IMAGE = re.compile(r"\.(png|jpe?g|gif)$", re.I)


class ScrtResult(str, Enum):
    """SCRT's result names (createReport.js). Blank is None, never a result."""

    PASS = "Pass"
    FAIL = "Fail"
    DNA = "Does Not Apply"
    NOT_TESTED = "Not Tested"


# The spec's outcome written in SCRT's words. NEEDS_REVIEW has no SCRT word:
# the row stays blank and is flagged for a person.
RESULT_OF: dict[Outcome, ScrtResult | None] = {
    Outcome.PASS: ScrtResult.PASS,
    Outcome.FAIL: ScrtResult.FAIL,
    Outcome.DNA: ScrtResult.DNA,
    Outcome.NOT_TESTED: ScrtResult.NOT_TESTED,
    Outcome.NEEDS_REVIEW: None,
}


class ScrtProduct(BaseModel):
    P_Name: str | None = None
    P_Version: str | None = None
    P_Owner: str | None = None
    P_Type: str | None = None
    P_Location: str | None = Field(default=None, description="The page URL.")
    P_Desc: str | None = None
    P_Notes: str | None = None


class Browser(BaseModel):
    name: str
    version: str | None = None


class ScrtSystem(BaseModel):
    os: list[str] = Field(default_factory=list)
    browsers: list[Browser] = Field(default_factory=list)


class ScrtTester(BaseModel):
    T_fstnm: str | None = None
    T_lstnm: str | None = None
    T_companyname: str | None = None
    T_cntc: str | None = None
    T_ID: str | None = Field(default=None, description="Trusted Tester number.")
    T_Role: str | None = None
    T_scope: str | None = None
    T_Date: str | None = None
    T_eval: str | None = None
    T_evalMthd_Vrsn: str | None = None


class Source(BaseModel):
    """Where a row's result came from."""

    by: Literal["tool", "person"]
    run_id: str | None = None
    spec_version: str | None = None
    outcome: str | None = Field(
        default=None, description="The tool's outcome (e.g. NEEDS_REVIEW)."
    )
    performed: bool = Field(
        default=True, description="False when the tool did not perform the test."
    )
    rows: list[str] = Field(default_factory=list, description="Spec rows (audit).")
    decided_by: str | None = None


class Review(BaseModel):
    checked: bool = False
    by: str | None = None
    at: datetime | None = None


class Row(BaseModel):
    TestID: str
    TestName: str | None = None
    Test: str | None = None
    CrtID: str | None = None
    Guideline: str | None = None
    TestCondition: str | None = None
    DisabilityImpact: list[str] = Field(default_factory=list)
    TestResult: ScrtResult | None = None
    needs_review: bool = Field(
        default=False, description="The tool could not decide: a person must."
    )
    TesterComment: str | None = None
    location: str | None = None
    GlobalIssue: Literal["Yes", "No"] | None = None
    ImageSrc: str | None = Field(default=None, description="Screenshot data URL.")
    ImageSrc2: str | None = Field(default=None, description="Remediation screenshot.")
    RemediationDetails: str | None = None
    RemediationDate: str | None = None
    parent: int | None = Field(
        default=None, description="Index of the row this is a child issue of."
    )
    source: Source
    review: Review | None = None


class RunRef(BaseModel):
    run_id: str
    report_sha256: str | None = None
    versions: dict[str, Any] = Field(default_factory=dict)


class Site(BaseModel):
    name: str | None = None
    pages: list[str] = Field(default_factory=list)


class PreScrt(BaseModel):
    format: Literal["pre-scrt/1"] = FORMAT
    disclaimer: str = NOT_CERTIFIED_DISCLAIMER
    certified: Literal[False] = False
    origin: Literal["pre-scrt", "scrt"] = Field(
        default="pre-scrt", description="The format the file was read from."
    )
    Product: ScrtProduct = Field(default_factory=ScrtProduct)
    System: ScrtSystem = Field(default_factory=ScrtSystem)
    Tester: ScrtTester = Field(default_factory=ScrtTester)
    site: Site | None = None
    runs: list[RunRef] = Field(default_factory=list)
    Criteria: list[Row] = Field(default_factory=list)

    def results(self) -> dict[str, list[Row]]:
        """Rows by test ID, in file order (a parent and its child issues)."""
        out: dict[str, list[Row]] = {}
        for r in self.Criteria:
            out.setdefault(r.TestID, []).append(r)
        return out


class NotAReport(ValueError):
    """The text is neither an SCRT nor a pre-SCRT file."""


# ── Reading ──────────────────────────────────────────────────────────────────


def normalize_id(raw: str) -> str:
    """'7. D' and ' 1.A' -> '7.D', '1.A'; must be a TT 5.1.3 test ID."""
    tid = re.sub(r"\s+", "", raw or "")
    if tid not in catalog.tests():
        raise NotAReport(f"Unknown TT 5.1.3 test ID {raw!r}")
    return tid


def _text(v: Any) -> str | None:
    """SCRT writes empty as '' or ' ' (and sometimes 'undefined')."""
    if v is None:
        return None
    s = str(v)
    if s.strip() in ("", "undefined", "null"):
        return None
    # SCRT saves a newline as a literal " \\n " (createReport.js escapes).
    return s.replace(" \\n ", "\n").replace("\\n", "\n").strip()


def impacts(raw: str | None) -> list[str]:
    """ "'Without Vision', 'With Limited Vision'" -> a list, duplicates dropped."""
    out: list[str] = []
    for part in (raw or "").split(","):
        name = part.strip().strip("'").strip()
        if name and name not in out:
            out.append(name)
    return out


def _result(v: Any) -> ScrtResult | None:
    s = _text(v)
    if s is None or s == "No Selection":
        return None
    try:
        return ScrtResult(s)
    except ValueError:
        raise NotAReport(f"Unknown SCRT test result {s!r}") from None


def _global(v: Any) -> Literal["Yes", "No"] | None:
    s = _text(v)
    return s if s in ("Yes", "No") else None


def from_scrt(record: dict[str, Any]) -> PreScrt:
    """One SCRT record (the array's first item) as pre-SCRT; every result in
    it is a person's."""
    p = record.get("Product") or {}
    s = record.get("System") or {}
    t = record.get("Tester") or {}
    browsers = [
        Browser(name=b.strip(), version=None)
        for b in str(s.get("S_selectedBrowser") or "").split(",")
        if b.strip()
    ]
    rows: list[Row] = []
    first: dict[str, int] = {}
    for c in record.get("Criteria") or []:
        tid = normalize_id(c.get("TestID", ""))
        parent = first.get(tid)
        first.setdefault(tid, len(rows))
        rows.append(
            Row(
                TestID=tid,
                TestName=_text(c.get("TestName")),
                Test=_text(c.get("Test")),
                CrtID=_text(c.get("CrtID")),
                Guideline=_text(c.get("Guideline")),
                TestCondition=_text(c.get("TestCondition")),
                DisabilityImpact=impacts(c.get("DisabilityImpact")),
                TestResult=_result(c.get("TestResult")),
                TesterComment=_text(c.get("TesterComment")),
                location=_text(c.get("location")),
                GlobalIssue=_global(c.get("GlobalIssue")),
                ImageSrc=_text(c.get("ImageSrc")),
                ImageSrc2=_text(c.get("ImageSrc2")),
                RemediationDetails=_text(c.get("RemediationDetails")),
                RemediationDate=_text(c.get("RemediationDate")),
                parent=parent,
                source=Source(by="person"),
            )
        )
    return PreScrt(
        origin="scrt",
        Product=ScrtProduct(**{k: _text(p.get(k)) for k in ScrtProduct.model_fields}),
        System=ScrtSystem(
            os=[
                o.strip()
                for o in str(s.get("S_selectedOS") or "").split(",")
                if o.strip()
            ],
            browsers=browsers,
        ),
        Tester=ScrtTester(**{k: _text(t.get(k)) for k in ScrtTester.model_fields}),
        Criteria=rows,
    )


def parse(text: str) -> PreScrt:
    """Read an SCRT or pre-SCRT file. Raises NotAReport for anything else."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise NotAReport(f"Not JSON: {exc.msg} at line {exc.lineno}") from None
    if isinstance(data, dict):
        if data.get("format") != FORMAT:
            raise NotAReport(
                f"Not a pre-SCRT file (format {str(data.get('format'))[:40]!r})"
            )
        doc = PreScrt.model_validate(data)
        for r in doc.Criteria:
            r.TestID = normalize_id(r.TestID)
        return doc
    if (
        isinstance(data, list)
        and data
        and isinstance(data[0], dict)
        and isinstance(data[0].get("Criteria"), list)
    ):
        return from_scrt(data[0])
    raise NotAReport("Not an SCRT or pre-SCRT file")


@cache
def template_rows() -> tuple[Row, ...]:
    """The TT 5.1.3 template's rows: SCRT's text for each test, no results."""
    doc = from_scrt(json.loads(TEMPLATE.read_text("utf-8"))[0])
    return tuple(doc.Criteria)


# ── Writing from a run ───────────────────────────────────────────────────────


def _data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


class _Images:
    """Screenshots inlined up to MAX_IMAGE_BYTES per file."""

    def __init__(self, run_dir: Path, run_id: str):
        self.run_dir, self.run_id, self.used = run_dir.resolve(), run_id, 0

    def first(self, refs: list[str]) -> tuple[str | None, str | None]:
        """(data URL, note) for the first screenshot in refs."""
        for ref in refs:
            if not _IMAGE.search(ref):
                continue
            path = (self.run_dir / ref).resolve()
            if not path.is_relative_to(self.run_dir) or not path.is_file():
                continue
            size = path.stat().st_size
            if self.used + size > MAX_IMAGE_BYTES:
                return None, (
                    "Screenshot left out to keep this file small: "
                    f"run://{self.run_id}/{ref} (while the run is kept)."
                )
            self.used += size
            return _data_url(path), None
        return None, None


def _not_run_reason(test_id: str, report: Report) -> str:
    from tobi508.checks import REGISTRY
    from tobi508.models import TestId

    if TestId(test_id) not in REGISTRY:
        return "the tool does not perform this test yet."
    return "it was not selected for this run."


def from_report(
    report: Report, run_dir: Path, report_sha256: str | None = None
) -> PreScrt:
    """One page's run as a pre-SCRT file: the template's 61 rows in order,
    each carrying the spec's outcome in SCRT's words. A FAIL with several
    instances becomes a parent row and child rows, one per instance."""
    findings = {f.test_id.value: f for f in report.findings}
    images = _Images(run_dir, report.run_id)
    rows: list[Row] = []
    for tmpl in template_rows():
        base = tmpl.model_dump(
            include={
                "TestID",
                "TestName",
                "Test",
                "CrtID",
                "Guideline",
                "TestCondition",
                "DisabilityImpact",
            }
        )
        f = findings.get(tmpl.TestID)
        if f is None:
            rows.append(
                Row(
                    **base,
                    needs_review=True,
                    TesterComment=f"{TEST_NOT_PERFORMED_NOTE}: "
                    + _not_run_reason(tmpl.TestID, report),
                    source=Source(
                        by="tool",
                        run_id=report.run_id,
                        performed=False,
                        outcome=Outcome.NEEDS_REVIEW.value,
                    ),
                )
            )
            continue
        source = Source(
            by="tool",
            run_id=report.run_id,
            spec_version=report.versions.rules_spec.get(tmpl.TestID),
            outcome=f.outcome.value,
            performed=f.note != TEST_NOT_PERFORMED_NOTE,
            rows=f.rows,
            decided_by=f.decided_by.value if f.decided_by else None,
        )
        result = RESULT_OF[f.outcome]
        places = f.instances if f.outcome is Outcome.FAIL else []
        parent = len(rows)
        for n, inst in enumerate(places or [None]):
            refs = (inst.evidence_refs if inst else []) + (
                f.evidence_refs if n == 0 else []
            )
            img, img_note = images.first(refs)
            comment = f.summary if n == 0 else None
            if img_note:
                comment = f"{comment}\n{img_note}" if comment else img_note
            rows.append(
                Row(
                    **base,
                    TestResult=result,
                    needs_review=result is None,
                    TesterComment=comment or None,
                    location=(inst.description or inst.selector) if inst else None,
                    ImageSrc=img,
                    parent=None if n == 0 else parent,
                    source=source,
                )
            )
    finished = report.finished_at or report.started_at
    v = report.versions
    return PreScrt(
        Product=ScrtProduct(
            P_Name=report.final_url or report.target,
            P_Location=report.final_url or report.target,
            P_Desc=f"Agent-assisted test run {report.run_id}",
            P_Notes=NOT_CERTIFIED_DISCLAIMER,
        ),
        System=ScrtSystem(
            os=[v.os],
            browsers=[Browser(name=v.browser_channel, version=v.browser)],
        ),
        Tester=ScrtTester(
            T_Date=finished.isoformat(),
            T_eval=AGENT_EVAL,
            T_evalMthd_Vrsn=EVAL_VERSION,
        ),
        runs=[
            RunRef(
                run_id=report.run_id,
                report_sha256=report_sha256,
                versions=v.model_dump(mode="json"),
            )
        ],
        Criteria=rows,
    )


def dump(doc: PreScrt) -> str:
    return doc.model_dump_json(indent=1, exclude_none=False) + "\n"


def write_for_run(run_dir: Path, report_path: Path, report: Report) -> Path:
    """Write <run>/pre-scrt.json beside report.json."""
    sha = hashlib.sha256(report_path.read_bytes()).hexdigest()
    out = run_dir / "pre-scrt.json"
    out.write_text(dump(from_report(report, run_dir, sha)), encoding="utf-8")
    return out
