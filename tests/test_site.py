"""site.py: the per-page read 9.A-9.C share, and its matching helpers."""

from __future__ import annotations

from tobi508.site import (
    PageRead,
    SiteRead,
    before,
    norm_href,
    pair_in_order,
    read_page,
    repeated_flags,
)

CASES = "WAI/content-assets/wcag-act-rules/testcases"
CH2 = "WAI/content-assets/wcag-act-rules/test-assets/bypass-blocks-cf77f2/chapter2.html"


def _opener(browser, url):
    async def new_page():
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto(url)
        return ctx, page

    return new_page


async def _read(browser, n, url):
    return await read_page(n, url, _opener(browser, url))


async def test_units_regions_and_repetition(browser, act_server):
    main = await _read(
        browser,
        0,
        f"{act_server}/{CASES}/cf77f2/235a899f291a8dbcd536b439728c2af509c8f1d6.html",
    )
    ch2 = await _read(browser, 1, f"{act_server}/{CH2}")
    assert not main.error and not ch2.error
    kinds = [(u.kind, u.role, u.text[:20]) for u in main.units]
    assert kinds[0] == ("control", "link", "skip to main content")
    assert kinds[1][:2] == ("control", "link")
    assert main.units[0].href_attr == "#main" and main.units[0].stop
    aside = next(u for u in main.units if u.text.startswith("the romance"))
    assert aside.regions == ["complementary|#about-book"]
    assert {r.key for r in ch2.regions} >= {
        "navigation|#chapters-navigation",
        "complementary|#about-book",
        "main|@1",
    }
    flags = repeated_flags(SiteRead(pages=[main, ch2]))
    assert [u.text[:12] for u, f in zip(main.units, flags, strict=True) if f] == [
        "the romance "
    ]


def test_helpers():
    page = "https://a.gov/x/page.html"
    assert norm_href("https://a.gov/x/page.html#main", page) == "#main"
    assert norm_href("https://a.gov/about/", page) == "https://a.gov/about"
    assert norm_href("https://a.gov/about#team", page) == "https://a.gov/about"
    assert before([0, 0, 10, 10], [0, 20, 10, 10])  # above
    assert before([0, 0, 10, 10], [20, 0, 10, 10])  # same line, left
    assert not before([20, 0, 10, 10], [0, 0, 10, 10])
    assert not before([0, 0, 0, 0], [0, 20, 10, 10])  # no box: not compared
    assert pair_in_order([("a", 0), ("b", 1), ("a", 2)], [("a", 5), ("a", 7)]) == [
        (0, 5),
        (2, 7),
    ]
    assert SiteRead(pages=[PageRead(n=0, url="", error="X")]).errors == [
        "the tested page could not be read: X"
    ]


def test_other_pages_are_checked_before_anything_runs(settings):
    import pytest

    from tobi508.pipeline import RunRefused, check_other_pages

    url = "http://127.0.0.1:8000/a.html"
    same = "http://127.0.0.1:8000/b.html"
    assert check_other_pages(settings, url, [same, same]) == [same]
    with pytest.raises(RunRefused, match="not allowed"):
        check_other_pages(settings, url, ["https://example.com/b"])
    with pytest.raises(RunRefused, match="same site"):
        settings.allowed_domains = ["127.0.0.1", "localhost"]
        check_other_pages(settings, url, ["http://localhost:8000/b.html"])
    with pytest.raises(RunRefused, match="itself"):
        check_other_pages(settings, url, [url + "#top"])
    six = [f"{same}?{i}" for i in range(6)]
    with pytest.raises(RunRefused, match="At most 5 .*no_time_limit=true"):
        check_other_pages(settings, url, six)
    # The cap keeps a call within its time limit; without the limit, more.
    assert check_other_pages(settings, url, six, no_time_limit=True) == six
    with pytest.raises(RunRefused, match="At most 50"):
        check_other_pages(
            settings, url, [f"{same}?{i}" for i in range(51)], no_time_limit=True
        )
