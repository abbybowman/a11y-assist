"""Model routes for the agent eval (docs/plans/2026-10-31-agent-eval.md
section 7.1). One interface; one adapter per route. Every adapter returns
the API's own usage counts, so tokens are never estimated.

Anthropic-style Messages API (Ask Sage's /server/anthropic route, or the
claude.ai API), configured from the environment or the root .env, never
the repository:

    AGENT_API_BASE         e.g. https://api.asksage.ai.nasa.gov/server/anthropic
    AGENT_API_KEY          the token
    AGENT_API_AUTH_HEADER  the header that carries it (default x-api-key)
    AGENT_MODEL            e.g. claude-sonnet-5-5-gov

Standard library only (urllib), so the eval adds no dependency.
"""

from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

REPO = Path(__file__).resolve().parents[2]
ANTHROPIC_VERSION = "2023-06-01"


@dataclass
class Reply:
    content: list[dict[str, Any]]  # Anthropic content blocks
    stop_reason: str
    model: str  # as the API reports it
    usage: dict[str, int] = field(default_factory=dict)


class ContextExceeded(RuntimeError):
    """The conversation no longer fits the model's context window."""


class Provider(Protocol):
    route: str
    model: str

    async def complete(
        self, system: str, messages: list[dict], tools: list[dict], max_tokens: int
    ) -> Reply: ...


def _dotenv() -> dict[str, str]:
    f = REPO / ".env"
    out: dict[str, str] = {}
    if f.is_file():
        for line in f.read_text("utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("'\"")
    return out


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name) or _dotenv().get(name) or default


class AnthropicMessages:
    """POST {base}/v1/messages. Temperature 0."""

    route = "anthropic-messages"

    def __init__(
        self,
        base: str,
        key: str,
        model: str,
        auth_header: str = "x-api-key",
        timeout_s: float = 600,
    ):
        self.base, self.key, self.model = base.rstrip("/"), key, model
        self.auth_header, self.timeout_s = auth_header, timeout_s

    @classmethod
    def from_env(cls) -> AnthropicMessages:
        missing = [
            n for n in ("AGENT_API_BASE", "AGENT_API_KEY", "AGENT_MODEL") if not env(n)
        ]
        if missing:
            raise SystemExit(f"Set {', '.join(missing)} (environment or root .env)")
        return cls(
            env("AGENT_API_BASE"),
            env("AGENT_API_KEY"),
            env("AGENT_MODEL"),
            env("AGENT_API_AUTH_HEADER", "x-api-key"),
        )

    def _post(self, body: dict) -> dict:
        req = urllib.request.Request(
            f"{self.base}/v1/messages",
            data=json.dumps(body).encode(),
            headers={
                "content-type": "application/json",
                "anthropic-version": ANTHROPIC_VERSION,
                self.auth_header: self.key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:2000]
            if e.code == 400 and ("too long" in text or "context" in text.lower()):
                raise ContextExceeded(text) from None
            raise RuntimeError(f"HTTP {e.code} from the model API: {text}") from None

    async def complete(self, system, messages, tools, max_tokens) -> Reply:
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": 0,
            "system": system,
            "messages": messages,
        }
        if tools:
            body["tools"] = tools
        raw = await asyncio.to_thread(self._post, body)
        return Reply(
            content=raw.get("content", []),
            stop_reason=raw.get("stop_reason") or "",
            model=raw.get("model") or "",
            usage={
                k: v for k, v in (raw.get("usage") or {}).items() if isinstance(v, int)
            },
        )


class Scripted:
    """For tests: replies from a function of the conversation so far."""

    route = "scripted"

    def __init__(self, model: str, fn):
        self.model, self._fn = model, fn

    async def complete(self, system, messages, tools, max_tokens) -> Reply:
        return self._fn(system, messages, tools)
