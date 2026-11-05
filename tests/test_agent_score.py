"""A whole agent round on fixtures (plan section 5): freeze, both arms with
scripted models, lock, reveal, score. Also the RESULT reader and roll-up."""

from __future__ import annotations

import hashlib
import json
import shutil

import pytest

from a11y_assist.scrt import ScrtResult as R
from evals.agent import run as agent_run
from evals.agent.arms import tool_arm
from evals.agent.freeze import freeze
from evals.agent.providers import Reply, Scripted
from evals.agent.score import parse_result, score
from evals.judging import JudgingError, lock
from evals.scoring import rollup

from .conftest import FIXTURES, LocalServer
from .test_agent_run import FIXTURE_ENV, _text, _usage, _use

SAMPLE = FIXTURES / "scrt" / "sample-scrt.json"


def test_rollup():
    assert rollup([R.PASS, R.FAIL, None]) is R.FAIL
    assert rollup([R.PASS, None]) is None
    assert rollup([R.PASS, R.NOT_TESTED]) is None
    assert rollup([R.PASS, R.DNA]) is R.PASS
    assert rollup([R.DNA, R.DNA]) is R.DNA
    assert rollup([]) is None


def test_parse_result_takes_the_last_line():
    assert parse_result('x\nRESULT: {"a": 1}\nRESULT: {"b": 2}') == {"b": 2}
    assert parse_result("RESULT: not json") is None
    assert parse_result("no result here") is None
    assert parse_result("RESULT: [1]") is None


def _key(results: dict[str, str]) -> bytes:
    data = json.loads(SAMPLE.read_text("utf-8"))
    for row in data[0]["Criteria"]:
        row["TestResult"] = results.get(row["TestID"].strip(), "")
    return json.dumps(data).encode()


async def test_a_whole_round(settings, tmp_path):
    srv = LocalServer()
    urls = [f"{srv.base}/19a/t-benefits.html", f"{srv.base}/19a/home.html"]
    keys = [_key({"19.A": "Pass", "4.C": "Fail"}), _key({"19.A": "Fail"})]
    rd = tmp_path / "round"
    rd.mkdir()
    (rd / "pages.txt").write_text(
        "".join(f"{u} {hashlib.sha256(k).hexdigest()}\n" for u, k in zip(urls, keys))
    )
    try:
        await freeze(rd, settings)
    finally:
        srv.stop()

    def agent_a(system, messages, tools):
        first = messages[0]["content"]
        if first.startswith("Before the task"):
            return Reply([_text("{}")], "end_turn", "m", _usage())
        if len(messages) == 1:
            args = {"url": urls[0], "tests": ["19.A"], "other_pages": [urls[1]]}
            return Reply(
                [_use("a1", "a11y_run_tt_tests", args)], "tool_use", "m", _usage()
            )
        line = {
            urls[0]: {
                "2.4.5": {"result": "PASS", "elements": []},
                "2.1.2": {"result": "FAIL", "elements": ["the menu"]},
            }
        }
        return Reply([_text("RESULT: " + json.dumps(line))], "end_turn", "m", _usage())

    def agent_b(system, messages, tools):
        return Reply([_text("I could not finish.")], "end_turn", "m", _usage())

    servers = tool_arm(
        (rd / "frozen").resolve(), "m", rd / "results" / "arm-a" / "runs"
    )
    servers[0].env |= FIXTURE_ENV
    sa = await agent_run.run_arm(rd, "a", Scripted("m", agent_a), servers)
    sb = await agent_run.run_arm(rd, "b", Scripted("m", agent_b), servers=[])
    assert sa.get("error") is None and sb.get("error") is None, (sa, sb)

    # A run is scored on the pages it was given (round 1's corrected typo).
    sb_file = rd / "results" / "arm-b" / "summary.json"
    sbd = json.loads(sb_file.read_text())
    sbd["pages"] = [urls[0]]
    sb_file.write_text(json.dumps(sbd))
    # A page recorded as not scored for a run (a broken frozen copy).
    (rd / "results" / "arm-a" / "not_scored.json").write_text(
        json.dumps({"pages": [urls[1]], "reason": "broken copy"})
    )

    with pytest.raises(JudgingError, match="Not locked"):
        score(rd)
    lock(rd)
    lk = json.loads((rd / "results" / "lock.json").read_text())
    assert any(f.startswith("frozen/") for f in lk["files"])
    assert any(f.startswith("results/arm-a/runs/") for f in lk["files"])
    (rd / "keys").mkdir()
    for i, k in enumerate(keys):
        (rd / "keys" / f"tester-{i}.json").write_bytes(k)

    out = score(rd)
    a, b = out["arms"]["arm-a"], out["arms"]["arm-b"]
    # Scored: page 1's 2.4.5 and 2.1.2, page 2's 2.4.5 (the keys leave the rest blank).
    assert a["per_criterion"]["counts"]["agree"] == 2
    assert a["per_criterion"]["counts"]["no_answer"] == 0  # page 2 not scored
    assert a["pages_not_given"] == [urls[1]] and a["not_scored_reason"] == "broken copy"
    assert a["fails"][0]["elements"] == ["the menu"]
    assert b["result_line"] == "missing or malformed"
    assert b["pages_not_given"] == [urls[1]]
    assert b["per_criterion"]["counts"]["no_answer"] == 2  # page 2 not given
    assert b["per_criterion"]["weighted"] == -2
    sv = a["server"]
    assert sv["pages_not_tested"] == []  # page 2 not scored for this run
    assert sv["per_tt"]["counts"]["not_performed"] >= 1  # 4.C was not run
    assert a["efficiency"]["tool_calls"] == {"a11y_run_tt_tests": 1}
    assert "Not a certified" in (rd / "agent-score.md").read_text()

    # A result changed after the lock stops the score.
    f = rd / "results" / "arm-b" / "final.md"
    f.write_text('RESULT: {"x": {}}\n')
    with pytest.raises(JudgingError, match="changed after the lock"):
        score(rd)
    shutil.rmtree(rd / "keys")


def test_page_keys_keep_the_query():
    """Post-round 1 fix 13: a search results page is not the home page."""
    from a11y_assist.compare import page_key

    assert page_key("https://www.nasa.gov/?search=artemis") == "nasa.gov?search=artemis"
    assert page_key("https://www.nasa.gov/") == "nasa.gov"
    assert page_key("www.nasa.gov/?search=artemis#top") == "nasa.gov?search=artemis"


def test_a_page_split_over_calls_keeps_each_tests_latest_run():
    """Post-round 1 fix 13: round 1's arm-a-2 ran Missions with six tests,
    then 9.A alone. Each test now comes from the latest run that included
    it, not only from the last call (which had 9.A alone)."""
    from pathlib import Path

    from evals.agent.score import tool_files

    arm = Path(__file__).parents[1] / "evals/judging/round1/results/arm-a-2"
    rows = tool_files(arm)["nasa.gov/missions"].results()
    run = {t: rows[t][0].source.run_id for t in ("4.C", "4.D", "9.A")}
    assert run["4.C"] == run["4.D"] != run["9.A"]
    assert all(rows[t][0].source.performed for t in ("4.C", "9.A"))


def test_review_reasons_are_told_apart():
    from evals.agent.score import review_reason

    assert (
        review_reason(
            "This test is not finished yet: 2 questions about it are still open."
        )
        == "open question"
    )
    assert (
        review_reason(
            "This test could not be performed: the run reached its time limit"
        )
        == "time limit"
    )
    assert (
        review_reason("This test could not be performed: no spec yet")
        == "could not be performed"
    )
