"""Checks whose spec is still a draft (0.y.z): not in checks.REGISTRY, so the
server gives no outcome for them (CLAUDE.md principle 2), but registered here
for the tests that build them. Move a check to checks/__init__.py when its
spec reaches 1.0.0."""

from __future__ import annotations

import pytest

from a11y_assist.checks import REGISTRY
from a11y_assist.checks.base import Check
from a11y_assist.checks.t5f import Check5F
from a11y_assist.checks.t5g import Check5G
from a11y_assist.models import TestId

# 5.F and 5.G: specs at 0.x (docs/rules/5f-*, 5g-*).
DRAFTS: dict[TestId, Check] = {TestId.T5F: Check5F(), TestId.T5G: Check5G()}


@pytest.fixture
def drafts(monkeypatch):
    """Register the draft checks for one test."""
    for t, c in DRAFTS.items():
        monkeypatch.setitem(REGISTRY, t, c)
