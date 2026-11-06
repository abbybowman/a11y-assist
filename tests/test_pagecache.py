"""Other pages recorded and read once per server session (pagecache.py;
Abby, 2026-11-06). The tests' own settings turn the cache off; these turn it
on for themselves."""

from __future__ import annotations

from a11y_assist import pagecache
from a11y_assist.models import TestId
from a11y_assist.pipeline import run_tt_tests

from .drafts import drafts  # noqa: F401 (a fixture)


async def test_an_other_page_is_recorded_and_read_once_per_session(
    settings,
    server,
    drafts,  # noqa: F811
):
    s = settings.model_copy(update={"page_cache_s": 1800})
    pagecache.clear()
    try:
        other = f"{server.base}/9x/a2-benefits.html"
        path = ("127.0.0.1", "/9x/a2-benefits.html")
        first = await run_tt_tests(
            s,
            f"{server.base}/9x/a1-home.html",
            [TestId.T9B, TestId.T9C],
            other_pages=[other],
        )
        loads = server.hits[path]
        assert loads >= 1 and first.report.other_pages[0].reused_from is None
        second = await run_tt_tests(
            s,
            f"{server.base}/9x/a3-nav-reordered.html",
            [TestId.T9C],
            other_pages=[other],
        )
        # Not requested again: the recording was copied into the new run.
        assert server.hits[path] == loads
        page = second.report.other_pages[0]
        assert page.reused_from is not None
        run_dir = s.runs_dir / second.run_id
        assert (run_dir / page.har).is_file()  # the run keeps its own copy
        assert pagecache.sha256(run_dir / page.har) == pagecache.sha256(
            s.runs_dir / first.run_id / first.report.other_pages[0].har
        )
        # The reads of that recording were kept too.
        sha = pagecache.sha256(run_dir / page.har)
        assert pagecache.read("site", sha) is not None
        assert pagecache.read("andi", sha) is not None
        # Same finding either way for the page compared.
        assert first.report.findings[0].outcome is not None
    finally:
        pagecache.clear()


async def test_the_cache_is_off_when_its_time_is_zero(settings, server, drafts):  # noqa: F811
    pagecache.clear()
    other = f"{server.base}/9x/a2-benefits.html"
    for page in ("a1-home", "a3-nav-reordered"):
        out = await run_tt_tests(
            settings, f"{server.base}/9x/{page}.html", [TestId.T9B], other_pages=[other]
        )
        assert out.report.other_pages[0].reused_from is None
