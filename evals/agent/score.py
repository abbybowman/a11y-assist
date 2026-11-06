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
    adjudications,
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
    """Agent A's tool runs, one file per page: each TT test from the latest
    finished run of that page whose `tests` included it (post-round 1 fix
    13: an agent that splits a page over several calls keeps every test's
    latest result, not only the last call's tests)."""
    runs: dict[str, list[tuple[str, list[str], scrt.PreScrt]]] = {}
    for rep in (arm_dir / "runs").glob("*/report.json"):
        r = json.loads(rep.read_text("utf-8"))
        pre = rep.parent / "pre-scrt.json"
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
    out: dict[str, scrt.PreScrt] = {}
    for k, rs in runs.items():
        rs.sort(key=lambda x: x[0])
        base = rs[-1][2].model_copy(deep=True)
        chosen: dict[str, list] = {}
        for _, tests, pre in rs:  # oldest first: later runs replace
            rows = pre.results()
            for t in tests:
                if t in rows:
                    chosen[t] = rows[t]
        merged = []
        for t, rows in base.results().items():
            merged += chosen.get(t, rows)
        base.Criteria = merged
        out[k] = base
    return out


def _window_change(w: dict | None) -> dict[str, float] | None:
    """How much of each subscription usage window a run used (last minus
    first utilization; post-round 1 fix 8: on a subscription the limit is
    the usage meter, not dollars). None when the route reports none."""

    def util(snaps) -> dict[str, float]:
        for snap in snaps or []:
            win = (snap or {}).get("unifiedWindows") or {}
            return {k: v.get("utilization") for k, v in win.items() if v}
        return {}

    if not w:
        return None
    a, b = util(w.get("first")), util(w.get("last"))
    out = {
        k: round(b[k] - a[k], 3)
        for k in a
        if isinstance(a.get(k), (int, float)) and isinstance(b.get(k), (int, float))
    }
    return out or None


def review_reason(comment: str | None) -> str:
    """Why the tool left a test for review, from its plain-language comment
    (post-round 1 fix 13: every NEEDS_REVIEW carries the "could not be
    performed" note, so the note alone cannot tell these apart)."""
    c = (comment or "").lower()
    if "not finished yet" in c and "question" in c:
        return "open question"
    if "time limit" in c:
        return "time limit"
    return "could not be performed"


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
        # A page whose frozen copy was broken for this run, recorded before
        # the lock with the reason (results/<arm>/not_scored.json).
        ns = arm_dir / "not_scored.json"
        excluded = json.loads(ns.read_text()) if ns.is_file() else {}
        given -= {page_key(u) for u in excluded.get("pages", [])}
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
            "not_scored_reason": excluded.get("reason"),
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
                    "cost_usd_list_price",
                )
            }
            | {"usage_window_change": _window_change(s.get("usage_windows"))},
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
    adjudicated = adjudications(rd)
    per_tt, crit, untested = [], [], []
    reasons: dict[str, int] = {}
    for url, (_, ref) in keys.items():
        mine = tools.get(page_key(url))
        if mine is None:
            untested.append(url)
            continue
        sc = score_page(compare(ref, mine), adjudicated.get(page_key(url)))
        per_tt.append(sc)
        for t in sc.comparison.tests:
            if t.second.rows and t.second.result is None:
                r = review_reason(t.second.comment)
                reasons[r] = reasons.get(r, 0) + 1
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
        "needs_review_reasons": reasons,
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


def _tokens(t: dict | None) -> str:
    if not t:
        return "not reported"
    names = {
        "input_tokens": "input",
        "cache_creation_input_tokens": "cache writes",
        "cache_read_input_tokens": "cache reads",
        "output_tokens": "output",
    }
    return ", ".join(f"{names.get(k, k)} {v:,}" for k, v in t.items())


def _usd(v) -> str:
    return f"${v:.2f}" if isinstance(v, (int, float)) else "not reported"


def _windows(w: dict | None) -> str:
    if not w:
        return "not reported"
    return ", ".join(f"{k.replace('_', ' ')} +{v * 100:.0f}%" for k, v in w.items())


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
            f"{eff['wall_s']} s (the efficiency figure: call durations include "
            "waits). Model calls: "
            f"{eff['model_calls']}. Tool calls: {eff['tool_calls']}.",
            "",
            f"Tokens by type: {_tokens(eff.get('tokens'))}. Cost at list price: "
            f"{_usd(eff.get('cost_usd_list_price'))}. Usage window change: "
            f"{_windows(eff.get('usage_window_change'))}.",
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
                "Why the tool left tests for review: "
                + (
                    ", ".join(
                        f"{k} {v}"
                        for k, v in sorted(sv.get("needs_review_reasons", {}).items())
                    )
                    or "none"
                ),
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
