import asyncio
import io
import os
import sys

from PIL import Image, ImageChops
from playwright.async_api import async_playwright

sys.argv = [sys.argv[0], sys.argv[1], "/dev/null"]
exec(
    open(os.path.join(os.path.dirname(__file__), "iframe_media.py"))
    .read()
    .split("MEDIA=")[0]
)


async def diff_in_iframe(pg, box):
    a = Image.open(io.BytesIO(await pg.screenshot())).convert("RGB")
    await pg.wait_for_timeout(1200)
    b = Image.open(io.BytesIO(await pg.screenshot())).convert("RGB")
    crop = tuple(
        int(v)
        for v in (box["x"], box["y"], box["x"] + box["width"], box["y"] + box["height"])
    )
    return ImageChops.difference(a.crop(crop), b.crop(crop)).getbbox() is not None


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            channel="chromium", args=["--autoplay-policy=no-user-gesture-required"]
        )
        c = await b.new_context()
        pg = await c.new_page()
        await pg.goto("http://127.0.0.1:8780/top2.html")
        await pg.wait_for_timeout(1500)
        fr = pg.frames[1]
        s = await c.new_cdp_session(fr)
        print("iframe out-of-process:", True)
        box = await pg.locator("#f1").bounding_box()
        print(
            "pixels change inside iframe (video+marquee):",
            await diff_in_iframe(pg, box),
        )
        path = []
        for i in range(6):
            await pg.keyboard.press("Tab")
            inner = await fr.evaluate(
                "document.activeElement && document.activeElement.id"
            )
            top = await pg.evaluate(
                "document.activeElement.tagName+':'+(document.activeElement.textContent||document.activeElement.title||'').trim().slice(0,12)"
            )
            path.append(top if top.split(":")[0] != "IFRAME" else f"iframe>{inner}")
            if inner == "p":
                break
        print("Tab path:", path)
        await pg.keyboard.press("Enter")
        await pg.wait_for_timeout(300)
        print(
            "after Enter on Pause: video paused =",
            await fr.evaluate("document.getElementById('v').paused"),
        )
        await b.close()


asyncio.run(main())
