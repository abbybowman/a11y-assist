# Worst case for pass T: a headless page that screenshots every 0.5 s and samples
# animations, nonstop, for the whole duration given.
import asyncio
import sys
import time

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page()
        await pg.goto("file://" + sys.argv[1])
        t0 = time.monotonic()
        n = 0
        while time.monotonic() - t0 < float(sys.argv[2]):
            await pg.screenshot()
            await pg.evaluate("document.getAnimations().length")
            n += 1
            await asyncio.sleep(0.5)
        print("watcher shots:", n)
        await b.close()


asyncio.run(main())
