# Record a page with cross-site iframes in the headless shell; replay the same
# HAR in full Chromium. Does the replay work, with out-of-process iframes?
import asyncio
import os
import sys

from playwright.async_api import async_playwright

sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2]]
exec(
    open(os.path.join(os.path.dirname(__file__), "iframe_media.py"))
    .read()
    .split("MEDIA=")[0]
)


async def main():
    async with async_playwright() as p:
        shell = await p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        c = await shell.new_context(record_har_path=HAR, record_har_mode="full")
        pg = await c.new_page()
        await pg.goto("http://127.0.0.1:8780/top2.html")
        await pg.wait_for_timeout(2000)
        top = pg.url.split("/")[2].split(":")[0]
        cross = [
            f.url for f in pg.frames[1:] if f.url.split("/")[2].split(":")[0] != top
        ]
        print("recorded in shell; cross-site frames seen while recording:", cross)
        await c.close()
        await shell.close()
        full = await p.chromium.launch(
            channel="chromium", args=["--autoplay-policy=no-user-gesture-required"]
        )
        c = await full.new_context()
        await c.route_from_har(HAR, not_found="abort")
        pg = await c.new_page()
        failed = []
        pg.on("requestfailed", lambda r: failed.append(r.url))
        await pg.goto("http://127.0.0.1:8780/top2.html")
        await pg.wait_for_timeout(2000)
        oop = []
        for f in pg.frames[1:]:
            try:
                await c.new_cdp_session(f)
                oop.append(True)
            except Exception:
                oop.append(False)
        media = await pg.frames[1].evaluate(
            "(()=>{const v=document.getElementById('v');return {paused:v.paused,t:+v.currentTime.toFixed(1),err:v.error&&v.error.code}})()"
        )
        await pg.keyboard.press("Tab")
        await pg.keyboard.press("Tab")
        await pg.keyboard.press("Enter")
        await pg.wait_for_timeout(200)
        paused = await pg.frames[1].evaluate("document.getElementById('v').paused")
        print(
            "replayed in full: out-of-process:",
            oop,
            "| iframe video:",
            media,
            "| Tab,Tab,Enter paused it:",
            paused,
            "| failed requests:",
            failed,
        )
        await full.close()


asyncio.run(main())
