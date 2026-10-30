"""Resources submodule — static/semi-static data the client can read directly.

Each resource module exposes a `register(mcp)` function; this file aggregates
them into `register_resources(mcp)`. None are defined yet.
"""

from __future__ import annotations


def register_resources(mcp) -> None:
    """Register all resources with the MCP server."""


__all__ = ["register_resources"]
