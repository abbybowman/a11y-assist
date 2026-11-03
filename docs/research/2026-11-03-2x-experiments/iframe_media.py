import asyncio
import collections
import http.server
import json
import os
import re
import sys
import threading
import time
import zipfile

from playwright.async_api import async_playwright

SITE = sys.argv[1]
HAR = sys.argv[2]
PROXY = os.environ.get("HTTPS_PROXY")


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        f = os.path.join(SITE, self.path.split("?")[0].lstrip("/"))
        if not os.path.isfile(f):
            self.send_response(404)
            self.end_headers()
            return
        data = open(f, "rb").read()
        ct = "text/html" if f.endswith("html") else "video/webm"
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


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8780), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
MEDIA = """()=>[...document.querySelectorAll('video,audio')].map(v=>({paused:v.paused,muted:v.muted,t:+v.currentTime.toFixed(1),err:v.error&&v.error.code,src:(v.currentSrc||'').slice(0,40)}))"""


async def run(b, mode):
    kw = {"record_har_path": HAR, "record_har_mode": "full"} if mode == "record" else {}
    c = await b.new_context(**kw)
    if mode == "replay":
        await c.route_from_har(HAR, not_found="abort")
    pg = await c.new_page()
    cdp = await c.new_cdp_session(pg)
    players = collections.defaultdict(dict)

    def on_props(e):
        for p in e["properties"]:
            players[e["playerId"][:8]][p["name"]] = str(p.get("value"))[:50]

    cdp.on("Media.playerPropertiesChanged", on_props)
    await cdp.send("Media.enable")
    aborted = collections.Counter()
    pg.on("requestfailed", lambda r: aborted.update([r.url.split("/")[2]]))
    t0 = time.monotonic()
    await pg.goto("http://127.0.0.1:8780/top.html", wait_until="load", timeout=30000)
    await pg.wait_for_timeout(8000)
    tg = await cdp.send("Target.getTargets")
    print(f"--- {mode} ({time.monotonic() - t0:.0f}s)")
    print(
        "  targets:",
        collections.Counter(t["type"] for t in tg["targetInfos"]),
        [t["url"][:45] for t in tg["targetInfos"] if t["type"] == "iframe"],
    )
    for fr in pg.frames[1:]:
        try:
            m = await fr.evaluate(MEDIA)
        except Exception as ex:
            m = f"ERR {str(ex)[:60]}"
        print("  frame", fr.url[:50], "->", m)
    print(
        "  page-session Media players:",
        {
            k: (
                v.get("kFrameUrl", "")[:35],
                v.get("kAudioTracks", "")[:12] != "",
                v.get("kIsStreaming"),
            )
            for k, v in players.items()
        },
    )
    if aborted:
        print("  failed requests by host:", dict(aborted))
    await c.close()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            channel=os.environ.get("CH") or None,
            args=["--autoplay-policy=no-user-gesture-required"],
            proxy={"server": PROXY, "bypass": "127.0.0.1,localhost"},
        )
        await run(b, "record")
        sz = os.path.getsize(HAR)
        with zipfile.ZipFile(HAR) as z:
            n = [x for x in z.namelist() if x.endswith(".har")][0]
            es = json.loads(z.read(n))["log"]["entries"]
        print(
            "HAR",
            sz // 1024,
            "kB,",
            len(es),
            "entries; googlevideo/vimeocdn media entries:",
            sum(
                ("googlevideo" in e["request"]["url"])
                or (
                    "vimeocdn" in e["request"]["url"] and "range" in e["request"]["url"]
                )
                for e in es
            ),
        )
        await run(b, "replay")
        await b.close()


asyncio.run(main())
