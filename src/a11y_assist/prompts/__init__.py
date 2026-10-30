"""Prompts submodule — reusable conversation starters.

Each prompt module exposes a `register(mcp)` function; this file aggregates them
into `register_prompts(mcp)`. None are defined yet.
"""

from __future__ import annotations


def register_prompts(mcp) -> None:
    """Register all prompts with the MCP server."""


__all__ = ["register_prompts"]
