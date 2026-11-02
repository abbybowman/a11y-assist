"""Make sample-scrt.json by filling the vendored SCRT in Chromium, the way a
person does: load the TT 5.1.3 template, set a few results, comments,
locations, a global issue, a screenshot and a child issue, then Save.

The file is a test input for the SCRT reader (a real SCRT file, made by SCRT,
not typed by hand). Its expected contents are asserted in
tests/test_scrt.py, never written into the file. Rerun after updating
third_party/scrt:

    uv run python tests/fixtures/scrt/make_sample.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
SCRT = HERE.parents[2] / "third_party" / "scrt"
TEMPLATE = SCRT / "Resources" / "SuccessCriteriaTT5.1.3.json"
PNG = HERE / "shot.png"
OUT = HERE / "sample-scrt.json"

FILL = (
    "(e,v)=>{e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));"
    "e.dispatchEvent(new Event('change',{bubbles:true}))}"
)
HEADER = {
    "#productID": "Sample product",
    "#versionID": "1",
    "#prodDescID": "Sample page for reader tests",
    "#CompanyName": "Example agency",
    "#firstname": "Sam",
    "#lastname": "Tester",
    "#testerContact": "sam@example.gov",
}
# test ID -> (result, comment, location, global)
ROWS = {
    "1.A": ("Fail", 'Says "hello"\nsecond line', "Header logo", "Yes"),
    "2.A": ("Does Not Apply", "", "", None),
    "3.A": ("Not Tested", "", "", None),
    "4.A": ("Pass", "All controls reachable", "", "No"),
}
CHILD = ("1.A", "Fail", "Second failure", "Footer")


async def main() -> None:
    ids = [
        c["TestID"].replace(" ", "")
        for c in json.loads(TEMPLATE.read_text())[0]["Criteria"]
    ]
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(accept_downloads=True)
        page.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
        await page.goto((SCRT / "createReport.html").as_uri())
        await page.set_input_files("#fileinput", str(TEMPLATE))
        await page.click("#button")
        await page.wait_for_selector("select.resultOptions")
        for sel, v in HEADER.items():
            await page.eval_on_selector(sel, FILL, v)
        sels = page.locator("select.resultOptions")

        async def fill_row(i: int, result: str, comment: str, where: str):
            await sels.nth(i).click()  # SCRT shows the screenshot input on click
            await page.keyboard.press("Escape")
            opt = sels.nth(i).locator("option:not([disabled])", has_text=result)
            await sels.nth(i).select_option(element=await opt.first.element_handle())
            if comment:
                await (
                    page.locator("textarea[ng-model='testerCommentID[$index]']")
                    .nth(i)
                    .fill(comment)
                )
            if where:
                await (
                    page.locator("textarea[ng-model='location[$index]']")
                    .nth(i)
                    .fill(where)
                )

        for tid, row in ROWS.items():
            await fill_row(ids.index(tid), *row[:3])
        i = ids.index("1.A")
        await page.locator(f"#fileInput{i}").set_input_files(str(PNG))
        await page.wait_for_timeout(500)
        # Child issue: a new row is added above the parent.
        await page.locator("[ng-click='addIssue($index)']").nth(i).click()
        await page.wait_for_timeout(500)
        # The child is row i + 1 (SCRT inserts it after the parent on screen).
        await fill_row(i + 1, *CHILD[1:])
        # Global issue last: SCRT does not move global choices when a child
        # row is inserted, so one set earlier lands on the row above
        # (docs/solutions/scrt-format.md).
        ids.insert(i + 1, CHILD[0])
        for tid, row in ROWS.items():
            if row[3]:
                await page.locator(f"#glblResult{ids.index(tid)}").select_option(
                    label=row[3]
                )
        async with page.expect_download() as dl:
            await page.click("#sbtBtn")
        await (await dl.value).save_as(OUT)
        await browser.close()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
