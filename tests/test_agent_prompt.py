"""The agent eval's task prompt (evals/agent/prompt.py): criteria from the
built tests, WCAG 2.0 only, a scope for every partly covered criterion."""

from __future__ import annotations

from evals.agent.prompt import SCOPE, criteria, task


def test_criteria_follow_the_built_tests():
    cs = {c["id"]: c for c in criteria()}
    assert cs["2.1.1"]["tests"] == ["4.A", "4.B"] and cs["2.1.1"]["full"]
    assert not cs["1.3.1"]["full"] and cs["1.3.1"]["tests"] == ["5.C"]
    # Every partly covered criterion has a written scope, and only those.
    assert {i for i, c in cs.items() if not c["full"]} == set(SCOPE)


def test_task_names_wcag_20_and_every_page():
    urls = ["https://www.example.gov/a", "https://www.example.gov/b"]
    t = task(urls)
    assert "WCAG 2.0" in t and "do not apply WCAG 2.1 or 2.2" in t
    assert all(u in t for u in urls)
    for c in criteria():
        assert c["label"] in t
    assert "Understanding" not in t and "w3.org" not in t  # no 2.2 links
    assert "Trusted Tester" not in t and "4.C" not in t  # no TT procedure
