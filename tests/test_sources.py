"""Vendored source documents match their recorded hashes."""

from __future__ import annotations

import hashlib
import re

from a11y_assist.config import REPO_ROOT

SOURCES = REPO_ROOT / "docs" / "sources"


def test_source_hashes_match_readme() -> None:
    rows = re.findall(
        r"\| `([^`]+)` \|.*\| `([0-9a-f]{64})` \|", (SOURCES / "README.md").read_text()
    )
    assert rows
    for name, digest in rows:
        assert hashlib.sha256((SOURCES / name).read_bytes()).hexdigest() == digest, name
