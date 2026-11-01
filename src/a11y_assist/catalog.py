"""The TT 5.1.3 test catalog, from the machine-readable copy of the PDF
(docs/sources/tt-5.1.3/tt.json; see docs/sources/README.md).

Everything about a test that comes from the PDF (name, condition, how to test,
requirements, WCAG links) is read from here, never retyped in code.
"""

from __future__ import annotations

import json
from functools import cache
from typing import Any

from a11y_assist.config import REPO_ROOT

TT_DIR = REPO_ROOT / "docs" / "sources" / "tt-5.1.3"
TT_VERSION = "5.1.3"


@cache
def data() -> dict[str, Any]:
    return json.loads((TT_DIR / "tt.json").read_text("utf-8"))


@cache
def tests() -> dict[str, dict[str, Any]]:
    """Test ID -> record, in document order."""
    return {t["id"]: t for t in data()["tests"]}


def active_ids() -> list[str]:
    return [i for i, t in tests().items() if t["status"] == "active"]


def wcag_label(test_id: str) -> str:
    """'2.1.2 No Keyboard Trap; Con.5 Conformance Requirement 5. ...'."""
    return "; ".join(r["label"] for r in tests()[test_id]["requirements"])


def understanding_urls(test_id: str) -> list[str]:
    return [
        r["understanding_url"]
        for r in tests()[test_id]["requirements"]
        if r.get("understanding_url")
    ]


def test_markdown(test_id: str) -> str:
    """One test as Markdown: a header with its requirements and links, the
    section's Identify Content, then the test's own text from the PDF."""
    t = tests()[test_id]
    lines = [
        f"# TT {TT_VERSION} test {t['id']}: {t['name']}",
        "",
        f"**Test condition:** {t['condition']}",
        "",
        f"**Status:** {t['status']}"
        + (f" ({t['status_basis']})" if t.get("status_basis") else ""),
        "",
        f"**Section:** {t.get('section', {}).get('title', 'n/a')}",
        "",
        "**Requirements:**",
        "",
    ]
    for r in t["requirements"]:
        extra = f", Level {r['level']}" if r.get("level") else ""
        if r.get("understanding_url"):
            ref = f" ([Understanding]({r['understanding_url']}))"
        elif r.get("url"):
            ref = f" ([WCAG 2.0]({r['url']}))"
        else:
            ref = ""
        lines.append(f"- {r['label']}{extra}{ref}")
    if t.get("identify_content"):
        lines += [
            "",
            "## Identify Content (shared by the section)",
            "",
            t["identify_content"],
        ]
    if t.get("markdown"):
        lines += ["", "## Test text (TT 5.1.3)", "", t["markdown"]]
    lines += [
        "",
        "---",
        "Source: DHS Trusted Tester Section 508 Conformance Test Process for Web "
        f"v{TT_VERSION} (April 2024), converted to Markdown; the PDF is the authority.",
    ]
    return "\n".join(lines) + "\n"
