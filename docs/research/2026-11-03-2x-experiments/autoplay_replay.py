import asyncio
import functools
import http.server
import json
import sys
import threading

from playwright.async_api import async_playwright

site = sys.argv[1]
har = sys.argv[2]
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = """()=>({media:[...document.querySelectorAll('audio')].map(a=>({id:a.id,paused:a.paused,t:a.currentTime,err:a.error&&a.error.code,ready:a.readyState,bytes:a.webkitAudioDecodedByteCount,dur:a.duration})),
anims:document.getAnimations().map(a=>a.animationName||a.constructor.name+':'+(a.effect&&a.effect.target&&a.effect.target.tagName)), ac:window.acs(), n:document.getElementById('n').textContent})"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for mode in ("live-record", "replay"):
            kw = (
                {"record_har_path": har, "record_har_mode": "full"}
                if mode == "live-record"
                else {}
            )
            c = await b.new_context(**kw)
            if mode == "replay":
                await c.route_from_har(har, not_found="abort")
            pg = await c.new_page()
            cdp = await c.new_cdp_session(pg)
            ev = []
            cdp.on("Media.playerPropertiesChanged", lambda e: ev.append(e))
            await cdp.send("Media.enable")
            reqs = []
            pg.on("requestfailed", lambda r: reqs.append(("FAIL", r.url, r.failure)))
            await pg.goto("http://127.0.0.1:8765/index.html")
            await pg.wait_for_timeout(3000)
            print(mode, json.dumps(await pg.evaluate(JS)))
            props = set()
            for e in ev:
                for pr in e["properties"]:
                    props.add((pr["name"], str(pr.get("value"))[:40]))
            print("  media props:", sorted(props)[:30])
            print("  failed:", reqs)
            await c.close()
        await b.close()


asyncio.run(main())
