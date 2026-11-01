"""Checks whose spec is still a draft (0.y.z): not in checks.REGISTRY, so the
server gives no outcome for them (CLAUDE.md principle 2), but registered here
for the tests that build them. Move a check to checks/__init__.py when its
spec reaches 1.0.0."""

from __future__ import annotations

import pytest

from a11y_assist.checks import REGISTRY
from a11y_assist.checks.base import Check
from a11y_assist.checks.t5a import Check5A
from a11y_assist.checks.t5c import Check5C
from a11y_assist.models import TestId

# 5.A and 5.C: specs at 0.x (docs/rules/5a-*, 5c-*).
DRAFTS: dict[TestId, Check] = {TestId.T5A: Check5A(), TestId.T5C: Check5C()}


@pytest.fixture
def drafts(monkeypatch):
    """Register the draft checks for one test."""
    for t, c in DRAFTS.items():
        monkeypatch.setitem(REGISTRY, t, c)
