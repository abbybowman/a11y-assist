"""Score our 4.C outcomes on the ACT cases against DHS's TT 5.1 results and
ACT's expected results, printed at the end of the test run.

NEEDS_REVIEW matches neither answer key and is reported as its own rate. A
mismatch is a finding to write up, never a reason to change rule code.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .conftest import ACT_ROOT

RESULTS_DIR = Path(__file__).parent / ".act_scores"


def _mine() -> Path:
    # One file per pytest-xdist worker ("gw0", ...; "main" when serial), so
    # parallel workers never write the same file.
    return RESULTS_DIR / f"{os.environ.get('PYTEST_XDIST_WORKER', 'main')}.json"


def clear_scores() -> None:
    for f in RESULTS_DIR.glob("*.json"):
        f.unlink()


def write_score(case_id: str, outcome: str, rows: list[str]) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    f = _mine()
    data = json.loads(f.read_text()) if f.exists() else {}
    data[case_id] = {"outcome": outcome, "rows": rows}
    f.write_text(json.dumps(data, indent=1))


def _all_scores() -> dict:
    out: dict = {}
    for f in sorted(RESULTS_DIR.glob("*.json")):
        out.update(json.loads(f.read_text()))
    return out


def _gated(rows: list[str]) -> str:
    """2.A-2.C: the mechanism works, but ER 3's tests are not all built, so
    PASS is held back (2c spec E3). Not a disagreement."""
    return " (gated: ER 3)" if any(r.endswith("/E3") for r in rows) else ""


def report_lines() -> list[str]:
    ours = _all_scores()
    if not ours:
        return []
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
                        + _gated(got["rows"])
                    )
            for rule, exp in c["act_expected"].items():
                act_n += 1
                act_ok += o == exp
                if o != exp:
                    mismatches.append(
                        f"  {cid} ours {o} vs ACT {rule} {exp} rows {got['rows']}"
                        + _gated(got["rows"])
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
