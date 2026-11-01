"""Vendored W3C ACT test cases: integrity, serving, and expected 4.C outcomes.

Expected outcomes come from manifest.json (never from the pages). Outcome tests run
for cases the implemented rows decide (DNA so far).
"""

from __future__ import annotations

import hashlib
import json

import pytest

from .conftest import ACT_ROOT
from .harness_4c import run_4c
from .scoring import write_score

MANIFEST = json.loads((ACT_ROOT / "manifest.json").read_text())
CASES = {c["id"]: c for c in MANIFEST["cases"]}


def test_manifest_files_match_their_hashes():
    for rel, digest in MANIFEST["files"].items():
        assert hashlib.sha256((ACT_ROOT / rel).read_bytes()).hexdigest() == digest, rel
    assert {c["path"] for c in CASES.values()} <= set(MANIFEST["files"])


def test_4c_cases_are_the_19_from_the_build_tasks():
    assert len([c for c in CASES.values() if c["tt_test"] == "4.C"]) == 19
    for c in CASES.values():
        assert c["expected"] in {"PASS", "FAIL", "DNA", "NEEDS_REVIEW"}


@pytest.mark.parametrize("case_id", sorted(CASES))
async def test_case_loads_with_every_asset(case_id, browser, act_server):
    failed = []
    ctx = await browser.new_context()
    page = await ctx.new_page()
    page.on("requestfailed", lambda r: failed.append(r.url))
    page.on("response", lambda r: failed.append(r.url) if r.status >= 400 else None)
    await page.goto(f"{act_server}/{CASES[case_id]['path']}")
    await page.wait_for_load_state("load")
    await ctx.close()
    assert failed == []


CTRL_M = {"documented": "yes", "keys": ["Ctrl+M"], "quote": "Press Ctrl+M to Exit"}
# What a correct judge answers on each case (test data; J1 defaults to "no").
ANSWERS = {
    "ab24c77e": CTRL_M,
    "e3902f01": CTRL_M,
    "b92b5214": CTRL_M,
    "62fd24e7": CTRL_M,
}

RESULTS: dict[str, str] = {}


@pytest.mark.parametrize(
    "case_id", sorted(c for c in CASES if CASES[c]["tt_test"] == "4.C")
)
async def test_case_outcome(case_id, settings, act_server, record_property):
    case = CASES[case_id]
    got = await run_4c(settings, f"{act_server}/{case['path']}", ANSWERS.get(case_id))
    outcome = got["finding"].outcome.value
    RESULTS[case_id] = outcome
    record_property("act_outcome", outcome)
    write_score(case_id, outcome, got["finding"].rows)
    assert outcome == case["expected"], got["finding"].rationale
