import asyncio
import functools
import http.server
import json
import sys
import threading

from playwright.async_api import async_playwright

site = sys.argv[1]
har = sys.argv[2]
args = sys.argv[3:]


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 8766), functools.partial(H, directory=site)
)
threading.Thread(target=srv.serve_forever, daemon=True).start()
INIT = """window.__ev=[];for(const t of ['play','playing','pause','error','stalled','waiting','canplaythrough'])addEventListener(t,e=>__ev.push(t+':'+e.target.id+':'+(e.target.currentTime||0).toFixed(1)),true);"""
JS = """async()=>{const r={ev:__ev.slice(0,30),ac:window.acs()};const a=document.getElementById('a1');r.t=[...document.querySelectorAll('audio')].map(x=>[x.id,x.paused,+x.currentTime.toFixed(1)]);
try{ if(a.paused){await a.play();r.manual='ok '+a.currentTime}}catch(e){r.manual=String(e)} r.nav=navigator.getAutoplayPolicy?navigator.getAutoplayPolicy('mediaelement'):null; r.navac=navigator.getAutoplayPolicy?navigator.getAutoplayPolicy('audiocontext'):null; return r}"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=args)
        for mode in ("live-record", "replay"):
            kw = (
                {"record_har_path": har, "record_har_mode": "full"}
                if mode == "live-record"
                else {}
            )
            c = await b.new_context(**kw)
            await c.add_init_script(INIT)
            if mode == "replay":
                await c.route_from_har(har, not_found="abort")
            pg = await c.new_page()
            await pg.goto("http://127.0.0.1:8766/index.html")
            await pg.wait_for_timeout(3000)
            print(args, mode, json.dumps(await pg.evaluate(JS)))
            await c.close()
        await b.close()


asyncio.run(main())
