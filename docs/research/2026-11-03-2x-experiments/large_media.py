import asyncio
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
reqs = []


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        f = os.path.join(SITE, self.path.split("?")[0].split("#")[0].lstrip("/"))
        if not os.path.isfile(f):
            self.send_response(404)
            self.end_headers()
            return
        data = open(f, "rb").read()
        ct = "text/html" if f.endswith("html") else "video/webm"
        rng = self.headers.get("Range")
        reqs.append(rng)
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
        try:
            self.wfile.write(body)
        except Exception:
            pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8796), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()


async def run(b, mode):
    kw = {"record_har_path": HAR, "record_har_mode": "full"} if mode == "record" else {}
    c = await b.new_context(**kw)
    if mode == "replay":
        await c.route_from_har(HAR, not_found="abort")
    pg = await c.new_page()
    fails = []
    pg.on("requestfailed", lambda r: fails.append(r.failure))
    await pg.goto("http://127.0.0.1:8796/b.html")
    await pg.wait_for_timeout(5000)
    st = await pg.evaluate(
        "(()=>{const v=document.getElementById('v');return {paused:v.paused,t:+v.currentTime.toFixed(1),err:v.error&&v.error.code,ready:v.readyState,buffered:[...Array(v.buffered.length).keys()].map(i=>[+v.buffered.start(i).toFixed(0),+v.buffered.end(i).toFixed(0)]), audio:v.webkitAudioDecodedByteCount}})()"
    )
    print(mode, st, "failed:", fails[:3])
    await c.close()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        await run(b, "record")
        print("ranges requested live:", reqs)
        with zipfile.ZipFile(HAR) as z:
            n = [x for x in z.namelist() if x.endswith(".har")][0]
            es = json.loads(z.read(n))["log"]["entries"]
        print(
            "HAR size",
            os.path.getsize(HAR) // 1024,
            "kB; media entries:",
            [
                (
                    e["response"]["status"],
                    next(
                        (
                            h["value"]
                            for h in e["request"]["headers"]
                            if h["name"].lower() == "range"
                        ),
                        None,
                    ),
                    e["response"]["content"].get("size"),
                )
                for e in es
                if "webm" in e["request"]["url"]
            ],
        )
        await run(b, "replay")
        await b.close()


asyncio.run(main())
