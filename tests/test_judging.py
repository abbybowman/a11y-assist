"""Judging rounds (evals/judging.py): pages.txt, lock, reveal and score.

Scanning needs live pages and an agent, so it is not run here; these tests
build a finished round by hand and check the commit-and-reveal rules.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from a11y_assist import scrt
from a11y_assist.models import Finding, Outcome, Report, TestId, Versions

from .conftest import FIXTURES

_spec = importlib.util.spec_from_file_location(
    "judging", Path(__file__).resolve().parents[1] / "evals" / "judging.py"
)
judging = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(judging)

SAMPLE = FIXTURES / "scrt" / "sample-scrt.json"
H1 = "a" * 64


def test_pages_txt_lines():
    text = f"""# round 1, tested live 2026-11-02

https://www.example.gov/a  {H1}
{"B" * 64} https://www.example.gov/b
"""
    assert judging.parse_pages(text) == [
        ("https://www.example.gov/a", H1),
        ("https://www.example.gov/b", "b" * 64),
    ]


@pytest.mark.parametrize(
    "text, message",
    [
        ("", "no pages"),
        ("https://example.gov/a", "one URL and one SHA-256"),
        (f"https://example.gov/a {H1} extra", "one URL and one SHA-256"),
        (f"example.gov/a {H1}", "one URL and one SHA-256"),
        (f"https://example.gov/a {H1[:-1]}", "one URL and one SHA-256"),
        (f"https://example.gov/a {H1}\nhttps://example.gov/a {H1}", "listed twice"),
    ],
)
def test_bad_pages_txt(text, message):
    with pytest.raises(judging.JudgingError, match=message):
        judging.parse_pages(text)


def _candidate(tmp_path: Path) -> str:
    t = datetime(2026, 11, 2, tzinfo=timezone.utc)
    report = Report(
        run_id="r1",
        target="https://example.gov/a",
        started_at=t,
        versions=Versions(
            a11y_assist="0",
            andi="1",
            jquery="1",
            playwright="1",
            browser_channel="chromium",
            browser=None,
            os="t",
            python="3",
            rules_spec={},
            judging_model="none",
        ),
        findings=[
            Finding(test_id=TestId.T1A, test_name="x", outcome=Outcome.PASS),
            Finding(test_id=TestId.T4A, test_name="x", outcome=Outcome.PASS),
        ],
        evidence_dir="evidence",
    )
    return scrt.dump(scrt.from_report(report, tmp_path))


def _round(tmp_path: Path) -> Path:
    """A finished round: one page, its result, no answer key yet."""
    rd = tmp_path / "round-1"
    (rd / "results" / "p01").mkdir(parents=True)
    (rd / "pages.txt").write_text(f"https://example.gov/a {judging.sha256(SAMPLE)}\n")
    (rd / "results" / "p01" / "pre-scrt.json").write_text(_candidate(tmp_path))
    (rd / "state.json").write_text(
        json.dumps(
            {
                "p01": {
                    "url": "https://example.gov/a",
                    "status": "done",
                    "scanned_at": "2026-11-02T20:00:00+00:00",
                }
            }
        )
    )
    return rd


def _reveal(rd: Path) -> None:
    (rd / "keys").mkdir(exist_ok=True)
    shutil.copyfile(SAMPLE, rd / "keys" / "tester-file.json")


def test_lock_then_reveal_then_score(tmp_path):
    rd = _round(tmp_path)
    with pytest.raises(judging.JudgingError, match="Not locked"):
        judging.score(rd)
    judging.lock(rd)
    _reveal(rd)
    out = judging.score(rd)
    # The sample fails 1.A, passes 4.A, and answers 2.A and 3.A, which the
    # run did not perform.
    assert out["counts"]["false_pass"] == 1 and out["counts"]["agree"] == 1
    assert out["counts"]["not_performed"] == 2
    [page] = out["pages"]
    assert [d["test_id"] for d in page["disagreements"]] == ["1.A"]
    md = (rd / "score.md").read_text()
    assert "| false PASS | 1 |" in md and "not a certified" in md
    assert "Scanned 2026-11-02" in md


def test_lock_refuses_answer_keys_or_open_pages(tmp_path):
    rd = _round(tmp_path)
    _reveal(rd)
    with pytest.raises(judging.JudgingError, match="before the reveal"):
        judging.lock(rd)
    shutil.rmtree(rd / "keys")
    (rd / "state.json").write_text(json.dumps({"p01": {"status": "open"}}))
    with pytest.raises(judging.JudgingError, match="Not every page"):
        judging.lock(rd)


@pytest.mark.parametrize("tamper", ["result", "pages", "stray_key", "code"])
def test_score_refuses_changes_after_the_lock(tmp_path, tamper, monkeypatch):
    rd = _round(tmp_path)
    judging.lock(rd)
    _reveal(rd)
    if tamper == "result":
        f = rd / "results" / "p01" / "pre-scrt.json"
        f.write_text(f.read_text().replace('"Pass"', '"Fail"', 1))
        message = "Result files changed"
    elif tamper == "pages":
        (rd / "pages.txt").write_text(
            f"https://example.gov/b {judging.sha256(SAMPLE)}\n"
        )
        message = "pages.txt changed"
    elif tamper == "stray_key":
        (rd / "keys" / "other.json").write_text("[]")
        message = "match no page"
    else:
        lk = rd / "results" / "lock.json"
        data = json.loads(lk.read_text())
        data["code"]["src/a11y_assist/compare.py"] = "0" * 64
        lk.write_text(json.dumps(data))
        # lock.json is outside the hashed files; the code hash is checked.
        message = "Comparison code changed"
    with pytest.raises(judging.JudgingError, match=message):
        judging.score(rd)


def test_other_pages_are_the_rounds_pages_on_the_same_host():
    listed = [
        "https://www.a.gov/1",
        "https://www.b.gov/1",
        "https://www.a.gov/2",
        *[f"https://www.a.gov/{n}" for n in range(3, 10)],
    ]
    assert judging.other_pages("https://www.b.gov/1", listed) == []
    got = judging.other_pages("https://www.a.gov/2", listed)
    assert got[:2] == ["https://www.a.gov/1", "https://www.a.gov/3"]
    assert len(got) == 5 and "https://www.a.gov/2" not in got


async def test_scan_runs_each_page_and_files_its_results(tmp_path, settings, server):
    rd = tmp_path / "round-x"
    rd.mkdir()
    (rd / "pages.txt").write_text(f"{server.base}/no_trap.html {H1}\n")
    await judging.scan(rd, settings)
    state = json.loads((rd / "state.json").read_text())
    p = state["p01"]
    assert p["status"] in ("open", "done") and p["other_pages"] == []
    if p["status"] == "open":  # questions go to a packet, never answered here
        q = json.loads(
            (rd / "packets" / "p01" / "round1" / "questions.json").read_text()
        )
        assert q["questions"] and "answer_format" in q
    else:
        assert (rd / "results" / "p01" / "pre-scrt.json").is_file()
