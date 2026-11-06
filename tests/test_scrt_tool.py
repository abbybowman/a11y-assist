"""SCRT files in the real SCRT (vendored, offline) and the tools end to end.

The SCRT tests check DHS's tool, not ours: what it loads and what its Save
keeps. They pin the behaviour docs/solutions/scrt-format.md describes.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from fastmcp import Client
from playwright.async_api import async_playwright

from tobi508 import config, scrt
from tobi508.app import mcp

from .conftest import FIXTURES

SCRT_DIR = Path(__file__).resolve().parents[1] / "third_party" / "scrt"
TEMPLATE = SCRT_DIR / "Resources" / "SuccessCriteriaTT5.1.3.json"
SAMPLE = FIXTURES / "scrt" / "sample-scrt.json"
SHOT = FIXTURES / "scrt" / "shot.png"
FILL = "(e,v)=>{e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}))}"


async def _scrt_page(pw, file: Path):
    browser = await pw.chromium.launch()
    page = await browser.new_page(accept_downloads=True)
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
    await page.goto((SCRT_DIR / "createReport.html").as_uri())
    await page.set_input_files("#fileinput", str(file))
    await page.click("#button")
    await page.wait_for_timeout(1000)
    return browser, page, errors


async def test_scrt_loads_its_files_but_not_pre_scrt(tmp_path):
    pre = tmp_path / "page.pre-scrt.json"
    pre.write_text(scrt.dump(scrt.PreScrt()))
    async with async_playwright() as pw:
        for file, rows in ((TEMPLATE, 61), (SAMPLE, 62), (pre, 0)):
            browser, page, errors = await _scrt_page(pw, file)
            assert await page.locator("select.resultOptions").count() == rows
            if rows == 0:  # SCRT reads jsonData[0].Product and stops
                assert any("Product" in e for e in errors), errors
            await browser.close()


async def test_scrt_save_drops_a_row_set_back_to_no_selection(tmp_path):
    """A screenshot stays on a row with no result chosen, but a row whose
    result is set back to "No Selection" is left out of the saved file with
    its screenshot (createReport.js skips it)."""
    async with async_playwright() as pw:
        browser, page, _ = await _scrt_page(pw, TEMPLATE)
        for sel, v in [
            ("#productID", "P"),
            ("#versionID", "1"),
            ("#prodDescID", "d"),
            ("#CompanyName", "c"),
            ("#firstname", "f"),
            ("#lastname", "l"),
            ("#testerContact", "e@example.gov"),
        ]:
            await page.eval_on_selector(sel, FILL, v)
        sels = page.locator("select.resultOptions")

        async def choose(i: int, label: str) -> None:
            opt = sels.nth(i).locator("option:not([disabled])", has_text=label)
            await sels.nth(i).select_option(element=await opt.first.element_handle())

        # Row 1 (1.B): Pass and a screenshot, then back to No Selection.
        # Row 0 (1.A): a screenshot and no result. A click on a row's result
        # list shows its screenshot input (SCRT hides it again for a row with
        # no result when another row is clicked, so row 0 goes last).
        for i in (1, 0):
            await sels.nth(i).click()
            await page.keyboard.press("Escape")
            if i == 1:
                await choose(1, "Pass")
            await page.locator(f"#fileInput{i}").set_input_files(str(SHOT))
            await page.wait_for_timeout(300)
        await sels.nth(1).click()
        await page.keyboard.press("Escape")
        await choose(1, "No Selection")
        async with page.expect_download() as dl:
            await page.click("#sbtBtn")
        out = tmp_path / "saved.json"
        await (await dl.value).save_as(out)
        await browser.close()
    rows = scrt.parse(out.read_text()).results()
    assert rows["1.A"][0].TestResult is None and rows["1.A"][0].ImageSrc
    assert "1.B" not in rows and len(rows) == 60


# ── Tools end to end ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _use_test_settings(settings, monkeypatch):
    monkeypatch.setattr(config, "settings", settings)


async def _call(client: Client, name: str, args: dict):
    return await client.call_tool(name, args, raise_on_error=False)


async def test_a_run_writes_a_pre_scrt_file_the_reader_reads(settings, server):
    async with Client(mcp) as client:
        res = await _call(
            client,
            "tobi_run_tt_tests",
            {"url": f"{server.base}/no_trap.html", "tests": ["4.C"]},
        )
        out = json.loads(res.content[0].text)
        assert out["pre_scrt_uri"] == f"run://{out['run_id']}/pre-scrt.json"
        [content] = await client.read_resource(out["pre_scrt_uri"])
        doc = scrt.parse(content.text)
        assert doc.runs[0].run_id == out["run_id"]
        [row] = doc.results()["4.C"]
        assert row.TestResult is scrt.ScrtResult.PASS  # the spec's outcome
        assert row.source.rows == ["A3", "G4"]

        res = await _call(
            client,
            "tobi_read_report",
            # The run's own file by its link: no need to send it back.
            {"content": out["pre_scrt_uri"], "compare_to": SAMPLE.read_text()},
        )
        assert not res.is_error
        read = json.loads(res.content[0].text)
    assert read["format"] == "pre-scrt" and "NOT a certified" in read["disclaimer"]
    assert read["counts"]["Pass"] == 1 and read["counts"]["needs_review"] == 60
    assert read["tester_named"] is False
    cmp = read["comparison"]
    assert cmp["same_page"] is False  # the sample has no page URL
    # The sample answers 1.A-4.A; the run performed only 4.C. The comparison
    # lists what changed and never calls either file wrong.
    assert cmp["counts"]["only_first"] == 4 and cmp["counts"]["only_second"] == 1
    assert [(c["test_id"], c["compare_to"], c["content"]) for c in cmp["changes"]][
        -1
    ] == ("4.C", "blank", "Pass")
    assert "false" not in json.dumps(cmp["counts"]) + json.dumps(cmp["changes"])


async def test_read_report_takes_a_local_path_only_in_dev_mode(settings):
    async with Client(mcp) as client:
        local = await _call(client, "tobi_read_report", {"content": str(SAMPLE)})
        settings.dev_mode = False
        refused = await _call(client, "tobi_read_report", {"content": str(SAMPLE)})
        gone = await _call(
            client,
            "tobi_read_report",
            {"content": SAMPLE.read_text(), "compare_to": "run://nope/pre-scrt.json"},
        )
    assert json.loads(local.content[0].text)["format"] == "scrt"
    assert refused.is_error and "DEV_MODE" in refused.content[0].text
    # The error names the argument that was wrong.
    assert gone.is_error and gone.content[0].text.startswith("compare_to:")


async def test_read_report_of_a_tt_file_and_bad_input():
    async with Client(mcp) as client:
        res = await _call(client, "tobi_read_report", {"content": SAMPLE.read_text()})
        read = json.loads(res.content[0].text)
        bad = await _call(client, "tobi_read_report", {"content": "[1, 2]"})
    assert read["format"] == "scrt" and read["tester_named"] is True
    assert [f["test_id"] for f in read["failures"]] == ["1.A"]
    assert (
        read["failures"][0]["rows"] == 2
        and read["failures"][0]["global_issue"] == "Yes"
    )
    assert read["comparison"] is None
    assert bad.is_error and "Not an SCRT or pre-SCRT file" in bad.content[0].text
