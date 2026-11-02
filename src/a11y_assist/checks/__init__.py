"""TT checks: one module per Trusted Tester test, each with its rules spec in
docs/rules/. See checks/base.py for the interface and how to add one."""

from __future__ import annotations

from a11y_assist.checks.base import Check, RunContext
from a11y_assist.checks.t4a import Check4A
from a11y_assist.checks.t4b import Check4B
from a11y_assist.checks.t4c import Check4C
from a11y_assist.checks.t4d import Check4D
from a11y_assist.checks.t4e import Check4E
from a11y_assist.checks.t4f import Check4F
from a11y_assist.checks.t5a import Check5A
from a11y_assist.checks.t5c import Check5C
from a11y_assist.checks.t5d import Check5D
from a11y_assist.checks.t5f import Check5F
from a11y_assist.checks.t5g import Check5G
from a11y_assist.checks.t9a import Check9A
from a11y_assist.checks.t9b import Check9B
from a11y_assist.checks.t9c import Check9C
from a11y_assist.checks.t19a import Check19A
from a11y_assist.models import TestId

REGISTRY: dict[TestId, Check] = {
    c.test_id: c
    for c in (
        Check4A(),
        Check4B(),
        Check4C(),
        Check4D(),
        Check4E(),
        Check4F(),
        Check5A(),
        Check5C(),
        Check5D(),
        Check5F(),
        Check5G(),
        Check9A(),
        Check9B(),
        Check9C(),
        Check19A(),
    )
}

__all__ = ["REGISTRY", "Check", "RunContext"]
