"""Vendored third-party files must match the hashes recorded at import time."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

THIRD_PARTY = Path(__file__).resolve().parents[1] / "third_party"
PROVENANCE = json.loads((THIRD_PARTY / "PROVENANCE.json").read_text())


@pytest.mark.parametrize("component", sorted(PROVENANCE))
def test_vendored_files_match_recorded_hashes(component: str) -> None:
    recorded = PROVENANCE[component]["sha256"]
    on_disk = {
        p.relative_to(THIRD_PARTY / component).as_posix(): hashlib.sha256(
            p.read_bytes()
        ).hexdigest()
        for p in (THIRD_PARTY / component).rglob("*")
        if p.is_file() and p.name != "NOTICE"  # NOTICE is ours, not upstream
    }
    assert on_disk == recorded


def test_andi_version_string_matches_provenance() -> None:
    js = (THIRD_PARTY / "andi" / "andi.js").read_text(encoding="utf-8")
    assert f'var andiVersionNumber = "{PROVENANCE["andi"]["version"]}";' in js
