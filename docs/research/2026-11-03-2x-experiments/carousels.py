import asyncio
import functools
import hashlib
import http.server
import os
import sys
import threading

from playwright.async_api import async_playwright


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 8790), functools.partial(H, directory=sys.argv[1])
)
threading.Thread(target=srv.serve_forever, daemon=True).start()


async def changes(pg, secs):
    """Distinct-content changes of the carousel box over secs (sampled every 150 ms)."""
    el = pg.locator("#c")
    last = None
    n = 0
    for _ in range(int(secs / 0.15)):
        h = hashlib.md5(await el.screenshot(animations="allow")).hexdigest()
        if last and h != last:
            n += 1
        last = h
        await asyncio.sleep(0.15)
    return n


async def inside(pg):
    return await pg.evaluate("!!document.activeElement.closest('#c')")


async def one(b, lib):
    c = await b.new_context()
    pg = await c.new_page()
    await pg.goto(f"http://127.0.0.1:8790/{lib}.html")
    await pg.wait_for_timeout(1500)
    r = {"idle": await changes(pg, 4.5)}
    for i in range(12):
        await pg.keyboard.press("Tab")
        if await inside(pg):
            break
    r["focus_on"] = (
        await pg.evaluate(
            "(document.activeElement.textContent||document.activeElement.getAttribute('aria-label')||document.activeElement.className).trim().slice(0,22)"
        )
        if await inside(pg)
        else None
    )
    r["focused_in"] = await changes(pg, 4.5)
    for i in range(12):
        await pg.keyboard.press("Tab")
        if not await inside(pg):
            break
    r["focus_left"] = await changes(pg, 4.5)
    box = await pg.locator("#c").bounding_box()
    await pg.mouse.move(box["x"] + 50, box["y"] + 40)
    r["hover"] = await changes(pg, 4.5)
    await c.close()
    return r


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            proxy={"server": os.environ["HTTPS_PROXY"], "bypass": "127.0.0.1,localhost"}
        )
        for lib in ["slick", "swiper", "splide", "bootstrap", "glide", "flickity"]:
            try:
                print(lib, await one(b, lib))
            except Exception as e:
                print(lib, "ERR", str(e)[:100])
        await b.close()


asyncio.run(main())
