"""The TT 5.1.3 test process as MCP resources, so a client can look up any
test (what it checks, how a tester does it, the WCAG requirement and its
Understanding page) without the PDF.

  tt://5.1.3/index           every test condition: ID, name, status, condition
  tt://5.1.3/tests/{test_id} one test as Markdown (e.g. tt://5.1.3/tests/4.C)
  tt://5.1.3/parts/{part}    a whole part of the document (e.g. 04-keyboard-
                             access-and-focus, appendix-b-change-log)

Text from the DHS document (a U.S. government work); the PDF is the authority.
"""

from __future__ import annotations

import json
import re

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError

from tobi508 import catalog

BASE = f"tt://{catalog.TT_VERSION}"


def test_uri(test_id: str) -> str:
    return f"{BASE}/tests/{test_id}"


def register(mcp: FastMCP) -> None:
    @mcp.resource(
        f"{BASE}/index",
        name="tt_index",
        mime_type="application/json",
        description="Every Trusted Tester 5.1.3 test condition: ID, name, status "
        "(active, obsolete, removed), condition and requirements.",
    )
    def tt_index() -> str:
        rows = [
            {
                "id": t["id"],
                "name": t["name"],
                "status": t["status"],
                "condition": t["condition"],
                "requirements": [r["label"] for r in t["requirements"]],
                "uri": test_uri(t["id"]),
            }
            for t in catalog.tests().values()
        ]
        return json.dumps(rows, ensure_ascii=False, indent=1)

    @mcp.resource(
        f"{BASE}/tests/{{test_id}}",
        name="tt_test",
        mime_type="text/markdown",
        description="One Trusted Tester 5.1.3 test as Markdown: condition, "
        "requirements with WCAG Understanding links, Identify Content, "
        "Applicability, How to Test, Evaluate Results and notes.",
    )
    def tt_test(test_id: str) -> str:
        if test_id not in catalog.tests():
            raise ResourceError(f"No TT {catalog.TT_VERSION} test {test_id!r}")
        return catalog.test_markdown(test_id)

    @mcp.resource(
        f"{BASE}/parts/{{part}}",
        name="tt_part",
        mime_type="text/markdown",
        description="A whole part of the TT 5.1.3 document as Markdown, e.g. "
        "00-conformance-reporting, 04-keyboard-access-and-focus, "
        "appendix-b-change-log. An unknown name lists the parts.",
    )
    def tt_part(part: str) -> str:
        if not re.fullmatch(r"[a-z0-9-]{1,80}", part):
            raise ResourceError("Invalid part name")
        path = catalog.TT_DIR / "md" / f"{part}.md"
        if not path.is_file():
            names = sorted(p.stem for p in (catalog.TT_DIR / "md").glob("*.md"))
            raise ResourceError(f"No part {part!r}. Parts: {', '.join(names)}")
        return path.read_text("utf-8")
