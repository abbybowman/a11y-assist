"""Smoke test for the container image, run by .github/workflows/container.yml
(not collected by pytest): the server, started by the image's own command,
answers over HTTP and finishes one real run.

    docker run -d --name tobi -e MCP_HOST=127.0.0.1 -e DEV_MODE=true <image>
    docker exec tobi uv run --no-sync python tests/container_smoke.py

It checks the plumbing a hosted server needs (HTTP transport, Chromium in
the image, headless, writable run storage), not outcomes: those belong to the
rules specs and the test suite.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
import urllib.request
from pathlib import Path

from fastmcp import Client

BASE = "http://127.0.0.1:8000"
PAGE = (Path(__file__).parent / "fixtures" / "no_trap.html").resolve().as_uri()


def wait_for_health(deadline_s: float = 60) -> None:
    end = time.monotonic() + deadline_s
    while True:
        try:
            with urllib.request.urlopen(BASE + "/health", timeout=2) as r:
                if r.status == 200:
                    return
        except OSError:
            pass
        if time.monotonic() > end:
            sys.exit("server did not answer /health")
        time.sleep(1)


def unwrap(content: dict) -> dict:
    """A tool whose result is one of several models wraps it in "result"."""
    return content.get("result", content)


async def main() -> None:
    wait_for_health()
    async with Client(BASE + "/mcp", timeout=300) as c:
        tools = {t.name for t in await c.list_tools()}
        assert "tobi_run_tt_tests" in tools, tools
        r = await c.call_tool("tobi_run_tt_tests", {"url": PAGE, "tests": ["4.C"]})
        data = unwrap(r.structured_content)
        while data.get("status") in ("queued", "running"):  # outlived one call
            r = await c.call_tool("tobi_run_status", {"job_id": data["job_id"]})
            data = unwrap(r.structured_content)
        findings = {f["test_id"]: f["outcome"] for f in data["findings"]}
        assert "4.C" in findings, data
        assert "NOT a certified" in data["disclaimer"]
        assert data["report_uri"].startswith("run://")
        report = await c.read_resource(data["report_uri"])
        versions = json.loads(report[0].text)["versions"]
        print("ok:", findings, versions.get("browser"), versions.get("os"))


asyncio.run(main())
