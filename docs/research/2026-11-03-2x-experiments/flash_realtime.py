# Real-time sampling: how many screenshots per second, and what flash rate does each box appear to have?
import asyncio
import functools
import http.server
import io
import sys
import threading
import time

from PIL import Image
from playwright.async_api import async_playwright


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 8801), functools.partial(H, directory=sys.argv[1])
)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BOX = {"css": 0, "int": 220, "raf": 440, "slow": 660, "gif": 880}


def lum(img, x):
    return sum(img.getpixel((x + 100, 100))) / 765


def flashes(seq):  # count opposing transitions of >= 0.1 between samples, /2
    tr = 0
    last = seq[0]
    for v in seq[1:]:
        if abs(v - last) >= 0.5:
            tr += 1
            last = v
    return tr / 2


async def main():
    async with async_playwright() as p:
        for ch in (None, "chromium"):
            b = await p.chromium.launch(channel=ch)
            pg = await b.new_page(viewport={"width": 1100, "height": 220})
            await pg.goto("http://127.0.0.1:8801/f.html")
            await pg.wait_for_timeout(500)
            for mode in ("screenshot", "screencast"):
                seq = []
                t0 = time.monotonic()
                if mode == "screenshot":
                    while time.monotonic() - t0 < 2:
                        seq.append(
                            Image.open(io.BytesIO(await pg.screenshot())).convert("RGB")
                        )
                else:
                    cdp = await pg.context.new_cdp_session(pg)
                    frames = []
                    import base64

                    async def on(e):
                        frames.append(e["data"])
                        await cdp.send(
                            "Page.screencastFrameAck", {"sessionId": e["sessionId"]}
                        )

                    cdp.on(
                        "Page.screencastFrame", lambda e: asyncio.ensure_future(on(e))
                    )
                    await cdp.send(
                        "Page.startScreencast", {"format": "png", "everyNthFrame": 1}
                    )
                    await asyncio.sleep(2)
                    await cdp.send("Page.stopScreencast")
                    seq = [
                        Image.open(io.BytesIO(base64.b64decode(f))).convert("RGB")
                        for f in frames
                    ]
                fps = len(seq) / 2
                res = {
                    k: flashes([lum(im, x) for im in seq]) / 2 for k, x in BOX.items()
                }
                print(
                    f"{'full' if ch else 'shell':5} {mode:10} {fps:5.1f} fps | apparent flashes/s:",
                    {k: round(v, 1) for k, v in res.items()},
                )
            await b.close()


asyncio.run(main())
