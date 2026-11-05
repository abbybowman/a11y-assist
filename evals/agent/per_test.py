"""Agent A's tool runs against a round's keys, per TT test: development
analysis outside the locked scorer (docs/solutions/agent-eval-scoring.md).
Verdicts come from evals/scoring.py; nothing here decides an outcome.

    uv run python -m evals.agent.per_test --keys evals/judging/round1 \\
        evals/judging/round1/results/arm-a-1 evals/judging/round1/results/arm-a-3
    uv run python -m evals.agent.per_test --keys evals/judging/round1 --as-one \\
        evals/judging/round1-answers/results/arm-a \\
        evals/judging/round1-answers-rest/results/arm-a

Each folder is one run, unless --as-one merges them into one run (one
arm whose pages were split across folders). Within a run, each TT test
comes from the latest finished tool run whose `tests` included it, so a
page split across calls is not lost (post-round 1 plan, fix 13), and
pages a run is not scored on (summary.json, not_scored.json) are left
out, as the locked scorer leaves them out. Prints a
Markdown table: per test, summed over runs and pages.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from a11y_assist import scrt
from a11y_assist.compare import compare, page_key
from evals.judging import _pages, read_keys
from evals.scoring import Verdict, score

UNDECIDED = {Verdict.NEEDS_REVIEW, Verdict.NOT_PERFORMED}


def merged(arm_dirs: list[Path]) -> dict[str, scrt.PreScrt]:
    """One pre-SCRT file per page: each test from the latest finished run
    whose `tests` included it."""
    runs: dict[str, list[tuple[str, list[str], scrt.PreScrt]]] = {}
    for d in arm_dirs:
        for rep in Path(d).glob("runs/*/report.json"):
            pre = rep.parent / "pre-scrt.json"
            r = json.loads(rep.read_text("utf-8"))
            k = page_key(r.get("target"))
            if not pre.is_file() or k is None:
                continue
            runs.setdefault(k, []).append(
                (
                    r.get("finished_at") or "",
                    list(r.get("tests") or []),
                    scrt.parse(pre.read_text("utf-8")),
                )
            )
    out = {}
    for k, found in runs.items():
        found.sort(key=lambda x: x[0])
        base, rows = found[-1][2], []
        for tid, latest in base.results().items():
            for _, tests, pre in reversed(found):
                if tid in tests:
                    latest = pre.results().get(tid, latest)
                    break
            rows += latest
        out[k] = base.model_copy(update={"Criteria": rows})
    return out


def scored_pages(arm_dirs: list[Path]) -> set[str] | None:
    """The pages a run is scored on, as the locked scorer reads them: those
    in summary.json, less any in not_scored.json. None if no summary."""
    pages: set[str] = set()
    found = False
    for d in arm_dirs:
        s = Path(d) / "summary.json"
        if not s.is_file():
            continue
        found = True
        pages |= {page_key(u) for u in json.loads(s.read_text()).get("pages") or []}
        ns = Path(d) / "not_scored.json"
        if ns.is_file():
            pages -= {page_key(u) for u in json.loads(ns.read_text()).get("pages", [])}
    return pages if found else None


def per_test(keys_round: Path, runs: list[list[Path]]) -> dict[str, Counter]:
    keys = read_keys(keys_round, _pages(keys_round))
    out: dict[str, Counter] = {}
    for run in runs:
        tool, given = merged(run), scored_pages(run)
        for url, (_, ref) in keys.items():
            mine = tool.get(page_key(url))
            if mine is None or (given is not None and page_key(url) not in given):
                continue
            for t in score(compare(ref, mine)).tests:
                if t.verdict is Verdict.NOT_SCORED:
                    continue
                c = out.setdefault(t.test.test_id, Counter())
                c["undecided" if t.verdict in UNDECIDED else t.verdict.value] += 1
    return out


def table(counts: dict[str, Counter]) -> str:
    lines = [
        "| Test | Agree | False PASS | False FAIL | Other | Undecided |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for tid, c in counts.items():
        other = sum(
            n
            for v, n in c.items()
            if v not in ("agree", "false_pass", "false_fail", "undecided")
        )
        lines.append(
            f"| {tid} | {c['agree']} | {c['false_pass']} | {c['false_fail']} | "
            f"{other} | {c['undecided']} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--keys", type=Path, required=True, help="round folder with keys/")
    ap.add_argument(
        "--as-one", action="store_true", help="merge the folders into one run"
    )
    ap.add_argument("arms", type=Path, nargs="+", help="arm folders (each holds runs/)")
    a = ap.parse_args(argv)
    runs = [a.arms] if a.as_one else [[d] for d in a.arms]
    print(table(per_test(a.keys, runs)))


if __name__ == "__main__":
    main()
