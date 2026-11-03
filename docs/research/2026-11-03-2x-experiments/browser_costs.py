import asyncio
import pathlib
import statistics
import time

from playwright.async_api import async_playwright

PAGE = (
    pathlib.Path(__file__).resolve().parents[3]
    / "tests/fixtures/budget/agency-home.html"
).as_uri()


async def main():
    async with async_playwright() as p:
        for ch in (None, "chromium"):
            launches = []
            for _ in range(5):
                t = time.monotonic()
                b = await p.chromium.launch(channel=ch)
                launches.append(time.monotonic() - t)
                await b.close()
            b = await p.chromium.launch(channel=ch)
            loads = []
            presses = []
            for _ in range(15):
                t = time.monotonic()
                c = await b.new_context()
                pg = await c.new_page()
                await pg.goto(PAGE)
                loads.append(time.monotonic() - t)
                t = time.monotonic()
                for _ in range(20):
                    await pg.keyboard.press("Tab")
                presses.append((time.monotonic() - t) / 20)
                await c.close()
            await b.close()
            print(
                f"{'full' if ch else 'shell':5}  launch {statistics.median(launches) * 1000:4.0f} ms   context+page+load {statistics.median(loads) * 1000:4.0f} ms   Tab press {statistics.median(presses) * 1000:4.1f} ms"
            )


asyncio.run(main())
