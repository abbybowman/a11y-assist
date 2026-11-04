"""Freeze a round's tested pages once, for both arms of the agent eval
(docs/plans/2026-10-31-agent-eval.md section 6).

    uv run python -m evals.agent.freeze evals/judging/<round>

(headless: BROWSER_CHANNEL=chromium HEADLESS=true)

Each page in <round>/pages.txt is recorded once, as a live run records it
(capture.record: the allowlist and every redirect hop checked, scrolled to
load lazy content), into <round>/frozen/ (index.json, the recordings and
freeze.json). Nothing else is recorded: during the arms, other pages of the
tested site (site maps, search results, any route an agent tries) load live
for both arms, and the tested pages come only from these copies.

This step touches the live site, close to the tester's own testing; compare
each page's footer timestamp with the tester's after freezing.
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

from a11y_assist.browser import launch_browser
from a11y_assist.config import Settings
from a11y_assist.egress import EgressProxy
from a11y_assist.frozen import load, obtain
from a11y_assist.policy import check_url
from a11y_assist.redact import safe_error
from evals.judging import JudgingError, _pages

FROZEN = "frozen"


async def freeze(rd: Path, settings: Settings) -> dict:
    if (rd / "results" / "lock.json").exists():
        raise JudgingError("This round is locked")
    folder = rd / FROZEN
    s = settings.model_copy(
        update={"frozen_pages_dir": folder, "frozen_pages_mode": "record_missing"}
    )
    pages = [u for u, _ in _pages(rd)]
    log: dict = {"started_at": datetime.now(timezone.utc).isoformat(), "pages": {}}
    async with EgressProxy(s) as proxy, async_playwright() as pw:
        browser = await launch_browser(pw, s, proxy)
        try:
            for url in pages:
                t0 = time.monotonic()
                entry: dict = {}
                print(f"freezing {url}", flush=True)
                decision = check_url(url, s.allowed_domains, s.dev_mode)
                try:
                    if not decision.allowed:
                        raise ValueError(f"not allowed: {decision.reason}")
                    with tempfile.TemporaryDirectory() as tmp:
                        cap = await obtain(
                            browser,
                            s,
                            url,
                            Path(tmp) / "page.har.zip",
                            lambda *a, **k: None,
                            proxy,
                        )
                    entry.update(
                        status="frozen",
                        final_url=cap.final_url,
                        cross_site_frames=len(cap.cross_site_frames),
                    )
                except Exception as exc:  # recorded: the arms are refused it
                    entry.update(status="error", error=safe_error(exc)[:300])
                entry["seconds"] = round(time.monotonic() - t0, 1)
                log["pages"][url] = entry
        finally:
            await browser.close()
    folder.mkdir(parents=True, exist_ok=True)
    log["finished_at"] = datetime.now(timezone.utc).isoformat()
    log["recordings"] = len(load(folder))
    (folder / "freeze.json").write_text(json.dumps(log, indent=1) + "\n")
    return log


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        sys.exit(__doc__)
    log = asyncio.run(freeze(Path(argv[0]), Settings()))
    bad = [u for u, e in log["pages"].items() if e["status"] != "frozen"]
    print(f"{log['recordings']} recordings; pages not frozen: {bad or 'none'}")


if __name__ == "__main__":
    main(sys.argv[1:])
