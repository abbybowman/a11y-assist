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
    ("127.0.0.1", 8767), functools.partial(H, directory=sys.argv[1])
)
threading.Thread(target=srv.serve_forever, daemon=True).start()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto("http://127.0.0.1:8767/m.html")
        await pg.wait_for_timeout(500)
        r = await pg.evaluate("""async()=>{const res=await fetch('anim.gif');const d=new ImageDecoder({data:res.body,type:'image/gif'});await d.tracks.ready;const t=d.tracks.selectedTrack;
      let tot=0;for(let i=0;i<t.frameCount;i++){const f=await d.decode({frameIndex:i});tot+=f.image.duration||0;}
      return {frames:t.frameCount,rep:t.repetitionCount,animated:t.animated,total_us:tot,anims:document.getAnimations().length, blinkTag:document.querySelector('blink').constructor.name, marqueeX:document.getElementById('m').getBoundingClientRect().x}}""")
        a = await pg.screenshot()
        await pg.wait_for_timeout(1000)
        c = await pg.screenshot()
        print(r, "marquee pixels changed:", a != c)
        await b.close()


asyncio.run(main())
