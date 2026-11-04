"""Frozen pages (frozen.py): every page a run loads, 19.A's site search
included, recorded once and then replayed from the folder, with the server
down. A URL with no recording is refused, never fetched live."""

from __future__ import annotations

import json

import pytest

from a11y_assist.models import TestId
from a11y_assist.pipeline import RunRefused, run_tt_tests

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
