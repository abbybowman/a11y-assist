"""The TT 5.1.3 copy (docs/sources/tt-5.1.3/) is complete and consistent."""

from __future__ import annotations

import json
import re

from a11y_assist.config import REPO_ROOT

TT = REPO_ROOT / "docs" / "sources" / "tt-5.1.3"
DATA = json.loads((TT / "tt.json").read_text("utf-8"))


def _norm(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", s)


def test_catalog_has_every_condition_once():
    ids = [t["id"] for t in DATA["tests"]]
    assert len(ids) == 63 == len(set(ids))  # "63 Test Conditions" (p. 5)
    status = {t["id"]: t["status"] for t in DATA["tests"]}
    assert status["5.E"] == "obsolete" and status["6.B"] == "removed"
    assert sum(s == "active" for s in status.values()) == 61
    assert [t["id"] for t in DATA["tests"] if t.get("not_tested_named")] == [
        "3.A",
        "20.A",
    ]


def test_known_records():
    t = {x["id"]: x for x in DATA["tests"]}
    assert t["4.C"]["name"] == "2.1.2-no-keyboard-trap"
    assert t["4.C"]["condition"] == "There is no keyboard trap."
    req = {r["id"]: r for r in t["4.C"]["requirements"]}
    assert req["2.1.2"]["level"] == "A"
    assert req["2.1.2"]["understanding_url"].endswith("/no-keyboard-trap.html")
    assert "Con.5" in req  # Non-Interference (Appendix A)
    assert "Continue from Test 4.C." in t["4.D"]["how_to_test"]


def test_every_active_test_has_its_blocks_and_text_in_its_section_file():
    for t in DATA["tests"]:
        if t["status"] != "active":
            continue
        assert t["name"] and t["condition"] and t["requirements"], t["id"]
        section = (TT / t["section"]["file"]).read_text("utf-8")
        assert _norm(t["markdown"]) in _norm(section), t["id"]
        assert _norm(t["condition"]) in _norm(section), t["id"]
        if t["id"] not in ("3.A", "20.A"):  # these two have no test steps
            assert t.get("how_to_test") and t.get("evaluate_results"), t["id"]
        for r in t["requirements"]:
            if r["kind"] == "wcag":
                assert r["level"] in ("A", "AA"), (t["id"], r)
                assert r["understanding_url"].startswith(
                    "https://www.w3.org/WAI/WCAG22/Understanding/"
                ), (t["id"], r)


def test_each_test_has_its_own_steps():
    """9.B's heading breaks over a line in the PDF ("consistent- navigation"),
    so the first conversion gave 9.B 9.A's steps and put 9.B's text in 9.C's
    Identify Content (fixed by hand from pp. 43-44, 2026-11-02). 5.B, 7.C and 16.B still
    repeat the previous test's steps (docs/ROADMAP.md)."""
    t = {x["id"]: x for x in DATA["tests"] if x["status"] == "active"}
    assert t["9.B"]["how_to_test"] != t["9.A"]["how_to_test"]
    assert t["9.B"]["how_to_test"].startswith("1. Review multiple web pages")
    assert "Same relative order" in t["9.B"]["notes"]
    assert "9.B" not in t["9.C"]["identify_content"]
