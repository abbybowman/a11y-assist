import asyncio
import functools
import http.server
import sys
import threading

from playwright.async_api import async_playwright


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 8771), functools.partial(H, directory=sys.argv[1])
)
threading.Thread(target=srv.serve_forever, daemon=True).start()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto("http://127.0.0.1:8771/")
        for f in ("silent.webm", "video.webm", "v264.mp4"):
            r = await pg.evaluate(
                """async(f)=>{const buf=await (await fetch(f)).arrayBuffer();const ac=new OfflineAudioContext(1,44100,44100);const a=await ac.decodeAudioData(buf);
          let mx=0,loud=0;for(let c=0;c<a.numberOfChannels;c++){const d=a.getChannelData(c);for(let i=0;i<d.length;i++){const v=Math.abs(d[i]);if(v>mx)mx=v;if(v>0.01)loud++}}
          return {seconds:+a.duration.toFixed(1), peak_dbfs:+(20*Math.log10(mx||1e-9)).toFixed(1), loud_samples:loud}}""",
                f,
            )
            print(f, r)
        await b.close()


asyncio.run(main())
