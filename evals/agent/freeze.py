"""Freeze a round's pages once, for both arms of the agent eval
(docs/plans/2026-10-31-agent-eval.md section 6).

    uv run python -m evals.agent.freeze evals/judging/<round>

Every page in <round>/pages.txt is run once with 19.A only, its other
pages being the round's other pages on its host, with the server's frozen
pages folder set to <round>/frozen/ in "record_missing" mode. That records
each page, each other page and 19.A's one live site search (where it runs)
exactly as a live run would, under the same allowlist and redirect checks.
The runs' own results are deleted unread: they are not an arm's results.
Afterwards both arms replay <round>/frozen/ only.

This is the only step that touches the live site. Run it headless:
BROWSER_CHANNEL=chromium HEADLESS=true.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from a11y_assist.config import Settings
from a11y_assist.frozen import load
from a11y_assist.models import TestId
from a11y_assist.pipeline import run_tt_tests
from evals.judging import JudgingError, _pages, other_pages

FROZEN = "frozen"


async def freeze(rd: Path, settings: Settings) -> dict:
    if (rd / "results" / "lock.json").exists():
        raise JudgingError("This round is locked")
    s = settings.model_copy(
        update={
            "frozen_pages_dir": rd / FROZEN,
            "frozen_pages_mode": "record_missing",
        }
    )
    pages = [u for u, _ in _pages(rd)]
    log: dict = {"started_at": datetime.now(timezone.utc).isoformat(), "pages": {}}
    for url in pages:
        t0 = time.monotonic()
        entry: dict = {"other_pages": other_pages(url, pages)}
        print(f"freezing {url} (+{len(entry['other_pages'])} other pages)", flush=True)
        try:
            res = await run_tt_tests(
                s,
                url,
                [TestId.T19A],
                no_time_limit=True,
                other_pages=entry["other_pages"],
            )
            shutil.rmtree(s.runs_dir / res.run_id, ignore_errors=True)
            entry["status"] = "frozen"
        except Exception as exc:  # recorded: an arm will be refused this page
            entry["status"] = "error"
            entry["error"] = str(exc)[:300]
        entry["seconds"] = round(time.monotonic() - t0, 1)
        log["pages"][url] = entry
    log["finished_at"] = datetime.now(timezone.utc).isoformat()
    log["recordings"] = len(load(rd / FROZEN))
    (rd / FROZEN).mkdir(parents=True, exist_ok=True)
    (rd / FROZEN / "freeze.json").write_text(json.dumps(log, indent=1) + "\n")
    return log


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        sys.exit(__doc__)
    log = asyncio.run(freeze(Path(argv[0]), Settings()))
    bad = [u for u, e in log["pages"].items() if e["status"] != "frozen"]
    print(f"{log['recordings']} recordings; pages not frozen: {bad or 'none'}")


if __name__ == "__main__":
    main(sys.argv[1:])
