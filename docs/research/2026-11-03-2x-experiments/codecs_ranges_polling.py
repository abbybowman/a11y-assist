import asyncio
import collections
import http.server
import json
import os
import re
import sys
import threading
import zipfile

from playwright.async_api import async_playwright

SITE = sys.argv[1]
HAR = sys.argv[2]
cnt = {"poll": 0}
seen = collections.Counter()


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        p = self.path.split("?")[0]
        seen[p] += 1
        if p == "/poll":
            cnt["poll"] += 1
            b = str(cnt["poll"]).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if p == "/bust":
            self.send_response(204)
            self.end_headers()
            return
        f = os.path.join(SITE, p.lstrip("/"))
        # Only files inside SITE: resolve the path and refuse anything
        # outside it ("/../" in a request), before touching the file.
        root = os.path.realpath(SITE)
        f = os.path.realpath(f)
        if not f.startswith(root + os.sep) or not os.path.isfile(f):
            self.send_response(404)
            self.end_headers()
            return
        data = open(f, "rb").read()
        ct = {
            "html": "text/html",
            "mp4": "video/mp4",
            "webm": "video/webm",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
        }.get(f.rsplit(".", 1)[1], "application/octet-stream")
        rng = self.headers.get("Range")
        if rng:
            m = re.match(r"bytes=(\d+)-(\d*)", rng)
            s = int(m[1])
            e = int(m[2]) if m[2] else len(data) - 1
            e = min(e, len(data) - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {s}-{e}/{len(data)}")
            body = data[s : e + 1]
        else:
            self.send_response(200)
            body = data
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8770), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
srv6 = None
JS = """()=>({v:[...document.querySelectorAll('video')].map(x=>({id:x.id,paused:x.paused,t:+x.currentTime.toFixed(1),err:x.error&&x.error.code,audio:x.webkitAudioDecodedByteCount})),q:document.getElementById('q').textContent})"""


async def run(b, mode):
    kw = {"record_har_path": HAR, "record_har_mode": "full"} if mode == "record" else {}
    c = await b.new_context(**kw)
    if mode == "replay":
        await c.route_from_har(HAR, not_found="abort")
    pg = await c.new_page()
    cdp = await c.new_cdp_session(pg)
    players = collections.defaultdict(set)
    cdp.on(
        "Media.playerPropertiesChanged",
        lambda e: [players[e["playerId"][:6]].add(p["name"]) for p in e["properties"]],
    )
    await cdp.send("Media.enable")
    failed = []
    pg.on(
        "requestfailed", lambda r: failed.append(r.url.split("?")[0].rsplit("/", 1)[-1])
    )
    await pg.goto("http://127.0.0.1:8770/media.html")
    qs = []
    for i in range(5):
        await pg.wait_for_timeout(800)
        qs.append(await pg.evaluate("document.getElementById('q').textContent"))
    st = await pg.evaluate(JS)
    fr = [f for f in pg.frames if "inner" in f.url]
    inner = (
        await fr[0].evaluate(
            "(()=>{const a=document.getElementById('ia');return {paused:a.paused,t:+a.currentTime.toFixed(1),err:a.error&&a.error.code}})()"
        )
        if fr
        else None
    )
    print(mode, json.dumps(st["v"]), "poll seen:", qs, "inner audio:", inner)
    print(
        "   page-session Media players:",
        len(players),
        "with audio-track prop:",
        sum("kAudioTracks" in v for v in players.values()),
        "| failed:",
        collections.Counter(failed),
    )
    await c.close()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        await run(b, "record")
        with zipfile.ZipFile(HAR) as z:
            n = [x for x in z.namelist() if x.endswith(".har")][0]
            es = json.loads(z.read(n))["log"]["entries"]
        print(
            "HAR entries:",
            collections.Counter(
                (
                    e["request"]["url"].split("?")[0].rsplit("/", 1)[-1],
                    e["response"]["status"],
                )
                for e in es
            ),
        )
        await run(b, "replay")
        pg = await b.new_page()
        await pg.goto("http://127.0.0.1:8770/media.html")
        for f in ("anim.png", "anim.webp", "anim.gif"):
            r = await pg.evaluate(
                """async(f)=>{const res=await fetch(f);const d=new ImageDecoder({data:res.body,type:res.headers.get('content-type')});await d.tracks.ready;const t=d.tracks.selectedTrack;let tot=0;for(let i=0;i<t.frameCount;i++){tot+=(await d.decode({frameIndex:i})).image.duration||0}return [t.frameCount,t.repetitionCount,tot/1e6]}""",
                f,
            )
            print("ImageDecoder", f, "frames, loops, seconds per loop:", r)
        await b.close()


asyncio.run(main())
