"""19.A (2.4.5) on a small custom site (tests/fixtures/19a/): no ACT rule,
DHS verdict or Baseline Alignment case covers it. Each case is a tested page
plus the other pages given; the fixture server answers the site search
(search.html for any query; search-empty.html finds nothing). Expected
outcomes and scripted answers live here, never in a page."""

from __future__ import annotations

import pytest

from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import run_tests

# case -> (tested page, other pages, expected outcome, rows, answers)
EXPECTED: dict[str, tuple[str, list[str], str, list[str], dict]] = {
    "nav-and-site-map": ("t-benefits", ["home", "sitemap"], "PASS", ["W1", "G2"], {}),
    "nav-and-related-link": (
        "t-benefits",
        ["home", "related"],
        "PASS",
        ["W1", "G2"],
        {},
    ),
    "nav-and-live-search": ("t-benefits", ["home"], "PASS", ["W1", "W2", "G2"], {}),
    "search-finds-nothing": (
        "t2-status",
        ["home"],
        "NEEDS_REVIEW",
        ["W1", "W3", "G3"],
        {},
    ),
    "search-finds-nothing-site-map-given": (
        "t2-status",
        ["home", "sitemap"],
        "PASS",
        ["W1", "G2"],
        {},
    ),
    "one-way-nothing-else": ("t3-forms", ["home2"], "FAIL", ["W1", "G4"], {}),
    "contact-form-not-process": (
        "contact",
        ["home", "sitemap"],
        "PASS",
        ["W1", "G2"],
        {"J1": {"choice": "not_process"}},
    ),
    "process-step": (
        "step2",
        ["home"],
        "DNA",
        ["A3", "G1"],
        {"J1": {"choice": "process"}},
    ),
}


@pytest.mark.parametrize("case", sorted(EXPECTED))
async def test_case(case, settings, server, drafts):  # noqa: F811
    page, others, outcome, rows, answers = EXPECTED[case]
    got = await run_tests(
        settings,
        f"{server.base}/19a/{page}.html",
        ["19.A"],
        {"19.A": answers},
        other_pages=[f"{server.base}/19a/{o}.html" for o in others],
    )
    f = got["19.A"]
    assert f.outcome.value == outcome, (f.rows, f.summary, f.rationale)
    assert [r for r in f.rows if r != "A5"] == rows, f.rows
    if case == "search-finds-nothing":
        assert "sitemap.html" in f.summary  # suggested, never visited


async def test_without_other_pages_nothing_runs(settings, server, drafts):  # noqa: F811
    got = await run_tests(settings, f"{server.base}/19a/t-benefits.html", ["19.A"], {})
    f = got["19.A"]
    assert f.outcome.value == "NEEDS_REVIEW" and f.rows == ["A1", "G1"]


def test_template_links_are_navigation_only():
    """19.A 1.1.0 (Abby, 2026-11-02): on a results page or a site map page,
    the shared menus, header and footer link to T whatever the search found
    or the site map lists. Built evidence: no fixture page has that template."""
    from a11y_assist.checks.t19a import _kind, results_link_to
    from a11y_assist.site import PageRead, Unit

    t = "https://example.gov/apply.html"

    def link(region_role):
        return Unit(
            i=0,
            kind="control",
            role="link",
            text="apply",
            name="Apply",
            css="a",
            href=t,
            region_role=region_role,
        )

    menu_only = PageRead(
        n=101, url="https://example.gov/search", units=[link("navigation")]
    )
    assert not results_link_to(menu_only, t)  # "No results", menu link only
    hit = PageRead(
        n=101, url="https://example.gov/search", units=[link(""), link("navigation")]
    )
    assert results_link_to(hit, t)
    site_map = PageRead(n=2, url="https://example.gov/sitemap.html", units=[])
    assert _kind(link("banner"), site_map, {2}) == "navigation"
    assert _kind(link(""), site_map, {2}) == "site_map"


def test_live_search_url_drops_the_action_query():
    """A GET submission replaces the action's own query (spec Terms)."""
    from a11y_assist.checks.t19a import search_url

    form = {
        "method": "get",
        "field": "q",
        "action": "https://example.gov/s?x=1",
        "hidden": {"site": "main"},
    }
    assert search_url(form, "Apply") == "https://example.gov/s?site=main&q=Apply"
