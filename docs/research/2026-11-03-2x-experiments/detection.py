import asyncio
import functools
import http.server
import io
import sys
import threading
import time

from PIL import Image, ImageChops
from playwright.async_api import async_playwright


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 8795), functools.partial(H, directory=sys.argv[1])
)
threading.Thread(target=srv.serve_forever, daemon=True).start()
HOOK = """(()=>{const log={timers:[],audio:0,muts:{}};Object.defineProperty(window,'__t',{value:log});
const si=window.setInterval;window.setInterval=function(f,ms,...a){log.timers.push(['interval',ms|0]);return si.call(this,f,ms,...a)};
const st=window.setTimeout;window.setTimeout=function(f,ms,...a){if((ms|0)>=1000)log.timers.push(['timeout',ms|0]);return st.call(this,f,ms,...a)};
const cn=AudioNode.prototype.connect;AudioNode.prototype.connect=function(d,...a){if(d instanceof AudioDestinationNode)log.audio++;return cn.call(this,d,...a)};
const idOf=n=>{for(let e=n.nodeType===1?n:n.parentElement;e;e=e.parentElement){if(e.id&&e.classList&&e.classList.contains('b'))return e.id}return 'other'};
new MutationObserver(rs=>{for(const r of rs){const k=idOf(r.target);log.muts[k]=(log.muts[k]||0)+1}}).observe(document,{subtree:true,childList:true,attributes:true,characterData:true});})()"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        c = await b.new_context()
        await c.add_init_script(HOOK)
        pg = await c.new_page()
        await pg.goto("http://127.0.0.1:8795/d.html")
        boxes = await pg.evaluate(
            "Object.fromEntries([...document.querySelectorAll('.b')].map(e=>{const r=e.getBoundingClientRect();return [e.id,[r.x,r.y,r.right,r.bottom]]}))"
        )
        t0 = time.monotonic()
        frames = []
        shot_cost = []
        while time.monotonic() - t0 < 6.5:
            s = time.monotonic()
            png = await pg.screenshot()
            shot_cost.append(time.monotonic() - s)
            frames.append(
                (time.monotonic() - t0, Image.open(io.BytesIO(png)).convert("RGB"))
            )
            await asyncio.sleep(max(0, 0.5 - (time.monotonic() - s)))
        TILE = 20
        changed = {}  # box id -> times it changed
        for (ta, a), (tb, bb) in zip(frames, frames[1:]):
            bbox = ImageChops.difference(a, bb)
            px = bbox.load()
            W, Hh = bbox.size
            hit = set()
            for y in range(0, Hh, TILE):
                for x in range(0, W, TILE):
                    if bbox.crop((x, y, min(x + TILE, W), min(y + TILE, Hh))).getbbox():
                        cx, cy = x + TILE / 2, y + TILE / 2
                        ids = [
                            k
                            for k, (l, t, r, bt) in boxes.items()
                            if l <= cx <= r and t <= cy <= bt
                        ]
                        hit.add(ids[0] if ids else f"tile@{x},{y}")
            for h in hit:
                changed.setdefault(h, []).append(round(tb, 1))
        info = await pg.evaluate(
            "({timers:__t.timers,audio:__t.audio,muts:__t.muts,anims:document.getAnimations().map(a=>[a.effect.target.closest('.b')?.id,a.effect.getComputedTiming().iterations,a.effect.getComputedTiming().duration,a.playState]),reduce:matchMedia('(prefers-reduced-motion: reduce)').matches})"
        )
        print(
            f"frames {len(frames)}, screenshot cost median {sorted(shot_cost)[len(shot_cost) // 2] * 1000:.0f} ms"
        )
        for k in boxes:
            ts = changed.get(k, [])
            print(
                f"  {k:9} pixel changes at {ts[:3]}{'...' if len(ts) > 3 else ''} last={ts[-1] if ts else None}  still changing after 5 s: {any(t >= 5 for t in ts)}  DOM mutations: {info['muts'].get(k, 0)}"
            )
        print("  other tiles:", [k for k in changed if k not in boxes])
        print(
            "  timers:",
            sorted(set(map(tuple, info["timers"]))),
            "| Web Audio nodes to destination:",
            info["audio"],
            "| prefers-reduced-motion reduce:",
            info["reduce"],
        )
        print("  getAnimations at end:", info["anims"])
        await b.close()


asyncio.run(main())
