"""Checks whose spec is still a draft (0.y.z): not in checks.REGISTRY, so the
server gives no outcome for them (CLAUDE.md principle 2), but registered here
for the tests that build them. Move a check to checks/__init__.py when its
spec reaches 1.0.0."""

from __future__ import annotations

import pytest

from a11y_assist.checks import REGISTRY
from a11y_assist.checks.base import Check
from a11y_assist.checks.t2b import Check2B
from a11y_assist.checks.t2c import Check2C
from a11y_assist.checks.t2d import Check2D
from a11y_assist.models import TestId

# 2.B, 2.C and 2.D: draft specs (docs/rules/2c-build-tasks.md).
DRAFTS: dict[TestId, Check] = {
    TestId.T2B: Check2B(),
    TestId.T2C: Check2C(),
    TestId.T2D: Check2D(),
}


@pytest.fixture
def drafts(monkeypatch):
    """Register the draft checks for one test."""
    for t, c in DRAFTS.items():
        monkeypatch.setitem(REGISTRY, t, c)
