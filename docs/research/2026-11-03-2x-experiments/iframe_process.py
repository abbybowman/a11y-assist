import asyncio
import collections
import os
import sys

from playwright.async_api import async_playwright

sys.argv = [sys.argv[0], sys.argv[1], "/dev/null"]
exec(
    open(os.path.join(os.path.dirname(__file__), "iframe_media.py"))
    .read()
    .split("MEDIA=")[0]
)  # reuse the server


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            channel=os.environ.get("CH") or None,
            args=["--autoplay-policy=no-user-gesture-required"],
            proxy={
                "server": os.environ["HTTPS_PROXY"],
                "bypass": "127.0.0.1,localhost",
            },
        )
        c = await b.new_context()
        pg = await c.new_page()
        await pg.goto("http://127.0.0.1:8780/top.html")
        await pg.wait_for_timeout(4000)
        bs = await b.new_browser_cdp_session()
        tg = await bs.send("Target.getTargets")
        print(
            "browser-level targets:",
            collections.Counter(t["type"] for t in tg["targetInfos"]),
        )
        for fr in pg.frames[1:]:
            try:
                s = await c.new_cdp_session(fr)
                ev = []
                s.on(
                    "Media.playersCreated",
                    lambda e, ev=ev: ev.append(len(e["players"])),
                )
                await s.send("Media.enable")
                await pg.wait_for_timeout(500)
                print(
                    "OOPIF (own session):",
                    fr.url[:45],
                    "| Media players reported on its own session:",
                    ev,
                )
            except Exception as ex:
                print("in-process:", fr.url[:45], str(ex)[:70])
        await b.close()


asyncio.run(main())
