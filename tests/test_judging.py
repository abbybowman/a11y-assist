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
    assert "| pages scored | 1 of 1 |" in md and "| pages not scored | none |" in md
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


def test_a_finished_page_keeps_every_recording_and_the_lock_hashes_them(
    tmp_path, settings
):
    # 9.A-9.C and 19.A are decided on the other pages' HARs; runs expire.
    run = settings.runs_dir / "r1"
    (run / "evidence" / "pages").mkdir(parents=True)
    for rel in ("report.json", "pre-scrt.json", "evidence/page.har.zip"):
        (run / rel).write_text("x")
    for name in ("p1.har.zip", "p2.har.zip", "live1.har.zip"):
        (run / "evidence" / "pages" / name).write_text(name)
    rd = tmp_path / "round"
    judging._finish(rd, settings, "p01", "r1")
    got = sorted(p.relative_to(rd / "results").as_posix() for p in rd.rglob("*.zip"))
    assert got == [
        "p01/page.har.zip",
        "p01/pages/live1.har.zip",
        "p01/pages/p1.har.zip",
        "p01/pages/p2.har.zip",
    ]
    assert "results/p01/pages/p2.har.zip" in judging._result_files(rd)


async def test_apply_saves_each_page_and_one_bad_file_stops_only_its_page(
    tmp_path, settings, monkeypatch
):
    from types import SimpleNamespace

    import evals.judge_eval as je

    async def fmt():
        return {}

    async def answered(settings, run_id, answers):
        return SimpleNamespace(rejected=[], open_questions=[])

    monkeypatch.setattr(je, "_answer_format", fmt)
    monkeypatch.setattr("a11y_assist.pipeline.answer_questions", answered)
    rd = tmp_path / "round"
    state = {
        pid: {"url": f"https://example.gov/{pid}", "run_id": pid, "round": 1}
        | {"status": "open"}
        for pid in ("p01", "p02")
    }
    rd.mkdir()
    (rd / "state.json").write_text(json.dumps(state))
    for pid, text in (("p01", "{not json"), ("p02", "[]")):
        d = rd / "packets" / pid / "round1"
        d.mkdir(parents=True)
        (d / "answers.json").write_text(text)
    await judging.apply(rd, settings)
    got = json.loads((rd / "state.json").read_text())
    assert got["p01"]["status"] == "open" and "error" in got["p01"]
    assert got["p02"]["status"] == "done"


def test_the_lock_covers_every_file_the_score_reads():
    assert {"evals/judging.py", "src/a11y_assist/catalog.py"} <= set(judging.CODE)
    assert all((judging.REPO / c).is_file() for c in judging.CODE)


def _key_for(rd: Path, location: str) -> Path:
    """An answer key naming `location`, hashed into pages.txt (as a tester
    would hash it) before the lock."""
    data = json.loads(SAMPLE.read_text("utf-8"))
    data[0]["Product"]["P_Location"] = location
    key = rd.parent / "key.json"
    key.write_text(json.dumps(data), encoding="utf-8")
    (rd / "pages.txt").write_text(f"https://example.gov/a {judging.sha256(key)}\n")
    return key


def test_a_key_naming_another_page_is_refused(tmp_path):
    # A hash pasted on the wrong line pairs page A with page B's answers.
    rd = _round(tmp_path)
    key = _key_for(rd, "https://example.gov/b")
    judging.lock(rd)
    (rd / "keys").mkdir()
    shutil.copyfile(key, rd / "keys" / "k.json")
    with pytest.raises(judging.JudgingError, match="names https://example.gov/b"):
        judging.score(rd)


@pytest.mark.parametrize("location", ["example.gov/a/", "https://www.example.gov/a"])
def test_a_key_naming_the_page_any_way_is_scored(tmp_path, location):
    rd = _round(tmp_path)
    key = _key_for(rd, location)
    judging.lock(rd)
    (rd / "keys").mkdir()
    shutil.copyfile(key, rd / "keys" / "k.json")
    assert judging.score(rd)["counts"]["agree"] == 1
    assert "by its hash only" not in (rd / "score.md").read_text()


def test_a_key_naming_no_page_is_scored_by_hash_and_says_so(tmp_path):
    rd = _round(tmp_path)  # the sample SCRT file leaves P_Location blank
    judging.lock(rd)
    _reveal(rd)
    judging.score(rd)
    assert "matched to this page by its hash only" in (rd / "score.md").read_text()


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
    # Every round page on the host (8 here): scans run with no time limit.
    assert len(got) == 8 and "https://www.a.gov/2" not in got


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


def test_a_page_that_could_not_be_tested_shows_in_the_rates(tmp_path):
    rd = _round(tmp_path)
    with (rd / "pages.txt").open("a") as f:
        f.write(f"https://example.gov/b {H1}\n")
    state = json.loads((rd / "state.json").read_text())
    state["p02"] = {
        "url": "https://example.gov/b",
        "status": "error",
        "error": "timeout",
    }
    (rd / "state.json").write_text(json.dumps(state))
    judging.lock(rd)
    _reveal(rd)
    rates = judging.score(rd)["rates"]
    assert rates["pages scored"] == "1 of 2"
    assert rates["pages not scored"] == "p02 (no answer key)"


# ── Scoring a tool file against an answer key (evals/scoring.py) ────────────

from a11y_assist.compare import compare  # noqa: E402
from a11y_assist.scrt import ScrtResult as R  # noqa: E402
from evals.scoring import Verdict, rates, verdict  # noqa: E402
from evals.scoring import score as score_page  # noqa: E402


@pytest.mark.parametrize(
    "key, tool, performed, expected",
    [
        (None, R.PASS, True, Verdict.NOT_SCORED),
        (R.FAIL, None, False, Verdict.NOT_PERFORMED),
        (R.FAIL, None, True, Verdict.NEEDS_REVIEW),
        (R.PASS, R.PASS, True, Verdict.AGREE),
        (R.FAIL, R.PASS, True, Verdict.FALSE_PASS),
        (R.FAIL, R.DNA, True, Verdict.MISSED_FAIL),
        (R.PASS, R.FAIL, True, Verdict.FALSE_FAIL),
        (R.DNA, R.FAIL, True, Verdict.FAIL_NOT_APPLICABLE),
        (R.DNA, R.PASS, True, Verdict.OTHER),
        (R.NOT_TESTED, R.DNA, True, Verdict.OTHER),
    ],
)
def test_verdicts(key, tool, performed, expected):
    assert verdict(key, tool, performed) is expected


def test_scoring_a_tool_file_against_a_persons_file(tmp_path):
    key = scrt.parse(SAMPLE.read_text())
    s = score_page(compare(key, scrt.parse(_candidate(tmp_path))))
    v = {t.test.test_id: t.verdict for t in s.tests}
    assert v["1.A"] is Verdict.FALSE_PASS  # the key fails it, the tool passes it
    assert v["4.A"] is Verdict.AGREE
    assert v["3.A"] is Verdict.NOT_PERFORMED  # the run did not include it
    assert v["4.B"] is Verdict.NOT_SCORED
    assert [t.test.test_id for t in s.disagreements()] == ["1.A"]
    assert rates(s.counts)["false PASS"] == "1"


def test_a_lock_scores_on_a_clone_without_the_ignored_recordings(tmp_path):
    """Post-round 1 fix 20: the lock hashes files git keeps strictly, and
    files it ignores (recordings, kept in an archive) only where present,
    so a round locked on one machine scores on another clone."""
    import subprocess

    def git(*a, cwd):
        subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)

    rd = _round(tmp_path)
    git("init", "-q", cwd=tmp_path)
    (tmp_path / ".gitignore").write_text("*.har.zip\n")
    rec = rd / "results" / "p01" / "page.har.zip"
    rec.write_bytes(b"recording")
    judging.lock(rd)
    lk = json.loads((rd / "results" / "lock.json").read_text())
    assert "results/p01/page.har.zip" in lk["ignored"]
    assert "results/p01/page.har.zip" not in lk["files"]
    _reveal(rd)
    rec.unlink()  # another clone: the archive is not restored
    judging.score(rd)
    rec.write_bytes(b"changed")  # restored, but not the locked copy
    with pytest.raises(judging.JudgingError, match="Archived files that differ"):
        judging.score(rd)
    rec.write_bytes(b"recording")
    (rd / "results" / "p01" / "extra.har.zip").write_bytes(b"new")
    with pytest.raises(judging.JudgingError, match="Archived files that differ"):
        judging.score(rd)
