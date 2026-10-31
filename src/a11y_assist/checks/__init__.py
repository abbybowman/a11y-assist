"""TT checks: one module per Trusted Tester test, each with its rules spec in
docs/rules/. See checks/base.py for the interface and how to add one."""

from __future__ import annotations

from a11y_assist.checks.base import Check, RunContext
from a11y_assist.checks.t4c import Check4C
from a11y_assist.models import TestId

REGISTRY: dict[TestId, Check] = {c.test_id: c for c in (Check4C(),)}

__all__ = ["REGISTRY", "Check", "RunContext"]
