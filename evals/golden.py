"""Golden reports: the outcome-bearing part of real runs, before and after a
change that must not touch outcomes (agent follow-through plan, change 2b:
the result refactor).

    uv run python evals/golden.py record OUT.json   # before the change
    uv run python evals/golden.py check OUT.json    # after: same, or a diff

Each case runs a fixture page through the real pipeline and keeps, per
test: outcome, rows, summary, note; the open questions (id, question,
rubric, input); and the follow-up calls. Run ids, times and local ports are
normalized. Record twice before a change to learn what varies by itself
(pass T timing); `check` names every difference.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from a11y_assist.checks import REGISTRY  # noqa: E402
from a11y_assist.models import TestId  # noqa: E402
from a11y_assist.pipeline import run_tt_tests  # noqa: E402
from evals.judge_eval import settings  # noqa: E402
from tests.conftest import LocalServer  # noqa: E402

ALL = [t for t in TestId if t in REGISTRY]
# (page, tests, other pages): realistic pages with every test, and pages
# that ask questions, cap a test, or make a follow-up call.
CASES = [
    ("budget/agency-home.html", None, []),
    ("budget/benefits-form.html", None, []),
    ("4a/f01-click-only-text.html", ["4.A"], []),
    ("4c/f06-script-loop.html", ["4.C"], []),
    ("5d/f15-filter-checkboxes-navigate.html", ["5.D"], []),
    (
        "19a/t-benefits.html",
        ["19.A", "9.A", "9.B", "9.C"],
        ["home.html", "contact.html"],
    ),
]

_NOISE = [
    (re.compile(r"\d{8}T\d{6}Z-[0-9a-f]{6}"), "<run>"),
    (re.compile(r"127\.0\.0\.1:\d+"), "127.0.0.1:<port>"),
]


def _clean(v):
    s = json.dumps(v, sort_keys=True)
    for pat, rep in _NOISE:
        s = pat.sub(rep, s)
    return json.loads(s)


async def record() -> dict:
    fix = LocalServer()
    out: dict = {}
    with tempfile.TemporaryDirectory() as tmp:
        s = settings(Path(tmp))
        for page, tests, others in CASES:
            url = f"{fix.base}/{page}"
            folder = page.rsplit("/", 1)[0]
            res = await run_tt_tests(
                s,
                url,
                [TestId(t) for t in tests] if tests else ALL,
                other_pages=[f"{fix.base}/{folder}/{o}" for o in others],
            )
            r = res.report
            out[page] = _clean(
                {
                    "findings": {
                        f.test_id.value: {
                            "outcome": f.outcome.value,
                            "rows": f.rows,
                            "summary": f.summary,
                            "note": f.note,
                        }
                        for f in r.findings
                    },
                    "questions": [
                        {
                            "id": q.question_id,
                            "question": q.question,
                            "rubric": q.rubric,
                            "input": q.input,
                        }
                        for q in r.open_questions
                    ],
                    "follow_up_calls": r.follow_up_calls,
                }
            )
            size = len(res.model_dump_json(exclude={"report"}))
            print(page, f"result {size} chars,", len(r.open_questions), "questions")
    return out


def diff(a: dict, b: dict, path: str = "") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += diff(a.get(k), b.get(k), f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [
            x for i, (p, q) in enumerate(zip(a, b)) for x in diff(p, q, f"{path}[{i}]")
        ]
    return [] if a == b else [f"{path}: {str(a)[:120]!r} -> {str(b)[:120]!r}"]


def main(argv: list[str]) -> None:
    mode, path = argv[0], Path(argv[1])
    now = asyncio.run(record())
    if mode == "record":
        path.write_text(json.dumps(now, indent=1, sort_keys=True))
        print(f"recorded {len(now)} cases in {path}")
        return
    changes = diff(json.loads(path.read_text()), now)
    print("\n".join(changes) or "identical")
    sys.exit(1 if changes else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
