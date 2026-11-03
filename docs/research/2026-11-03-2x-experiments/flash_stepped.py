# Deterministic capture: Playwright's clock (timers, rAF, Date) plus paused Web
# Animations set to each frame's time; one screenshot per 1/60 s step.
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
    ("127.0.0.1", 8802), functools.partial(H, directory=sys.argv[1])
)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BOX = {"css": 0, "int": 220, "raf": 440, "slow": 660, "gif": 880}


def lum(img, x):
    return sum(img.getpixel((x + 100, 100))) / 765


def flashes(seq):
    tr = 0
    last = seq[0]
    for v in seq[1:]:
        if abs(v - last) >= 0.5:
            tr += 1
            last = v
    return tr / 2


STEP = 1000 / 60
STEP_MS = 17


async def main():
    async with async_playwright() as p:
        for ch in (None, "chromium"):
            b = await p.chromium.launch(channel=ch)
            c = await b.new_context(viewport={"width": 1100, "height": 220})
            pg = await c.new_page()
            await pg.clock.install(time=1_000_000)
            await pg.clock.pause_at(1_000_100)
            await pg.goto("http://127.0.0.1:8802/f.html")
            await pg.clock.run_for(100)
            await pg.evaluate(
                "window.__t0=document.timeline.currentTime; for (const a of document.getAnimations()) a.pause()"
            )
            seq = []
            t0 = time.monotonic()
            n = 120
            for k in range(n):
                await pg.clock.run_for(STEP_MS)
                await pg.evaluate(
                    "(t)=>{for (const a of document.getAnimations()) a.currentTime=t}",
                    k * STEP_MS,
                )
                seq.append(Image.open(io.BytesIO(await pg.screenshot())).convert("RGB"))
            wall = time.monotonic() - t0
            res = {
                k: flashes([lum(im, x) for im in seq]) / (n * STEP_MS / 1000)
                for k, x in BOX.items()
            }
            print(
                f"{'full' if ch else 'shell':5} stepped {n} frames (about 2 s of page time, 17 ms steps) in {wall:.1f} s wall | flashes/s:",
                {k: round(v, 2) for k, v in res.items()},
            )
            g = await pg.evaluate("""async()=>{const r=await fetch('flash5.gif');const d=new ImageDecoder({data:r.body,type:'image/gif'});await d.tracks.ready;const t=d.tracks.selectedTrack;const out=[];
              for(let i=0;i<t.frameCount;i++){const f=(await d.decode({frameIndex:i})).image;const c=new OffscreenCanvas(f.displayWidth,f.displayHeight);const x=c.getContext('2d');x.drawImage(f,0,0);const p=x.getImageData(50,50,1,1).data;out.push([f.duration/1000,(p[0]+p[1]+p[2])/765])}return {frames:out.slice(0,6),count:t.frameCount,loops:t.repetitionCount}}""")
            print("   GIF decoded:", g)
            await b.close()


asyncio.run(main())
