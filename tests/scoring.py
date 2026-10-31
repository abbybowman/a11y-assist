"""Score our 4.C outcomes on the ACT cases against DHS's TT 5.1 results and
ACT's expected results, printed at the end of the test run.

NEEDS_REVIEW matches neither answer key and is reported as its own rate. A
mismatch is a finding to write up, never a reason to change rule code.
"""

from __future__ import annotations

import json
from pathlib import Path

from .conftest import ACT_ROOT

RESULTS_FILE = Path(__file__).parent / ".act_scores.json"


def write_score(case_id: str, outcome: str, rows: list[str]) -> None:
    data = json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else {}
    data[case_id] = {"outcome": outcome, "rows": rows}
    RESULTS_FILE.write_text(json.dumps(data, indent=1))


def report_lines() -> list[str]:
    if not RESULTS_FILE.exists():
        return []
    ours = json.loads(RESULTS_FILE.read_text())
    cases = {
        c["id"]: c
        for c in json.loads((ACT_ROOT / "manifest.json").read_text())["cases"]
    }
    lines: list[str] = []
    for tt in sorted({cases[cid]["tt_test"] for cid in ours}):
        mine = {cid: got for cid, got in ours.items() if cases[cid]["tt_test"] == tt}
        rules = sorted({r for cid in mine for r in cases[cid]["act_expected"]})
        lines.append(f"{tt} on W3C ACT cases (rules {', '.join(rules)})")
        dhs_n = dhs_ok = act_n = act_ok = review = 0
        mismatches = []
        for cid, got in sorted(mine.items()):
            c = cases[cid]
            o = got["outcome"]
            review += o == "NEEDS_REVIEW"
            if c["dhs_tt51"]:
                dhs_n += 1
                dhs_ok += o == c["dhs_tt51"]
                if o != c["dhs_tt51"]:
                    mismatches.append(
                        f"  {cid} ours {o} vs DHS {c['dhs_tt51']} rows {got['rows']}"
                    )
            for rule, exp in c["act_expected"].items():
                act_n += 1
                act_ok += o == exp
                if o != exp:
                    mismatches.append(
                        f"  {cid} ours {o} vs ACT {rule} {exp} rows {got['rows']}"
                    )
        lines.append(
            f"  agreement with DHS TT 5.1: {dhs_ok}/{dhs_n}"
            + (" (DHS publishes no results for these rules)" if not dhs_n else "")
        )
        lines.append(f"  agreement with ACT expected (per rule): {act_ok}/{act_n}")
        lines.append(f"  NEEDS_REVIEW: {review}/{len(mine)}")
        lines.append("  mismatches:" if mismatches else "  mismatches: none")
        lines += mismatches
    return lines
