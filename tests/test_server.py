"""Smoke tests for the example MCP server.

These verify the server imports and every submodule registers without error.
Add functional tests for your own tools as you build them.
"""

from __future__ import annotations

from fastmcp import FastMCP

from a11y_assist.app import mcp
from a11y_assist.config import settings


def test_server_is_importable():
    assert mcp is not None


def test_server_has_name():
    assert mcp.name == "a11y-assist"


def test_default_transport_is_stdio():
    """Guard against accidentally shipping with a non-stdio default."""
    assert settings.mcp_transport == "stdio"


def test_tools_register_without_error():
    from a11y_assist.tools import register_tools

    register_tools(FastMCP("test"))  # must not raise


def test_prompts_register_without_error():
    from a11y_assist.prompts import register_prompts

    register_prompts(FastMCP("test"))  # must not raise


def test_resources_register_without_error():
    from a11y_assist.resources import register_resources

    register_resources(FastMCP("test"))  # must not raise


def test_routes_register_without_error():
    from a11y_assist.routes import register_routes

    register_routes(FastMCP("test"))  # must not raise


def test_instructions_have_a_tool_selection_guide():
    """Every tool, the explain prompt and both resource schemes are named, and
    the implemented-test list follows the check registry."""
    import asyncio

    from fastmcp import Client

    from a11y_assist.checks import REGISTRY

    async def names():
        async with Client(mcp) as client:
            tools = {t.name for t in await client.list_tools()}
            prompts = {p.name for p in await client.list_prompts()}
        return tools, prompts

    tools, prompts = asyncio.run(names())
    text = mcp.instructions
    assert "TOOL SELECTION GUIDE" in text
    for name in tools | prompts:
        assert name in text, name
    assert "tt://5.1.3/tests/" in text and "run://" in text
    for t in REGISTRY:
        assert t.value in text
    assert "NOT certified" in text
