"""Vendor Section 508 ICT Baseline Alignment test cases (section508.gov).

Run deliberately, then review the diff:

    uv run python -I tests/fixtures/baseline/sync_baseline.py

Pages are saved byte for byte under their URL path and never edited; tests
serve this folder as the web root and never fetch from the network. Expected
outcomes are ours (docs/rules/4a-*, 4b-*, 5d-*) and live only in manifest.json.
Baseline's own expected result is recorded beside ours for scoring.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOST = "https://baselinealignment.section508.gov"

# case -> (test file path, Baseline's expected result, our expected outcome
# per TT test, why ours differs if it does)
CASES = {
    "TC01.A-1-fail-1": (
        "/testfiles/TF01/01.A-1-fail-1.html",
        "FAIL",
        {"4.A": "FAIL", "4.B": "PASS"},
        "",
    ),
    "TC01.A-2-fail-1": (
        "/testfiles/TF01/01.A-2-fail-1.html",
        "FAIL",
        {"4.A": "PASS", "4.B": "NEEDS_REVIEW"},
        "4.B: the page's integrity hash for jQuery is wrong, so Chrome blocks the "
        "script and holding Space does nothing; the documented timing cannot be "
        "confirmed (verified against the cdnjs file, 2026-10-31).",
    ),
    # Every control is disabled: no focus, no functionality. Baseline judges
    # only 4.C and 4.D here; 4.A, 4.B, 4.E and 4.F follow from the same fact.
    "TC01.B-ic-dna-1": (
        "/testfiles/TF01/01.B-ic-dna-1.html",
        "DNA",
        {t: "DNA" for t in ("4.A", "4.B", "4.C", "4.D", "4.E", "4.F")},
        "",
    ),
    "TC02.A-ic-dna-1": (
        "/testfiles/TF02/02.A-ic-dna-1.html",
        "DNA",
        {t: "DNA" for t in ("4.A", "4.B", "4.C", "4.D", "4.E", "4.F")},
        "",
    ),
    # 5.D On input (3.2.2), Baseline test 10.C.
    "TC10.C-3-fail-1": (
        "/testfiles/TF10/10.C-3-fail-1.html",
        "FAIL",
        {"5.D": "FAIL"},
        "",
    ),
    "TC10.C-3-fail-2": (
        "/testfiles/TF10/10.C-3-fail-2.html",
        "FAIL",
        {"5.D": "FAIL"},
        "",
    ),
    "TC10.C-3-fail-3": (
        "/testfiles/TF10/10.C-3-fail-3.html",
        "FAIL",
        {"5.D": "FAIL"},
        "",
    ),
    "TC10.C-all-pass": (
        "/testfiles/TF10/10.C-all-pass-1.html",
        "PASS",
        {"5.D": "PASS"},
        "",
    ),
    "TC10.C-ic-dna-1": (
        "/testfiles/TF10/10.C-ic-dna-1.html",
        "DNA",
        {"5.D": "DNA"},
        "",
    ),
    # 5.F Error identification (3.3.1), Baseline test 10.D; 5.G (3.3.3)
    # continues from it (docs/rules/5f-*, 5g-*). No 10.F (3.3.3) cases exist.
    "TC10.D-2-fail-1": (
        "/testfiles/TF10/10.D-2-fail-1.html",
        "FAIL",
        {"5.F": "FAIL", "5.G": "PASS"},
        '5.G: Baseline judges 3.3.1 only; "Error: not a number." tells the '
        "user to enter a number.",
    ),
    "TC10.D-2-fail-2": (
        "/testfiles/TF10/10.D-2-fail-2.html",
        "FAIL",
        {"5.F": "FAIL", "5.G": "FAIL"},
        "",
    ),
    "TC10.D-2-fail-3": (
        "/testfiles/TF10/10.D-2-fail-3.html",
        "FAIL",
        {"5.F": "FAIL", "5.G": "FAIL"},
        "",
    ),
    "TC10.D-all-pass-1": (
        "/testfiles/TF10/10.D-all-pass-1.html",
        "PASS",
        {"5.F": "PASS", "5.G": "PASS"},
        "",
    ),
    "TC10.D-all-pass-2": (
        "/testfiles/TF10/10.D-all-pass-2.html",
        "PASS",
        {"5.F": "PASS", "5.G": "PASS"},
        "",
    ),
    "TC10.D-all-pass-3": (
        "/testfiles/TF10/10.D-all-pass-3.html",
        "PASS",
        {"5.F": "PASS", "5.G": "PASS"},
        "",
    ),
    "TC10.D-ic-dna-1": (
        "/testfiles/TF10/10.D-ic-dna-1.html",
        "DNA",
        {"5.F": "DNA", "5.G": "DNA"},
        "",
    ),
    # 5.A (3.3.2, Baseline 10.E) and 5.C (1.3.1/4.1.2, Baseline 10.A),
    # docs/rules/5a-*, 5c-*. Baseline judges one test per case; the other
    # test's expectation is ours.
    "TC10.A-1-fail-1": (
        "/testfiles/TF10/10.A-1-fail-1.html",
        "FAIL",
        {"5.A": "PASS", "5.C": "FAIL", "5.B": "PASS"},
        '5.A: Baseline judges the name only; "First Name:" is visible beside '
        "the field.",
    ),
    "TC10.A-all-pass-1": (
        "/testfiles/TF10/10.A-all-pass-1.html",
        "PASS",
        {"5.A": "FAIL", "5.C": "PASS", "5.B": "DNA"},
        "5.A: Baseline judges the name only; a placeholder alone is not a visual "
        "label (5.A spec M3; W3C forms tutorial; w3c/wcag#4918). 5.B: no visual "
        "label to judge (DNA).",
    ),
    "TC10.A-all-pass-2": (
        "/testfiles/TF10/10.A-all-pass-2.html",
        "PASS",
        {"5.A": "PASS", "5.C": "PASS", "5.B": "PASS"},
        "",
    ),
    "TC10.A-all-pass-3": (
        "/testfiles/TF10/10.A-all-pass-3.html",
        "PASS",
        {"5.A": "PASS", "5.C": "PASS", "5.B": "PASS"},
        "",
    ),
    "TC10.A-all-pass-4": (
        "/testfiles/TF10/10.A-all-pass-4.html",
        "PASS",
        {"5.A": "PASS", "5.C": "PASS", "5.B": "PASS"},
        "",
    ),
    "TC10.A-all-pass-5": (
        "/testfiles/TF10/10.A-all-pass-5.html",
        "PASS",
        {"5.A": "PASS", "5.C": "PASS", "5.B": "PASS"},
        "",
    ),
    "TC10.A-all-pass-6": (
        "/testfiles/TF10/10.A-all-pass-6.html",
        "PASS",
        {"5.A": "PASS", "5.C": "PASS", "5.B": "PASS"},
        "",
    ),
    "TC10.A-ic-dna-1": (
        "/testfiles/TF10/10.A-ic-dna-1.html",
        "DNA",
        {"5.A": "DNA", "5.C": "DNA", "5.B": "DNA"},
        "",
    ),
    "TC10.A-ic-dna-2": (
        "/testfiles/TF10/10.A-ic-dna-2.html",
        "DNA",
        {"5.A": "DNA", "5.C": "DNA", "5.B": "DNA"},
        "",
    ),
    "TC10.E-1-fail-1": (
        "/testfiles/TF10/10.E-1-fail-1.html",
        "FAIL",
        {"5.A": "FAIL", "5.C": "FAIL", "5.B": "DNA"},
        "",
    ),
    "TC10.E-1-pass-1": (
        "/testfiles/TF10/10.E-1-pass-1.html",
        "PASS",
        {"5.A": "PASS", "5.C": "PASS", "5.B": "FAIL"},
        '5.C: the name repeats the visible label; whether "The sky is blue" '
        "describes the field is 5.B's (5.C spec M5). 5.B: it does not (10.E "
        "judges presence only).",
    ),
    "TC10.E-1-pass-2": (
        "/testfiles/TF10/10.E-1-pass-2.html",
        "PASS",
        {"5.A": "PASS", "5.C": "PASS", "5.B": "PASS"},
        "",
    ),
    "TC10.E-1-pass-3": (
        "/testfiles/TF10/10.E-1-pass-3.html",
        "PASS",
        {"5.A": "PASS", "5.C": "PASS", "5.B": "PASS"},
        "",
    ),
    # 5.H Error prevention (3.3.4), Baseline 10.G: one-page scripted order
    # forms; the TT makes a one-page form DNA (Abby, 2026-11-02).
    "TC10.G-2.a-pass-1": (
        "/testfiles/TF10/10.G-2.a-pass-1.html",
        "PASS",
        {"5.H": "DNA"},
        "5.H: one page (the TT's applicability); Baseline tests it (reversible).",
    ),
    "TC10.G-2.b-pass-1": (
        "/testfiles/TF10/10.G-2.b-pass-1.html",
        "PASS",
        {"5.H": "DNA"},
        "5.H: one page (the TT's applicability); Baseline tests it (checked).",
    ),
    "TC10.G-2.c-pass-1": (
        "/testfiles/TF10/10.G-2.c-pass-1.html",
        "PASS",
        {"5.H": "PASS"},
        "",
    ),
    "TC10.G-all-fail-1": (
        "/testfiles/TF10/10.G-all-fail-1.html",
        "FAIL",
        {"5.H": "DNA"},
        "5.H: one page (the TT's applicability); Baseline tests it.",
    ),
    "TC10.G-ic-dna-1": (
        "/testfiles/TF10/10.G-ic-dna-1.html",
        "DNA",
        {"5.H": "DNA"},
        "",
    ),
    "TC10.G-ic-dna-2": (
        "/testfiles/TF10/10.G-ic-dna-2.html",
        "DNA",
        {"5.H": "DNA"},
        "",
    ),
}


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 - fixed host
        return r.read()


def main() -> None:
    cases, files = [], {}
    for cid, (path, baseline, ours, why) in CASES.items():
        local = HERE / path.lstrip("/")
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(fetch(HOST + path))
        rel = local.relative_to(HERE).as_posix()
        files[rel] = hashlib.sha256(local.read_bytes()).hexdigest()
        cases.append(
            {
                "id": cid,
                "summary": f"{HOST}/testcases/{cid}.html",
                "path": rel,
                "baseline_expected": baseline,
                "expected": ours,
                "differs": why,
            }
        )
    manifest = {
        "source": HOST,
        "license": "U.S. Government work",
        "cases": cases,
        "files": files,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")


if __name__ == "__main__":
    main()
