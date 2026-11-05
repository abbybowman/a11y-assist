"""evals/agent/per_test.py on round 1's locked files: per-test counts
that the README's table shows, from the scorer's own verdicts."""

from __future__ import annotations

from a11y_assist.config import REPO_ROOT
from evals.agent.per_test import per_test

R1 = REPO_ROOT / "evals/judging/round1"


def test_round1_per_test_counts():
    runs = [[R1 / "results" / a] for a in ("arm-a-1", "arm-a-2", "arm-a-3")]
    got = per_test(R1, runs)
    # 8 + 8 + 8 page-runs: A-1 was not given the search page, A-2's copy is
    # in not_scored.json, A-3's tool never ran Missions.
    assert all(sum(c.values()) == 24 for c in got.values())
    assert sum(c["false_pass"] for c in got.values()) == 0
    assert got["9.B"]["agree"] == 24
    # The locked score has 7 false FAILs; merging A-2's split Missions call
    # adds its 4.D.
    assert sum(c["false_fail"] for c in got.values()) == 8
