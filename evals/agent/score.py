"""Score both arms of an agent round against the tester's SCRT files
(docs/plans/2026-10-31-agent-eval.md section 8), after the lock and the
reveal:

    uv run python -m evals.agent.score evals/judging/<round>

- Relayed outcome, per WCAG 2.0 criterion, both arms: each arm's RESULT
  line against the keys rolled up to the criterion (scoring.rollup).
- Server outcome, Agent A only: the tool's own pre-SCRT files, per TT test
  (as judging rounds score) and rolled up per criterion, so a gap between
  what the tool found and what the agent reported shows.
- Efficiency: tokens, wall time and tool calls from each arm's summary.

Writes <round>/agent-score.json and agent-score.md. Neutral on outcomes:
the verdicts and weights are evals/scoring.py's.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from a11y_assist import scrt
from a11y_assist.compare import compare, page_key, summary
from a11y_assist.scrt import ScrtResult
from evals.agent.prompt import criteria
from evals.judging import _pages, _verify, read_keys
from evals.scoring import (
    SEVERITY,
    Verdict,
    rates,
    rollup,
    totals,
    verdict,
    weighted,
)
from evals.scoring import score as score_page

WORDS = {
    "PASS": ScrtResult.PASS,
    "FAIL": ScrtResult.FAIL,
    "DNA": ScrtResult.DNA,
    "NEEDS_REVIEW": None,
}
MISSING = "missing"


def parse_result(final: str) -> dict | None:
    """The last line starting with RESULT:, as JSON; None if none parses."""
    for line in reversed(final.splitlines()):
        line = line.strip()
        if line.startswith("RESULT:"):
            try:
                got = json.loads(line[len("RESULT:") :])
            except ValueError:
                return None
            return got if isinstance(got, dict) else None
    return None


def relayed(result: dict | None, url: str, sc: str) -> tuple[object, list[str]]:
    """(ScrtResult, None for needs review, or MISSING; failing elements)."""
    if result is None:
        return MISSING, []
    page = next((v for k, v in result.items() if page_key(k) == page_key(url)), None)
    entry = page.get(sc) if isinstance(page, dict) else None
    if not isinstance(entry, dict) or entry.get("result") not in WORDS:
        return MISSING, []
    els = entry.get("elements") or []
    return WORDS[entry["result"]], [str(e) for e in els][:20]


def _counts(verdicts: list[Verdict]) -> dict[str, int]:
    out = {v.value: 0 for v in Verdict}
    for v in verdicts:
        out[v.value] += 1
    return out


def tool_files(arm_dir: Path) -> dict[str, scrt.PreScrt]:
    """Agent A's tool runs: the latest finished run of each page."""
    best: dict[str, tuple[str, Path]] = {}
    for rep in (arm_dir / "runs").glob("*/report.json"):
        r = json.loads(rep.read_text("utf-8"))
        pre = rep.parent / "pre-scrt.json"
        k = page_key(r.get("target"))
        if not pre.is_file() or k is None:
            continue
        when = r.get("finished_at") or ""
        if k not in best or when > best[k][0]:
            best[k] = (when, pre)
    return {k: scrt.parse(p.read_text("utf-8")) for k, (_, p) in best.items()}


def score(rd: Path) -> dict:
    lk = _verify(rd)
    pages = _pages(rd)
    keys = read_keys(rd, pages)
    cs = criteria()
    out: dict = {
        "round": rd.name,
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "lock_commit": lk["code_commit"],
        "pages": len(pages),
        "pages_with_keys": len(keys),
        "criteria": [c["id"] for c in cs],
        "arms": {},
    }
    key_tt = {
        url: {tid: summary(rows) for tid, rows in ref.results().items()}
        for url, (_, ref) in keys.items()
    }
    for arm_dir in sorted((rd / "results").glob("arm-*")):
        s = json.loads((arm_dir / "summary.json").read_text())
        final = (arm_dir / "final.md").read_text("utf-8")
        result = parse_result(final)
        rows, verdicts = [], []
        # Each run is scored on the pages it was given (summary.json): a
        # page corrected after a run (round 1's typo) is not that run's.
        given = {page_key(u) for u in s.get("pages") or []}
        not_given = [u for u in keys if page_key(u) not in given]
        for url in keys:
            if url in not_given:
                continue
            for c in cs:
                kv = rollup([key_tt[url].get(t) for t in c["tests"]])
                got, els = relayed(result, url, c["id"])
                if kv is None:
                    v = Verdict.NOT_SCORED
                elif got == MISSING:
                    v = Verdict.NO_ANSWER
                else:
                    v = verdict(kv, got, True)
                verdicts.append(v)
                rows.append(
                    {
                        "page": url,
                        "criterion": c["id"],
                        "key": kv.value if kv else None,
                        "arm": got if got in (MISSING, None) else got.value,
                        "verdict": v.value,
                        "elements": els,
                    }
                )
        counts = _counts(verdicts)
        arm = {
            "result_line": "found" if result is not None else "missing or malformed",
            "pages_not_given": not_given,
            "per_criterion": {
                "counts": counts,
                "weighted": weighted(counts),
                "rates": rates(counts),
            },
            "disagreements": sorted(
                (r for r in rows if Verdict(r["verdict"]) in SEVERITY),
                key=lambda r: SEVERITY.index(Verdict(r["verdict"])),
            ),
            "fails": [r for r in rows if r["arm"] == "Fail"],
            "efficiency": {
                k: s.get(k)
                for k in (
                    "ended",
                    "wall_s",
                    "tokens",
                    "model_calls",
                    "tool_calls",
                    "models_reported",
                    "route",
                    "model_requested",
                )
            },
        }
        if arm_dir.name.startswith("arm-a"):
            arm["server"] = _server(
                rd,
                arm_dir,
                {u: k for u, k in keys.items() if u not in not_given},
                key_tt,
                cs,
            )
        out["arms"][arm_dir.name] = arm
    (rd / "agent-score.json").write_text(json.dumps(out, indent=1) + "\n")
    (rd / "agent-score.md").write_text(_markdown(out))
    return out


def _server(rd, arm_dir, keys, key_tt, cs) -> dict:
    tools = tool_files(arm_dir)
    per_tt, crit, untested = [], [], []
    for url, (_, ref) in keys.items():
        mine = tools.get(page_key(url))
        if mine is None:
            untested.append(url)
            continue
        sc = score_page(compare(ref, mine))
        per_tt.append(sc)
        side = {t.test_id: t.second for t in sc.comparison.tests}
        for c in cs:
            kv = rollup([key_tt[url].get(t) for t in c["tests"]])
            tv = rollup(
                [side[t].result if side[t].performed else None for t in c["tests"]]
            )
            crit.append(Verdict.NOT_SCORED if kv is None else verdict(kv, tv, True))
    tt_counts = totals(per_tt)
    c_counts = _counts(crit)
    return {
        "pages_tested_by_the_tool": len(per_tt),
        "pages_not_tested": untested,
        "per_tt": {
            "counts": tt_counts,
            "weighted": weighted(tt_counts),
            "rates": rates(tt_counts),
        },
        "per_criterion": {
            "counts": c_counts,
            "weighted": weighted(c_counts),
            "rates": rates(c_counts),
        },
    }


def _markdown(out: dict) -> str:
    lines = [
        f"# Agent eval score: {out['round']}",
        "",
        "Agent-assisted results scored against a tester's SCRT files. Not a "
        "certified Trusted Tester result.",
        "",
        f"Scored {out['scored_at']}; lock commit {out['lock_commit']}; "
        f"{out['pages_with_keys']} of {out['pages']} pages have keys.",
    ]
    for name, a in out["arms"].items():
        eff = a["efficiency"]
        lines += [
            "",
            f"## {name}",
            "",
            f"RESULT line: {a['result_line']}. Ended: {eff['ended']}. Wall time: "
            f"{eff['wall_s']} s. Tokens: {eff['tokens']}. Model calls: "
            f"{eff['model_calls']}. Tool calls: {eff['tool_calls']}.",
            "",
            f"Per WCAG 2.0 criterion (what the agent reported): weighted "
            f"{a['per_criterion']['weighted']}",
            "",
            *[f"- {k}: {v}" for k, v in a["per_criterion"]["rates"].items()],
        ]
        if "server" in a:
            sv = a["server"]
            lines += [
                "",
                f"Tool's own results, per TT test: weighted {sv['per_tt']['weighted']}",
                "",
                *[f"- {k}: {v}" for k, v in sv["per_tt"]["rates"].items()],
                "",
                "Tool's own results rolled up per criterion: weighted "
                f"{sv['per_criterion']['weighted']}",
            ]
        if a["disagreements"]:
            lines += ["", "| Page | Criterion | Key | Arm | Verdict | Elements |"]
            lines += ["| --- | --- | --- | --- | --- | --- |"]
            for r in a["disagreements"]:
                lines.append(
                    f"| {r['page']} | {r['criterion']} | {r['key']} | {r['arm']} | "
                    f"{r['verdict']} | {'; '.join(r['elements'])[:200]} |"
                )
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        sys.exit(__doc__)
    out = score(Path(argv[0]))
    for name, a in out["arms"].items():
        print(
            name,
            "weighted",
            a["per_criterion"]["weighted"],
            a["per_criterion"]["rates"],
        )


if __name__ == "__main__":
    main(sys.argv[1:])
