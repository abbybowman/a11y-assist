"""Resources submodule: data the client can read directly.

Each resource module exposes a `register(mcp)` function; this file aggregates
them into `register_resources(mcp)`.
"""

from __future__ import annotations

from a11y_assist.resources import runs, tt


def register_resources(mcp) -> None:
    """Register all resources with the MCP server."""
    runs.register(mcp)
    tt.register(mcp)


__all__ = ["register_resources"]
