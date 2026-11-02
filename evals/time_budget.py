"""Where a run's time goes: run a11y_run_tt_tests (every implemented test, as
the tool's default) on local fixture pages and print each phase's cost from
the run's steps.jsonl (record, walk, each check's collect: seconds, page loads,
key presses). Measurement only; it decides nothing.

    uv run python evals/time_budget.py 4d/f10-100-links.html budget/agency-home.html
    uv run python evals/time_budget.py --no-time-limit 4c/f34-600-links.html

--drafts also runs the checks whose spec is still a draft (tests/drafts.py).
--limit sets RUN_LIMIT_S for the run (default 120, the tool's own);
--no-time-limit runs as the tool's no_time_limit does (what an uncapped run
costs); --other PAGE (repeatable) compares each page with other pages of the
same fixture site, as other_pages does (9.A-9.C; the limit grows per page).
--json prints one JSON object per page instead of the table (total and each
phase's seconds, and each test's outcome), for timing changes one at a time;
--keep DIR keeps the run folders there (to read a check's evidence after).
"quick" counts replay-prefix presses without the quiet window,
"redos" replays redone fully settled. Paths are under tests/fixtures/.
Offline, like the tests: only 127.0.0.1 resolves.
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import http.server
import ipaddress
import json
import sys
import tempfile
import threading
import time
from pathlib import Path

from a11y_assist import egress
from a11y_assist.checks import REGISTRY
from a11y_assist.config import Settings
from a11y_assist.pipeline import RunRefused, run_tt_tests

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


async def _offline(host: str, port: int) -> list[str]:
    if host == "localhost":
        return ["127.0.0.1"]
    try:
        return [str(ipaddress.ip_address(host))]
    except ValueError:
        raise OSError(f"offline: {host} not resolved") from None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass


def _serve() -> str:
    handler = functools.partial(_Quiet, directory=str(FIXTURES))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{httpd.server_address[1]}"


def costs(steps_path: Path) -> list[tuple]:
    """(phase, seconds, loads, presses, quick, slow redos) per phase, from
    steps.jsonl."""
    out = []
    for line in steps_path.read_text("utf-8").splitlines():
        e = json.loads(line)
        d = e["detail"]
        if e["step"] == "captured":
            out.append(("record", d.get("seconds", 0.0), 1, 0, 0, 0))
        elif e["step"] == "captured_other":
            out.append((f"record p{d['n']}", d.get("seconds", 0.0), 1, 0, 0, 0))
        elif e["step"] == "walk":
            c = d["cost"]
            out.append(("walk", *_cost(c)))
        elif e["step"] == "collected":
            c = d["cost"]
            out.append((d["test"], *_cost(c)))
    return out


def _cost(c: dict) -> tuple:
    keys = ("seconds", "loads", "presses", "quick", "slow_redos")
    return tuple(c.get(k, 0) for k in keys)


async def measure(
    base: str,
    page: str,
    limit: int,
    runs: Path,
    no_limit: bool = False,
    others: list[str] | None = None,
    as_json: bool = False,
) -> None:
    settings = Settings(
        _env_file=None,
        allowed_domains=["127.0.0.1"],
        dev_mode=True,
        browser_channel="chromium",  # as the tests: Playwright's, headless
        headless=True,
        browser_args=["--disable-features=LocalNetworkAccessChecks"],
        runs_dir=runs,
        dev_allowed_addresses=["127.0.0.1/32"],
        run_limit_s=limit,
    )
    t0 = time.monotonic()
    try:
        out = await run_tt_tests(
            settings,
            f"{base}/{page}",
            list(REGISTRY),
            no_time_limit=no_limit,
            other_pages=[f"{base}/{o}" for o in others or []],
        )
    except RunRefused as exc:
        print(f"\n{page}  refused after {time.monotonic() - t0:.1f} s: {exc}")
        return
    total = time.monotonic() - t0
    if as_json:
        phases = costs(runs / out.run_id / "steps.jsonl")
        print(
            json.dumps(
                {
                    "page": page,
                    "total_s": round(total, 1),
                    "phases": {p[0]: round(p[1], 1) for p in phases},
                    "loads": sum(p[2] for p in phases),
                    "outcomes": {
                        f.test_id.value: f.outcome.value for f in out.report.findings
                    },
                    "run_id": out.run_id,
                    "errors": out.errors,
                }
            )
        )
        return
    lim = out.report.versions.run_settings
    extra = len(out.report.other_pages) * lim.get("other_page_s", 0)
    print(f"\n{page}  (limit {limit + extra} s, total {total:.1f} s)")
    print(
        f"  {'phase':8} {'s':>7} {'loads':>6} {'presses':>8} {'quick':>6} {'redos':>6}"
    )
    for name, s, loads, presses, quick, redos in costs(
        runs / out.run_id / "steps.jsonl"
    ):
        print(f"  {name:9} {s:7.1f} {loads:6} {presses:8} {quick:6} {redos:6}")
    asked = [q.test_id.value for q in out.open_questions]
    for f in out.report.findings:
        n = asked.count(f.test_id.value)
        print(f"  {f.test_id.value} {f.outcome.value}" + (f" ({n} open)" if n else ""))
    for e in out.errors:
        print(f"  error: {e}")


async def main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pages", nargs="+")
    ap.add_argument("--limit", type=int, default=120)
    ap.add_argument("--no-time-limit", action="store_true")
    ap.add_argument("--drafts", action="store_true")
    ap.add_argument("--other", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--keep", type=Path)
    args = ap.parse_args(argv)
    if args.drafts:
        sys.path.insert(0, str(FIXTURES.parent.parent))
        from tests.drafts import DRAFTS

        REGISTRY.update(DRAFTS)
    egress.RESOLVER = _offline
    base = _serve()
    with tempfile.TemporaryDirectory() as tmp:
        runs = args.keep or Path(tmp)
        for page in args.pages:
            await measure(
                base,
                page,
                args.limit,
                runs,
                args.no_time_limit,
                args.other,
                args.json,
            )


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
