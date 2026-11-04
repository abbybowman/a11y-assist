"""Freezing a round (evals/agent/freeze.py) and Agent B's replay of it in
Playwright MCP (evals/agent/node/frozen-init.cjs), with the site down."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.agent.arms import PLAYWRIGHT_MCP as MCP_BIN
from evals.agent.arms import browser_arm
from evals.agent.freeze import freeze

from .conftest import LocalServer


async def _frozen_round(settings, tmp_path) -> tuple[Path, list[str]]:
    srv = LocalServer()
    urls = [
        f"{srv.base}/19a/t-benefits.html",
        f"{srv.base}/19a/home.html",
    ]
    rd = tmp_path / "round"
    rd.mkdir()
    (rd / "pages.txt").write_text("".join(f"{u} {'ab' * 32}\n" for u in urls))
    try:
        log = await freeze(rd, settings)
    finally:
        srv.stop()  # from here on, the site is down
    assert {e["status"] for e in log["pages"].values()} == {"frozen"}
    return rd, urls


async def test_freeze_records_every_page_and_the_search(settings, tmp_path):
    rd, urls = await _frozen_round(settings, tmp_path)
    index = json.loads((rd / "frozen" / "index.json").read_text())
    assert set(urls) <= set(index)
    assert any("search" in u for u in index)
    # 19.A suggested the site map for the home page: frozen too, once; its
    # own links were not followed.
    log = json.loads((rd / "frozen" / "freeze.json").read_text())
    assert any(u.endswith("/19a/sitemap.html") for u in index)
    assert any(e.get("suggested") for e in log["pages"].values())
    assert not any(
        u.endswith(("/19a/contact.html", "/19a/t2-status.html")) for u in index
    )
    assert not any(settings.runs_dir.glob("*/report.json"))  # results discarded


@pytest.mark.skipif(not MCP_BIN.exists(), reason="npm install in evals/agent/node")
async def test_playwright_mcp_replays_the_frozen_round(settings, tmp_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from playwright.async_api import async_playwright

    rd, urls = await _frozen_round(settings, tmp_path)
    async with async_playwright() as pw:
        chrome = pw.chromium.executable_path  # full Chromium, as Agent A's
    (srv,) = browser_arm(rd / "frozen", tmp_path / "out", chrome)
    params = StdioServerParameters(command=srv.command, args=srv.args, env=srv.env)
    async with stdio_client(params) as (r, w), ClientSession(r, w) as mcp:
        await mcp.initialize()
        got = await mcp.call_tool("browser_navigate", {"url": urls[0]})
        text = "".join(c.text for c in got.content if hasattr(c, "text"))
        assert "Page Title: Apply for benefits" in text, text[:2000]
        # Automatic snapshots go to a file Agent B cannot open (it has no file
        # tools); browser_snapshot returns the page inline.
        snap = await mcp.call_tool("browser_snapshot", {})
        stext = "".join(c.text for c in snap.content if hasattr(c, "text"))
        assert "heading" in stext and "Apply for benefits" in stext, stext[:2000]
        port = urls[0].split(":")[2].split("/")[0]
        # The page 19.A suggested (frozen by freeze.py) opens for Agent B as
        # it does for Agent A: the same frozen copy, never the live site.
        smap = await mcp.call_tool(
            "browser_navigate", {"url": f"http://127.0.0.1:{port}/19a/sitemap.html"}
        )
        sm = "".join(c.text for c in smap.content if hasattr(c, "text"))
        assert not smap.is_error and "Page Title: Site map" in sm, sm[:2000]
        miss = await mcp.call_tool(
            "browser_navigate", {"url": f"http://127.0.0.1:{port}/19a/not-frozen.html"}
        )
        mtext = "".join(c.text for c in miss.content if hasattr(c, "text"))
        assert miss.is_error or "ERR_FAILED" in mtext or "net::" in mtext, mtext[:2000]
