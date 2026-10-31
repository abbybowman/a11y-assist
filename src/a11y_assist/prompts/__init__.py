"""Prompts submodule: reusable conversation starters, shown by clients as
commands. Each prompt module exposes a `register(mcp)` function."""

from __future__ import annotations

from a11y_assist.prompts import explain_result


def register_prompts(mcp) -> None:
    """Register all prompts with the MCP server."""
    explain_result.register(mcp)


__all__ = ["register_prompts"]
