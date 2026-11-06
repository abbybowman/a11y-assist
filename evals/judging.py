"""Judging rounds: the tool's results on real pages scored against a
Trusted Tester's blind SCRT files, by commit and reveal.

    uv run python evals/judging.py scan  evals/judging/<round>   # run every page
    # ... ONE fresh agent answers <round>/packets/pNN/roundK/questions.json
    #     into answers.json in the same folder, seeing only that folder ...
    uv run python evals/judging.py apply evals/judging/<round>   # repeat until done
    uv run python evals/judging.py lock  evals/judging/<round>   # then commit
    # ... the tester adds their SCRT files to <round>/keys/ and commits ...
    uv run python evals/judging.py score evals/judging/<round>

1. Commit: the tester commits <round>/pages.txt when the round starts (not
   before: the page list would let development prepare for those pages).
   One page per line: its URL and the SHA-256 of their SCRT file for it.
2. Scan and apply: each page is run with every implemented test; its open
   questions go to a fresh agent as in the judge eval. A finished page's
   report, pre-SCRT file and HAR go to <round>/results/pNN/.
3. Lock: results/lock.json holds the SHA-256 of pages.txt, of every result
   file and of the comparison code, and the code commit. Commit it before
   any answer key is in the repository; that commit is the lock.
4. Reveal and score: answer keys are matched to pages by hash. A key that
   matches no page, a changed result, a changed pages.txt or changed
   comparison code stops the score. Output: <round>/score.md and score.json.

Scores are recorded per round (evals/README.md) and are not written into
docs/hackathon/evaluation.md until Abby picks the final round.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from evals.scoring import (  # noqa: E402
    SEVERITY,
    Score,
    ScoredTest,
    adjudications,
    rates,
    totals,
)
from evals.scoring import score as score_page  # noqa: E402
from tobi508 import scrt  # noqa: E402
from tobi508.compare import compare, page_key  # noqa: E402

MAX_ROUNDS = 3
# Everything score() reads to decide what counts: a change after the reveal
# (the tests compared, which pages count) must stop the score.
CODE = [
    "evals/judging.py",
    "evals/scoring.py",
    "src/tobi508/compare.py",
    "src/tobi508/scrt.py",
    "src/tobi508/catalog.py",
    "docs/sources/tt-5.1.3/tt.json",
    "third_party/scrt/Resources/SuccessCriteriaTT5.1.3.json",
    # The agent eval's scoring (agent rounds; plan section 8).
    "evals/agent/score.py",
    "evals/agent/prompt.py",
]
_HASH = re.compile(r"^[0-9a-fA-F]{64}$")
_URL = re.compile(r"^https?://\S+$")


class JudgingError(Exception):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_pages(text: str) -> list[tuple[str, str]]:
    """pages.txt: one page per line, a URL and a SHA-256 in any order,
    separated by spaces. Blank lines and # comments are skipped."""
    pages: list[tuple[str, str]] = []
    seen: set[str] = set()
    for n, raw in enumerate(text.splitlines(), 1):
        line = "" if raw.lstrip().startswith("#") else raw.strip()
        if not line:
            continue
        parts = line.split()
        urls = [p for p in parts if _URL.match(p)]
        hashes = [p.lower() for p in parts if _HASH.match(p)]
        if len(parts) != 2 or len(urls) != 1 or len(hashes) != 1:
            raise JudgingError(
                f"pages.txt line {n}: expected one URL and one SHA-256, got {raw!r}"
            )
        if urls[0] in seen:
            raise JudgingError(f"pages.txt line {n}: {urls[0]} is listed twice")
        seen.add(urls[0])
        pages.append((urls[0], hashes[0]))
    if not pages:
        raise JudgingError("pages.txt lists no pages")
    return pages


def other_pages(url: str, listed: list[str]) -> list[str]:
    """The round's other pages on the same host, in list order: 9.A-9.C and
    19.A compare pages of one site, and more pages make them more reliable.
    Scans run with no time limit, so the 5-page cap does not apply (Abby,
    2026-11-03). They come from pages.txt (the caller), never from links on
    a page."""
    from tobi508.pipeline import OTHER_PAGES_NO_LIMIT_MAX, _same_site

    same = [u for u in listed if u != url and _same_site(u, url)]
    if len(same) > OTHER_PAGES_NO_LIMIT_MAX:
        raise JudgingError(
            f"{url}: {len(same)} other pages on its host; one run compares at "
            f"most {OTHER_PAGES_NO_LIMIT_MAX}"
        )
    return same


def _pages(rd: Path) -> list[tuple[str, str]]:
    f = rd / "pages.txt"
    if not f.is_file():
        raise JudgingError(f"No {f}: the tester commits it when the round starts")
    return parse_pages(f.read_text("utf-8"))


def _state(rd: Path) -> dict:
    f = rd / "state.json"
    return json.loads(f.read_text()) if f.exists() else {}


def _save_state(rd: Path, state: dict) -> None:
    (rd / "state.json").write_text(json.dumps(state, indent=1, sort_keys=True) + "\n")


def _finish(rd: Path, settings, pid: str, run_id: str) -> None:
    """Copy a finished page's report, pre-SCRT file and HARs into results/:
    the page's own, and those of its other pages and any live site search
    (9.A-9.C and 19.A were decided on them; runs expire)."""
    run_dir = settings.runs_dir / run_id
    out = rd / "results" / pid
    out.mkdir(parents=True, exist_ok=True)
    for name in ("report.json", "pre-scrt.json", "evidence/page.har.zip"):
        src = run_dir / name
        if src.is_file():
            shutil.copyfile(src, out / Path(name).name)
    hars = sorted((run_dir / "evidence" / "pages").glob("*.har.zip"))
    if hars:
        (out / "pages").mkdir(exist_ok=True)
        for src in hars:
            shutil.copyfile(src, out / "pages" / src.name)


async def scan(rd: Path, settings) -> None:
    from evals.judge_eval import _answer_format, write_packet
    from tobi508.checks import REGISTRY
    from tobi508.models import TestId
    from tobi508.pipeline import run_tt_tests

    if (rd / "results" / "lock.json").exists():
        raise JudgingError("This round is locked")
    fmt = await _answer_format()
    state = _state(rd)
    pages = _pages(rd)
    tests = [t for t in TestId if t in REGISTRY]  # every implemented test
    for n, (url, _) in enumerate(pages, 1):
        pid = f"p{n:02d}"
        if pid in state:
            continue
        others = other_pages(url, [u for u, _ in pages])
        print(f"{pid} {url} (+{len(others)} other pages)", flush=True)
        try:
            # No time limit: a round wants every test's full result (Abby,
            # 2026-11-02).
            res = await run_tt_tests(
                settings, url, tests, no_time_limit=True, other_pages=others
            )
        except Exception as exc:  # a page that cannot be tested: record why
            state[pid] = {"url": url, "status": "error", "error": str(exc)[:300]}
            _save_state(rd, state)
            continue
        state[pid] = {
            "url": url,
            "other_pages": others,
            "run_id": res.run_id,
            "round": 1,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }
        if res.open_questions:
            d = rd / "packets" / pid / "round1"
            write_packet(
                d,
                settings.runs_dir / res.run_id,
                res.run_id,
                res.open_questions,
                res,
                fmt,
            )
            state[pid]["status"] = "open"
        else:
            _finish(rd, settings, pid, res.run_id)
            state[pid]["status"] = "done"
        _save_state(rd, state)
    _report_status(state)


async def apply(rd: Path, settings) -> None:
    from evals.judge_eval import _answer_format, write_packet
    from tobi508.models import Answer
    from tobi508.pipeline import answer_questions

    fmt = await _answer_format()
    state = _state(rd)
    for pid, p in sorted(state.items()):
        if p.get("status") != "open":
            continue
        f = rd / "packets" / pid / f"round{p['round']}" / "answers.json"
        if not f.exists():
            print(f"{pid}: no answers yet")
            continue
        try:
            answers = [Answer.model_validate(a) for a in json.loads(f.read_text())]
            res = await answer_questions(settings, p["run_id"], answers)
        except Exception as exc:  # fix the file and rerun: other pages go on
            p["error"] = str(exc)[:300]
            print(f"{pid}: {p['error']}")
            _save_state(rd, state)
            continue
        p.pop("error", None)
        p.setdefault("rejected", []).extend(str(r) for r in res.rejected)
        if res.open_questions and not res.rejected and p["round"] < MAX_ROUNDS:
            p["round"] += 1
            d = rd / "packets" / pid / f"round{p['round']}"
            write_packet(
                d,
                settings.runs_dir / p["run_id"],
                p["run_id"],
                res.open_questions,
                res,
                fmt,
            )
        else:
            p["still_open"] = [q.question_id for q in res.open_questions]
            _finish(rd, settings, pid, p["run_id"])
            p["status"] = "done"
        # Saved per page: answers are recorded in the run as they are applied,
        # so a rerun must not apply them again or rewrite the next packet.
        _save_state(rd, state)
    _report_status(state)


def _report_status(state: dict) -> None:
    by: dict[str, list[str]] = {}
    for pid, p in sorted(state.items()):
        by.setdefault(p.get("status", "?"), []).append(pid)
    print(" ".join(f"{k}: {' '.join(v)}" for k, v in sorted(by.items())))


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _result_files(rd: Path) -> dict[str, str]:
    """results/ and, for an agent round, the frozen pages both arms used."""
    files = [*sorted((rd / "results").rglob("*")), *sorted((rd / "frozen").rglob("*"))]
    return {
        p.relative_to(rd).as_posix(): sha256(p)
        for p in files
        if p.is_file() and p.name != "lock.json"
    }


def _ignored(rd: Path, names: list[str]) -> set[str]:
    """The names (relative to rd) git ignores: recordings and screenshots kept
    in an archive, not in the repository (post-round 1 fix 20). Outside a git
    repository, none."""
    if not names:
        return set()
    try:
        got = subprocess.run(
            ["git", "check-ignore", "--stdin", "-z"],
            cwd=rd,
            input="\0".join(names) + "\0",
            capture_output=True,
            text=True,
        )
    except OSError:
        return set()
    if got.returncode not in (0, 1):  # 1: none ignored; 128: not a repository
        return set()
    return {x for x in got.stdout.split("\0") if x}


def _split(rd: Path) -> tuple[dict[str, str], dict[str, str]]:
    """(files git keeps, files git ignores), each name -> SHA-256."""
    allf = _result_files(rd)
    ign = _ignored(rd, list(allf))
    return (
        {k: v for k, v in allf.items() if k not in ign},
        {k: v for k, v in allf.items() if k in ign},
    )


def lock(rd: Path) -> Path:
    state = _state(rd)
    pages = _pages(rd)
    arms = sorted(p for p in (rd / "results").glob("arm-*") if p.is_dir())
    if state or not arms:  # a scanned round: every page finished
        open_ = [pid for pid, p in state.items() if p.get("status") == "open"]
        if len(state) != len(pages) or open_:
            raise JudgingError(f"Not every page is finished (open: {open_})")
    unfinished = [a.name for a in arms if not (a / "summary.json").is_file()]
    if unfinished:
        raise JudgingError(f"Arms that have not finished: {unfinished}")
    keys = rd / "keys"
    if keys.exists() and any(keys.iterdir()):
        raise JudgingError("Answer keys are already here: lock before the reveal")
    out = rd / "results" / "lock.json"
    if out.exists():
        raise JudgingError("Already locked")
    data = {
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "code_commit": _git_commit(),
        "pages_txt": sha256(rd / "pages.txt"),
        "code": {c: sha256(REPO / c) for c in CODE},
    }
    # Files git keeps must match on any clone; files it ignores (an
    # archive's recordings) are checked wherever they are present.
    data["files"], data["ignored"] = _split(rd)
    out.write_text(json.dumps(data, indent=1) + "\n")
    print(
        f"Locked {len(data['files'])} files and {len(data['ignored'])} the "
        f"repository ignores. Commit {out} before any answer key."
    )
    return out


def _verify(rd: Path) -> dict:
    f = rd / "results" / "lock.json"
    if not f.is_file():
        raise JudgingError("Not locked: run lock and commit it before the reveal")
    lk = json.loads(f.read_text())
    if sha256(rd / "pages.txt") != lk["pages_txt"]:
        raise JudgingError("pages.txt changed after the lock")
    if "ignored" not in lk:  # locked before fix 20: every file, as then
        if _result_files(rd) != lk["files"]:
            raise JudgingError("Result files changed after the lock")
    else:
        kept, ignored = _split(rd)
        if kept != lk["files"]:
            raise JudgingError("Result files changed after the lock")
        bad = [k for k, h in ignored.items() if lk["ignored"].get(k) != h]
        if bad:
            raise JudgingError(
                f"Archived files that differ from the lock: {bad[:5]}"
                + (f" and {len(bad) - 5} more" if len(bad) > 5 else "")
            )
    # A file that moved since the lock (the package rename, 2026-11-06)
    # counts as changed: score with the code at the lock commit.
    changed = [
        c
        for c, h in lk["code"].items()
        if not (REPO / c).is_file() or sha256(REPO / c) != h
    ]
    if changed:
        raise JudgingError(
            f"Comparison code changed since the lock ({', '.join(changed)}): "
            f"score with the code at commit {lk['code_commit']}"
        )
    return lk


def read_keys(rd: Path, pages: list[tuple[str, str]]) -> dict[str, tuple[Path, object]]:
    """The tester's SCRT files by page URL, matched by hash. Stops on a key
    that matches no page, or one whose page (P_Location) is another page."""
    keys = {sha256(p): p for p in sorted((rd / "keys").glob("*")) if p.is_file()}
    by_hash = {h: url for url, h in pages}
    stray = [p.name for h, p in keys.items() if h not in by_hash]
    if stray:
        raise JudgingError(f"Answer keys that match no page's hash: {stray}")
    out = {}
    for n, (url, h) in enumerate(pages, 1):
        key = keys.get(h)
        if key is None:
            continue
        ref = scrt.parse(key.read_text("utf-8"))
        # Keys pair with pages by hash only, so a hash pasted on the wrong
        # line would score one page against another page's answers.
        named = page_key(ref.Product.P_Location)
        if named is not None and named != page_key(url):
            raise JudgingError(
                f"p{n:02d}: the answer key {key.name} names "
                f"{ref.Product.P_Location}, not {url}: check the hash on that "
                "line of pages.txt"
            )
        out[url] = (key, ref)
    return out


def score(rd: Path) -> dict:
    lk = _verify(rd)
    pages = _pages(rd)
    state = _state(rd)
    keys = read_keys(rd, pages)
    comparisons: list[tuple[str, str, Score | None, str]] = []
    for n, (url, h) in enumerate(pages, 1):
        pid = f"p{n:02d}"
        key, ref = keys.get(url, (None, None))
        cand = rd / "results" / pid / "pre-scrt.json"
        if key is None or not cand.is_file():
            why = (
                "no answer key"
                if key is None
                else state.get(pid, {}).get("error", "no result")
            )
            comparisons.append((pid, url, None, why))
            continue
        c = score_page(
            compare(ref, scrt.parse(cand.read_text("utf-8"))),
            adjudications(rd).get(page_key(url)),
        )
        comparisons.append((pid, url, c, ""))
    done = [c for _, _, c, _ in comparisons if c]
    tot = totals(done)
    # A skipped page leaves the rates silently otherwise: "no false PASS" on
    # a round that lost a host's pages would read as a clean result.
    skipped = [f"{pid} ({why})" for pid, _, c, why in comparisons if c is None]
    out = {
        "round": rd.name,
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "lock_commit": lk["code_commit"],
        "rates": {
            "pages scored": f"{len(done)} of {len(comparisons)}",
            "pages not scored": "; ".join(skipped) or "none",
            **rates(tot),
        },
        "counts": tot,
        "pages": [
            {
                "page": pid,
                "url": url,
                "scanned_at": state.get(pid, {}).get("scanned_at"),
                "skipped": why or None,
                "counts": c.counts if c else None,
                "same_page": c.comparison.same_page if c else None,
                "disagreements": [_flat(t) for t in c.disagreements()] if c else [],
            }
            for pid, url, c, why in comparisons
        ],
    }
    (rd / "score.json").write_text(json.dumps(out, indent=1) + "\n")
    (rd / "score.md").write_text(_markdown(out, comparisons, done))
    print("\n".join(f"{k}: {v}" for k, v in out["rates"].items()))
    return out


def _flat(t: ScoredTest) -> dict:
    """One disagreement: the key's answer, the tool's and its audit trail."""
    tool = t.test.second.source
    return {
        "test_id": t.test.test_id,
        "test_name": t.test.test_name,
        "verdict": t.verdict.value,
        "key": t.test.first.result.value if t.test.first.result else None,
        "tool": t.test.second.result.value if t.test.second.result else None,
        "tool_outcome": tool.outcome if tool else None,
        "spec_version": tool.spec_version if tool else None,
        "rows": tool.rows if tool else [],
    }


def _markdown(out: dict, comparisons, done: list[Score]) -> str:
    lines = [
        f"# Judging {out['round']}: score",
        "",
        f"Scored {out['scored_at'][:10]} against the results locked at commit "
        f"`{out['lock_commit'][:12]}`. Agent-assisted results, not a certified "
        "Trusted Tester result.",
        "",
        "| Measure | Value |",
        "| --- | --- |",
        *[f"| {k} | {v} |" for k, v in out["rates"].items()],
        "",
        "## Per test",
        "",
        "| Test | Agree | False PASS | Missed fail | False FAIL | Other "
        "| Needs review |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    per: dict[str, dict[str, int]] = {}
    for c in done:
        for t in c.tests:
            row = per.setdefault(t.test.test_id, {})
            row[t.verdict.value] = row.get(t.verdict.value, 0) + 1
    for tid, r in per.items():
        if not set(r) - {"not_scored", "not_performed"}:
            continue
        other = r.get("fail_vs_dna", 0) + r.get("other_mismatch", 0)
        lines.append(
            f"| {tid} | {r.get('agree', 0)} | {r.get('false_pass', 0)} | "
            f"{r.get('missed_fail', 0)} | {r.get('false_fail', 0)} | {other} | "
            f"{r.get('needs_review', 0)} |"
        )
    lines += ["", "## Pages", ""]
    for pid, url, c, why in comparisons:
        page = next(p for p in out["pages"] if p["page"] == pid)
        lines.append(f"### {pid} {url}")
        lines.append("")
        lines.append(f"Scanned {page['scanned_at'] or 'n/a'}.")
        if c is None:
            lines += [f"Not scored: {why}.", ""]
            continue
        if page_key(c.comparison.first_page) is None:
            lines.append(
                "The answer key names no page; it was matched to this page by "
                "its hash only."
            )
        bad = c.disagreements()
        if not bad:
            lines += ["No disagreements.", ""]
            continue
        lines.append("")
        lines.append("| Test | Verdict | Tester | Tool | Tool outcome | Spec | Rows |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for d in map(_flat, bad):
            lines.append(
                f"| {d['test_id']} | {d['verdict']} | {d['key'] or ''} | "
                f"{d['tool'] or ''} | {d['tool_outcome'] or ''} | "
                f"{d['spec_version'] or ''} | {' '.join(d['rows'])} |"
            )
        lines.append("")
    lines.append("Verdicts, worst first: " + ", ".join(v.value for v in SEVERITY) + ".")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> None:
    if len(argv) != 3 or argv[1] not in ("scan", "apply", "lock", "score"):
        raise SystemExit(__doc__)
    cmd, rd = argv[1], Path(argv[2]).resolve()
    try:
        if cmd in ("scan", "apply"):
            from tobi508.config import Settings

            settings = Settings()  # .env / environment: the real allowlist
            asyncio.run((scan if cmd == "scan" else apply)(rd, settings))
        elif cmd == "lock":
            lock(rd)
        else:
            score(rd)
    except JudgingError as exc:
        raise SystemExit(f"judging: {exc}") from None


if __name__ == "__main__":
    main(sys.argv)
