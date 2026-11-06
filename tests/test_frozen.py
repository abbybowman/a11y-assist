"""Frozen pages (frozen.py): every page a run loads, 19.A's site search
included, recorded once and then replayed from the folder, with the server
down. A URL with no recording is refused, never fetched live."""

from __future__ import annotations

import json

import pytest

from tobi508.models import TestId
from tobi508.pipeline import RunRefused, run_tt_tests

from .conftest import LocalServer
from .drafts import drafts  # noqa: F401 (a fixture)
from .harness import run_tests


async def test_freeze_then_replay_with_the_server_down(settings, drafts, tmp_path):  # noqa: F811
    srv = LocalServer()
    page = f"{srv.base}/19a/t-benefits.html"
    others = [f"{srv.base}/19a/home.html"]
    frozen = settings.model_copy(
        update={
            "frozen_pages_dir": tmp_path / "frozen",
            "frozen_pages_mode": "record_missing",
        }
    )
    try:
        first = await run_tests(frozen, page, ["19.A"], {}, other_pages=others)
    finally:
        srv.stop()
    index = json.loads((tmp_path / "frozen" / "index.json").read_text())
    # The tested page, the other page and the live site search.
    assert page in index and others[0] in index
    assert any("search" in u for u in index), sorted(index)
    assert first["19.A"].outcome.value == "PASS" and "W2" in first["19.A"].rows

    replay = frozen.model_copy(update={"frozen_pages_mode": "replay"})
    again = await run_tests(replay, page, ["19.A"], {}, other_pages=others)
    assert again["19.A"].outcome.value == "PASS"
    assert again["19.A"].rows == first["19.A"].rows  # the search replayed too
    res = await run_tt_tests(replay, page, [TestId.T19A], other_pages=others)
    assert res.report.frozen_pages == "replay"
    assert json.loads((tmp_path / "frozen" / "index.json").read_text()) == index


async def test_a_page_with_no_recording_is_refused(settings, server, tmp_path):
    replay = settings.model_copy(update={"frozen_pages_dir": tmp_path / "frozen"})
    with pytest.raises(RunRefused, match="frozen copies of pages only"):
        await run_tt_tests(replay, f"{server.base}/dyn", [TestId.T4C])
    assert server.hits[("127.0.0.1", "/dyn")] == 0  # nothing fetched live
    assert not (settings.runs_dir.exists() and any(settings.runs_dir.iterdir()))


async def test_an_other_page_with_no_recording_is_refused(settings, server, tmp_path):
    frozen = settings.model_copy(
        update={
            "frozen_pages_dir": tmp_path / "f",
            "frozen_pages_mode": "record_missing",
        }
    )
    await run_tt_tests(frozen, f"{server.base}/dyn", [TestId.T4C])
    replay = frozen.model_copy(update={"frozen_pages_mode": "replay"})
    with pytest.raises(RunRefused, match="Other page 1"):
        await run_tt_tests(
            replay,
            f"{server.base}/dyn",
            [TestId.T9B],
            other_pages=[f"{server.base}/landed"],
        )


async def test_without_the_setting_runs_are_live(settings, server):
    res = await run_tt_tests(settings, f"{server.base}/dyn", [TestId.T4C])
    assert res.report.frozen_pages is None


async def test_tested_frozen_mode(settings, server, drafts, tmp_path):  # noqa: F811
    """The agent eval's mode: the tested page only from the frozen copies;
    other pages of its host, and 19.A's search, recorded live as usual."""
    base = f"{server.base}/19a"
    rec = settings.model_copy(
        update={
            "frozen_pages_dir": tmp_path / "f",
            "frozen_pages_mode": "record_missing",
        }
    )
    for page in ("t-benefits", "home"):  # what freeze.py records: the round's pages
        await run_tt_tests(rec, f"{base}/{page}.html", [TestId.T4C])
    index = json.loads((tmp_path / "f" / "index.json").read_text())
    mode = rec.model_copy(update={"frozen_pages_mode": "tested_frozen"})

    res = await run_tt_tests(
        mode,
        f"{base}/t-benefits.html",
        [TestId.T19A],
        other_pages=[f"{base}/home.html", f"{base}/sitemap.html"],
    )
    rep = res.report
    assert rep.frozen_pages == "tested_frozen"
    assert [(p.url.rsplit("/", 1)[1], p.frozen) for p in rep.other_pages] == [
        ("home.html", True),
        ("sitemap.html", False),  # live: the agent's own route
    ]
    assert json.loads((tmp_path / "f" / "index.json").read_text()) == index
    assert server.hits[("127.0.0.1", "/19a/sitemap.html")] >= 1

    # A tested page that is not frozen is refused, never loaded live.
    before = server.hits[("127.0.0.1", "/19a/sitemap.html")]
    with pytest.raises(RunRefused, match="no recording"):
        await run_tt_tests(mode, f"{base}/sitemap.html", [TestId.T4C])
    assert server.hits[("127.0.0.1", "/19a/sitemap.html")] == before


async def test_tested_frozen_refuses_other_hosts(settings, tmp_path):
    from tobi508.frozen import NotFrozen, obtain

    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "index.json").write_text(
        json.dumps(
            {
                "https://www.example.gov/a": {
                    "url": "https://www.example.gov/a",
                    "final_url": "https://www.example.gov/a",
                    "har": "pages/001.har.zip",
                    "recorded_at": "2026-11-04T00:00:00Z",
                }
            }
        )
    )
    s = settings.model_copy(
        update={"frozen_pages_dir": folder, "frozen_pages_mode": "tested_frozen"}
    )
    with pytest.raises(NotFrozen, match="only from the tested site"):
        await obtain(
            None, s, "https://other.gov/x", tmp_path / "x.har.zip", noop, tested=False
        )


def noop(*a, **k):
    pass


async def test_a_new_recording_never_reuses_a_file_name(settings, server, tmp_path):
    """Round 1: after removing one entry, counting the index named the next
    recording after a page that was still there, and overwrote it."""
    folder = tmp_path / "f"
    rec = settings.model_copy(
        update={"frozen_pages_dir": folder, "frozen_pages_mode": "record_missing"}
    )
    for path in ("/dyn", "/landed"):
        await run_tt_tests(rec, f"{server.base}{path}", [TestId.T4C])
    index = json.loads((folder / "index.json").read_text())
    first = index.pop(f"{server.base}/dyn")
    (folder / first["har"]).unlink()
    (folder / "index.json").write_text(json.dumps(index))
    kept = {u: (folder / e["har"]).read_bytes() for u, e in index.items()}
    await run_tt_tests(rec, f"{server.base}/19a/home.html", [TestId.T4C])
    after = json.loads((folder / "index.json").read_text())
    hars = [e["har"] for e in after.values()]
    assert len(hars) == len(set(hars)) == 2
    assert all((folder / after[u]["har"]).read_bytes() == b for u, b in kept.items())
