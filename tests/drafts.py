"""Checks whose spec is still a draft (0.y.z): not in checks.REGISTRY, so the
server gives no outcome for them (CLAUDE.md principle 2), but registered here
for the tests that build them. Move a check to checks/__init__.py when its
spec reaches 1.0.0."""

from __future__ import annotations

import pytest

from a11y_assist.checks import REGISTRY
from a11y_assist.checks.base import Check
from a11y_assist.models import TestId

# None now: 5.F and 5.G moved to the registry at 1.0.0 (2026-11-01).
DRAFTS: dict[TestId, Check] = {}


@pytest.fixture
def drafts(monkeypatch):
    """Register the draft checks for one test."""
    for t, c in DRAFTS.items():
        monkeypatch.setitem(REGISTRY, t, c)
