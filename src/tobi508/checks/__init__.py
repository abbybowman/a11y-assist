"""TT checks: one module per Trusted Tester test, each with its rules spec in
docs/rules/. See checks/base.py for the interface and how to add one."""

from __future__ import annotations

from tobi508.checks.base import Check, RunContext
from tobi508.checks.t2a import Check2A
from tobi508.checks.t2b import Check2B
from tobi508.checks.t2c import Check2C
from tobi508.checks.t2d import Check2D
from tobi508.checks.t4a import Check4A
from tobi508.checks.t4b import Check4B
from tobi508.checks.t4c import Check4C
from tobi508.checks.t4d import Check4D
from tobi508.checks.t4e import Check4E
from tobi508.checks.t4f import Check4F
from tobi508.checks.t5a import Check5A
from tobi508.checks.t5b import Check5B
from tobi508.checks.t5c import Check5C
from tobi508.checks.t5d import Check5D
from tobi508.checks.t5f import Check5F
from tobi508.checks.t5g import Check5G
from tobi508.checks.t5h import Check5H
from tobi508.checks.t9a import Check9A
from tobi508.checks.t9b import Check9B
from tobi508.checks.t9c import Check9C
from tobi508.checks.t19a import Check19A
from tobi508.models import TestId

REGISTRY: dict[TestId, Check] = {
    c.test_id: c
    for c in (
        Check2A(),
        Check2B(),
        Check2C(),
        Check2D(),
        Check4A(),
        Check4B(),
        Check4C(),
        Check4D(),
        Check4E(),
        Check4F(),
        Check5A(),
        Check5B(),
        Check5C(),
        Check5D(),
        Check5F(),
        Check5G(),
        Check5H(),
        Check9A(),
        Check9B(),
        Check9C(),
        Check19A(),
    )
}

__all__ = ["REGISTRY", "Check", "RunContext"]
