"""Checks whose spec is still a draft (0.y.z): not in checks.REGISTRY, so the
server gives no outcome for them (CLAUDE.md principle 2), but registered here
for the tests that build them. Move a check to checks/__init__.py when its
spec reaches 1.0.0."""

from __future__ import annotations

import pytest

from tobi508.checks import REGISTRY
from tobi508.checks.base import Check
from tobi508.checks.t3a import Check3A
from tobi508.models import TestId

# 2.A-2.D moved to the registry at 1.0.0 (2026-11-05). 3.A's spec is 0.2.0.
DRAFTS: dict[TestId, Check] = {TestId.T3A: Check3A()}


@pytest.fixture
def drafts(monkeypatch):
    """Register the draft checks for one test."""
    for t, c in DRAFTS.items():
        monkeypatch.setitem(REGISTRY, t, c)
