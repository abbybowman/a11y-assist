# Fix candidate: while recording, also save each media URL's full body (one extra
# GET without Range, as the recorder would); on replay, answer Range requests for
# those URLs from the saved body (route registered after route_from_har runs first).
import asyncio
import os
import re
import time

from playwright.async_api import async_playwright

exec(
    open(os.path.join(os.path.dirname(__file__), "large_media.py"))
    .read()
    .split("async def run")[0]
)
store = {}


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        # record: note media URLs, then fetch each once in full with the context's request API
        c = await b.new_context(record_har_path=HAR, record_har_mode="full")
        pg = await c.new_page()
        media = set()
        pg.on(
            "request",
            lambda r: media.add(r.url) if r.resource_type == "media" else None,
        )
        await pg.goto("http://127.0.0.1:8796/b.html")
        await pg.wait_for_timeout(3000)
        t = time.monotonic()
        for u in media:
            r = await c.request.get(u.split("#")[0])
            store[u.split("#")[0]] = (await r.body(), r.headers.get("content-type"))
        print(
            "media saved:",
            {u: len(v[0]) // 1024 for u, (v) in [(k, v) for k, v in store.items()]},
            "kB in",
            round(time.monotonic() - t, 2),
            "s",
        )
        await c.close()
        c = await b.new_context()
        await c.route_from_har(HAR, not_found="abort")

        async def serve(route):
            body, ct = store[route.request.url.split("#")[0]]
            rng = route.request.headers.get("range")
            if rng:
                m = re.match(r"bytes=(\d+)-(\d*)", rng)
                s = int(m[1])
                e = int(m[2]) if m[2] else len(body) - 1
                e = min(e, len(body) - 1)
                await route.fulfill(
                    status=206,
                    headers={
                        "Content-Type": ct,
                        "Accept-Ranges": "bytes",
                        "Content-Range": f"bytes {s}-{e}/{len(body)}",
                    },
                    body=body[s : e + 1],
                )
            else:
                await route.fulfill(
                    status=200,
                    headers={"Content-Type": ct, "Accept-Ranges": "bytes"},
                    body=body,
                )

        await c.route(lambda u: u.split("#")[0] in store, serve)
        pg = await c.new_page()
        await pg.goto("http://127.0.0.1:8796/b.html")
        await pg.wait_for_timeout(5000)
        print(
            "replay with media store:",
            await pg.evaluate(
                "(()=>{const v=document.getElementById('v');return {paused:v.paused,t:+v.currentTime.toFixed(1),err:v.error&&v.error.code,audio:v.webkitAudioDecodedByteCount}})()"
            ),
        )
        await b.close()


asyncio.run(main())
