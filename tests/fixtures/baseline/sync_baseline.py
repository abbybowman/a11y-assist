"""Vendor Section 508 ICT Baseline Alignment test cases (section508.gov).

Run deliberately, then review the diff:

    uv run python -I tests/fixtures/baseline/sync_baseline.py

Pages are saved byte for byte under their URL path and never edited; tests
serve this folder as the web root and never fetch from the network. Expected
outcomes are ours (docs/rules/4a-*, 4b-*) and live only in manifest.json.
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
