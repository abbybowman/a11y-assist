"""Judge eval: real agents answer the open questions, not scripted answers.

    uv run python evals/judge_eval.py prepare OUT [TESTS]   # TESTS e.g. "5.F,5.G"
    # ... an agent answers OUT/packets/<case>/round<N>/questions.json into
    #     answers.json in the same folder, seeing only that folder ...
    uv run python evals/judge_eval.py apply OUT      # answer, then next round or score

`prepare` runs each fixture through the real pipeline and writes, per case, a
packet holding only what a consumer agent receives: the open questions (with
rubric and input), the evidence files they point to (run:// resources copied
as local files), the page text, and the answer_questions field description.
Expected outcomes never enter a packet; they stay in OUT/state.json (not for
the answering agent).

`apply` sends each case's answers.json through answer_questions. A follow-up
question (4.B J2) becomes the next round's packet; otherwise the final
outcome is scored against the expected one. Results: OUT/results.json.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from a11y_assist.config import Settings  # noqa: E402
from a11y_assist.models import Answer, TestId  # noqa: E402
from a11y_assist.pipeline import answer_questions, run_tt_tests  # noqa: E402
from tests import (  # noqa: E402
    test_fixtures_4a,
    test_fixtures_4b,
    test_fixtures_4c,
    test_fixtures_4e,
    test_fixtures_4f,
    test_fixtures_5a,
    test_fixtures_5d,
    test_fixtures_5f,
    test_fixtures_9a,
    test_fixtures_9x,
)
from tests.conftest import (  # noqa: E402
    ACT_ROOT,
    BASELINE_ROOT,
    LocalServer,
    _ActHandler,
    _BaselineHandler,
)
from tests.drafts import DRAFTS  # noqa: E402

PARALLEL = 4


def settings(out: Path) -> Settings:
    return Settings(
        _env_file=None,
        allowed_domains=["127.0.0.1"],
        dev_mode=True,
        browser_channel="chromium",
        headless=True,
        browser_args=[
            "--disable-features=LocalNetworkAccessChecks",
            "--host-resolver-rules=MAP cdnjs.cloudflare.com ~NOTFOUND",
        ],
        runs_dir=out / "runs",
        run_ttl_hours=48,
        # The fixture servers listen on 127.0.0.1; the egress proxy refuses
        # local addresses unless listed (as in tests/conftest.py). Without
        # this, recording hangs (docs/solutions/egress-proxy.md).
        dev_allowed_addresses=["127.0.0.1/32"],
    )


def cases() -> list[dict]:
    """Every fixture with an expected outcome, by test. Pages that ask no
    question are dropped after `prepare` runs them."""
    out = []
    for mod, tt, folder in (
        (test_fixtures_4a, "4.A", "4a"),
        (test_fixtures_4b, "4.B", "4b"),
        (test_fixtures_4c, "4.C", "4c"),
        (test_fixtures_4e, "4.E", "4e"),
        (test_fixtures_4f, "4.F", "4f"),
        (test_fixtures_5d, "5.D", "5d"),
    ):
        for name, e in mod.EXPECTED.items():
            if e.get("slow"):
                continue
            out.append(
                {
                    "case": f"{tt}-{name}",
                    "tt": tt,
                    "root": "fix",
                    "path": f"{folder}/{name}.html",
                    "expected": e["outcome"],
                }
            )
    # 5.F/5.G and 5.A/5.C share fixtures: EXPECTED is page -> test ->
    # expectation, with an optional "with": tests that must run alongside
    # (4.F's pass R reveals 5.A/5.C's f12 field).
    for mod, folder in ((test_fixtures_5f, "5f"), (test_fixtures_5a, "5a")):
        for name, by_test in mod.EXPECTED.items():
            for tt, e in by_test.items():
                if tt == "with":
                    continue
                out.append(
                    {
                        "case": f"{tt}-{name}",
                        "tt": tt,
                        "root": "fix",
                        "path": f"{folder}/{name}.html",
                        "expected": e["outcome"],
                        "with": by_test.get("with", []),
                    }
                )
    # 9.x: a tested page plus the other pages it is compared with.
    for name, (page, others, want, _answers) in test_fixtures_9x.EXPECTED.items():
        if name in test_fixtures_9x.NOT_EVAL:
            continue
        for tt, exp in want.items():
            out.append(
                {
                    "case": f"{tt}-{name}",
                    "tt": tt,
                    "root": "fix",
                    "path": f"9x/{page}.html",
                    "pages": [f"9x/{o}.html" for o in others],
                    "expected": exp,
                }
            )
    act = json.loads((ACT_ROOT / "manifest.json").read_text())["cases"]
    for c in act:
        if c["tt_test"] == "9.A":
            out.append(
                {
                    "case": f"9.A-act-{c['id']}",
                    "tt": "9.A",
                    "root": "act",
                    "path": c["path"],
                    "pages": [test_fixtures_9a.CH2],
                    "expected": c["expected"],
                }
            )
        if c["tt_test"] in ("4.A", "4.C"):
            out.append(
                {
                    "case": f"{c['tt_test']}-act-{c['id']}",
                    "tt": c["tt_test"],
                    "root": "act",
                    "path": c["path"],
                    "expected": c["expected"],
                }
            )
    base = json.loads((BASELINE_ROOT / "manifest.json").read_text())["cases"]
    for c in base:
        for tt, exp in c["expected"].items():
            out.append(
                {
                    "case": f"{tt}-baseline-{c['id']}",
                    "tt": tt,
                    "root": "base",
                    "path": c["path"],
                    "expected": exp,
                }
            )
    return out


def packets(out: Path) -> Path:
    """Packets live beside OUT, never inside it: OUT holds the answer key."""
    return out.with_name(out.name + "-packets")


def _serve(handler):
    import http.server
    import threading

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{httpd.server_address[1]}"


async def _answer_format() -> str:
    """The a11y_answer_questions description and answers schema, as a client
    sees."""
    from fastmcp import Client

    from a11y_assist.app import mcp

    async with Client(mcp) as c:
        tools = {t.name: t for t in await c.list_tools()}
    a = tools["a11y_answer_questions"]
    return (
        (a.description or "")
        + "\n\nanswers: "
        + json.dumps(a.inputSchema["properties"]["answers"], indent=1)
    )


def _write_packet(out: Path, case: dict, run_id: str, rnd: int, res) -> None:
    """Only what a consumer agent receives; evidence copied as local files."""
    # Neutral folder names: case names describe the expected answer.
    d = packets(out) / case["packet"] / f"round{rnd}"
    if d.exists():
        shutil.rmtree(d)
    (d / "evidence").mkdir(parents=True)
    run_dir = out / "runs" / run_id
    prefix = f"run://{run_id}/"

    def local(uri: str) -> str:
        rel = uri[len(prefix) :] if uri.startswith(prefix) else uri
        src = run_dir / rel
        if not src.is_file():
            return uri
        dst = d / "evidence" / rel.replace("/", "__")
        shutil.copyfile(src, dst)
        return f"evidence/{dst.name}"

    def rewrite(v):
        if isinstance(v, str) and v.startswith(prefix):
            return local(v)
        if isinstance(v, list):
            return [rewrite(x) for x in v]
        if isinstance(v, dict):
            return {k: rewrite(x) for k, x in v.items()}
        return v

    qs = [
        rewrite(q.model_dump(mode="json"))
        for q in res.open_questions
        if q.test_id.value == case["tt"]
    ]
    (d / "questions.json").write_text(
        json.dumps(
            {
                "about": "Open questions from an accessibility test run. Answer "
                "each one by its rubric, using only the files in this folder.",
                "questions": qs,
                "page_text": res.page_text,
                "shared_inputs": rewrite(res.shared_inputs),
                "answer_format": _ANSWER_FORMAT,
                "write_answers_to": "answers.json (a JSON list of answer objects)",
            },
            indent=1,
        )
    )
    scrub(d)


_ANSWER_FORMAT = ""
_URL = re.compile(r"http://(?:127\.0\.0\.1|localhost):\d+(/[^\s\"'#?]*)")


def scrub(folder: Path) -> None:
    """Fixture file names describe the expected answer ("key-in-comment-only"),
    so every local URL becomes a neutral /site/pageN.html (fragments kept)."""
    names: dict[str, str] = {}

    def neutral(m: re.Match) -> str:
        path = m.group(1)
        if path not in names:
            names[path] = "/" if path == "/" else f"/site/page{len(names) + 1}.html"
        return "https://example.gov" + names[path]

    for f in sorted(folder.rglob("*.json")):
        f.write_text(_URL.sub(neutral, f.read_text()))


async def prepare(out: Path, only: set[str] | None = None) -> None:
    global _ANSWER_FORMAT
    _ANSWER_FORMAT = await _answer_format()
    s = settings(out)
    fix = LocalServer()
    roots = {
        "fix": fix.base,
        "act": _serve(_ActHandler),
        "base": _serve(_BaselineHandler),
    }
    state: dict = {}
    sem = asyncio.Semaphore(PARALLEL)

    all_cases = [c for c in cases() if not only or c["tt"] in only]
    # Shuffled neutral packet IDs, so neither the name nor the order hints at
    # the case.
    ids = random.Random(0).sample(range(1, len(all_cases) + 1), len(all_cases))
    for c, n in zip(all_cases, ids, strict=True):
        c["packet"] = f"q{n:02d}"

    async def one(c: dict) -> None:
        async with sem:
            res = await run_tt_tests(
                s,
                f"{roots[c['root']]}/{c['path']}",
                [TestId(t) for t in c.get("with", [])] + [TestId(c["tt"])],
                other_pages=[f"{roots[c['root']]}/{p}" for p in c.get("pages", [])],
            )
        if [q for q in res.open_questions if q.test_id.value == c["tt"]]:
            _write_packet(out, c, res.run_id, 1, res)
            state[c["case"]] = {**c, "run_id": res.run_id, "round": 1, "status": "open"}

    await asyncio.gather(*(one(c) for c in all_cases))
    (out / "state.json").write_text(json.dumps(state, indent=1, sort_keys=True))
    print(f"{len(state)} cases ask questions; packets in {packets(out)}")
    print(" ".join(sorted(c["packet"] for c in state.values())))


async def apply(out: Path) -> None:
    global _ANSWER_FORMAT
    _ANSWER_FORMAT = await _answer_format()
    s = settings(out)
    state = json.loads((out / "state.json").read_text())
    results = (
        json.loads((out / "results.json").read_text())
        if (out / "results.json").exists()
        else {}
    )
    for name, c in sorted(state.items()):
        if c["status"] != "open":
            continue
        d = packets(out) / c["packet"] / f"round{c['round']}"
        f = d / "answers.json"
        if not f.exists():
            print(f"{name}: no answers yet")
            continue
        try:
            answers = [Answer.model_validate(a) for a in json.loads(f.read_text())]
        except Exception as exc:
            c["status"] = "bad_answers"
            results[name] = {"error": repr(exc)[:300]}
            continue
        res = await answer_questions(s, c["run_id"], answers)
        rejected = [
            r.model_dump(mode="json") if hasattr(r, "model_dump") else r
            for r in res.rejected
        ]
        own = [q for q in res.open_questions if q.test_id.value == c["tt"]]
        if own and not rejected and c["round"] < 3:
            c["round"] += 1
            _write_packet(out, c, c["run_id"], c["round"], res)
            continue
        [fd] = [x for x in res.report.findings if x.test_id.value == c["tt"]]
        c["status"] = "done"
        results[name] = {
            "tt": c["tt"],
            "expected": c["expected"],
            "got": fd.outcome.value,
            "match": fd.outcome.value == c["expected"],
            "rows": fd.rows,
            "rejected": rejected,
            "still_open": [q.question_id for q in own],
            "answers": [
                {
                    "q": r.answer.question_id,
                    "choice": (
                        r.answer.choice.model_dump(exclude_none=True)
                        if r.answer.choice
                        else None
                    ),
                    "j1": r.answer.j1.model_dump() if r.answer.j1 else None,
                    "j2": r.answer.j2.model_dump() if r.answer.j2 else None,
                    "rationale": r.answer.rationale,
                }
                for r in res.report.answers
            ],
        }
    (out / "state.json").write_text(json.dumps(state, indent=1, sort_keys=True))
    (out / "results.json").write_text(json.dumps(results, indent=1, sort_keys=True))
    done = [r for r in results.values() if "match" in r]
    print(
        f"scored {len(done)}: {sum(r['match'] for r in done)} match; "
        f"open: {[n for n, c in state.items() if c['status'] == 'open']}"
    )


if __name__ == "__main__":
    # Checks whose spec is still a draft are evaluated too (tests/drafts.py).
    from a11y_assist.checks import REGISTRY

    REGISTRY.update(DRAFTS)
    # prepare OUT [TESTS]: TESTS (e.g. "5.F,5.G") limits the run to the
    # tests whose questions or inputs changed.
    cmd, out = sys.argv[1], Path(sys.argv[2]).resolve()
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    out.mkdir(parents=True, exist_ok=True)
    os.chdir(REPO)
    if cmd == "prepare":
        asyncio.run(prepare(out, only))
    else:
        asyncio.run(apply(out))
