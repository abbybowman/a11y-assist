"""Freezing a round (evals/agent/freeze.py) and Agent B's browser on it in
Playwright MCP (evals/agent/node/frozen-init.cjs): the tested pages only
from the frozen copies; other pages of the tested site live, logged and
through the egress proxy; other sites refused."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from a11y_assist.egress import EgressProxy
from evals.agent.arms import PLAYWRIGHT_MCP as MCP_BIN
from evals.agent.arms import browser_arm
from evals.agent.freeze import freeze

from .conftest import LocalServer


async def _frozen_round(settings, tmp_path, stop=True) -> tuple[Path, list[str]]:
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
        if stop:
            srv.stop()  # from here on, the site is down
    assert {e["status"] for e in log["pages"].values()} == {"frozen"}
    return rd, (urls if stop else (urls, srv))


async def test_freeze_records_the_tested_pages_only(settings, tmp_path):
    rd, urls = await _frozen_round(settings, tmp_path)
    index = json.loads((rd / "frozen" / "index.json").read_text())
    assert sorted(index) == sorted(urls)  # no search, no site map: those are live
    log = json.loads((rd / "frozen" / "freeze.json").read_text())
    assert log["recordings"] == 2


def _text(res) -> str:
    return "".join(c.text for c in res.content if hasattr(c, "text"))


@pytest.mark.skipif(not MCP_BIN.exists(), reason="npm install in evals/agent/node")
async def test_agent_b_browser_rules(settings, tmp_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from playwright.async_api import async_playwright

    rd, (urls, srv) = await _frozen_round(settings, tmp_path, stop=False)
    try:
        hits_before = srv.hits[("127.0.0.1", "/19a/t-benefits.html")]
        async with async_playwright() as pw:
            chrome = pw.chromium.executable_path  # full Chromium, as Agent A's
        live_log = tmp_path / "live.jsonl"
        async with EgressProxy(settings) as proxy:
            (srv_def,) = browser_arm(
                rd / "frozen", tmp_path / "out", chrome, proxy.url, live_log
            )
            params = StdioServerParameters(
                command=srv_def.command, args=srv_def.args, env=srv_def.env
            )
            async with stdio_client(params) as (r, w), ClientSession(r, w) as mcp:
                await mcp.initialize()
                # A tested page: its frozen copy, never the live site.
                got = await mcp.call_tool("browser_navigate", {"url": urls[0]})
                assert "Page Title: Apply for benefits" in _text(got), _text(got)[:2000]
                # Automatic snapshots go to a file Agent B cannot open (it has no
                # file tools); browser_snapshot returns the page inline.
                snap = _text(await mcp.call_tool("browser_snapshot", {}))
                assert "heading" in snap and "Apply for benefits" in snap
                # Another page of the tested site: live, as for Agent A.
                smap = await mcp.call_tool(
                    "browser_navigate", {"url": f"{srv.base}/19a/sitemap.html"}
                )
                assert "Page Title: Site map" in _text(smap), _text(smap)[:2000]
                # Another site: refused.
                other = await mcp.call_tool(
                    "browser_navigate",
                    {"url": f"http://localhost:{srv.port}/19a/sitemap.html"},
                )
                assert other.is_error or "ERR_BLOCKED" in _text(other)
            connected = list(proxy.connected)
        assert srv.hits[("127.0.0.1", "/19a/t-benefits.html")] == hits_before
        assert srv.hits[("127.0.0.1", "/19a/sitemap.html")] >= 1
        assert srv.hits[("localhost", "/19a/sitemap.html")] == 0
        rows = [json.loads(x) for x in live_log.read_text().splitlines()]
        assert any(r.get("live") and r["url"].endswith("/sitemap.html") for r in rows)
        assert any(r.get("refused") and "localhost" in r["url"] for r in rows)
        assert connected, "live loads go through the egress proxy"
    finally:
        srv.stop()
