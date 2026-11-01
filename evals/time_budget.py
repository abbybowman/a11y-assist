"""Where a run's time goes: run a11y_run_tt_tests (every implemented test, as
the tool's default) on local fixture pages and print each phase's cost from
the run's steps.jsonl (record, walk, each check's collect: seconds, page loads,
key presses). Measurement only; it decides nothing.

    uv run python evals/time_budget.py 4d/f10-100-links.html budget/agency-home.html
    uv run python evals/time_budget.py --limit 900 4c/f34-600-links.html

--limit sets RUN_LIMIT_S for the run (default 120, the tool's own); a larger
limit shows what an uncapped run would cost. Paths are under tests/fixtures/.
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
from a11y_assist.pipeline import run_tt_tests

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


def costs(steps_path: Path) -> list[tuple[str, float, int, int]]:
    """(phase, seconds, loads, presses) per phase, from steps.jsonl."""
    out = []
    for line in steps_path.read_text("utf-8").splitlines():
        e = json.loads(line)
        d = e["detail"]
        if e["step"] == "captured":
            out.append(("record", d.get("seconds", 0.0), 1, 0))
        elif e["step"] == "walk":
            c = d["cost"]
            out.append(("walk", c["seconds"], c["loads"], c["presses"]))
        elif e["step"] == "collected":
            c = d["cost"]
            out.append((d["test"], c["seconds"], c["loads"], c["presses"]))
    return out


async def measure(base: str, page: str, limit: int, runs: Path) -> None:
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
    out = await run_tt_tests(settings, f"{base}/{page}", list(REGISTRY))
    total = time.monotonic() - t0
    print(f"\n{page}  (limit {limit} s, total {total:.1f} s)")
    print(f"  {'phase':8} {'s':>7} {'loads':>6} {'presses':>8}")
    for name, s, loads, presses in costs(runs / out.run_id / "steps.jsonl"):
        print(f"  {name:8} {s:7.1f} {loads:6} {presses:8}")
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
    args = ap.parse_args(argv)
    egress.RESOLVER = _offline
    base = _serve()
    with tempfile.TemporaryDirectory() as tmp:
        for page in args.pages:
            await measure(base, page, args.limit, Path(tmp))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
