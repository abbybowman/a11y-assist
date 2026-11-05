# Video flashes: play a tool page's <video> slowed down and read every presented
# frame with requestVideoFrameCallback (each callback carries the frame's media time).
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
    ("127.0.0.1", 8803), functools.partial(H, directory=sys.argv[1])
)
threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = """async ([src, rate, secs])=>{const v=document.createElement('video');v.src=src;v.muted=true;v.playbackRate=rate;document.body.append(v);
 await new Promise(r=>v.oncanplay=r);const c=new OffscreenCanvas(160,120),x=c.getContext('2d'),out=[];
 const lin=u=>{u/=255;return u<=0.04045?u/12.92:((u+0.055)/1.055)**2.4};
 await new Promise(done=>{const cb=(now,m)=>{x.drawImage(v,0,0,160,120);const p=x.getImageData(80,60,1,1).data;
   out.push([m.mediaTime,0.2126*lin(p[0])+0.7152*lin(p[1])+0.0722*lin(p[2])]);
   if(m.mediaTime>=secs||v.ended)done();else v.requestVideoFrameCallback(cb)};v.requestVideoFrameCallback(cb);v.play()});
 let tr=0,last=out[0][1];for(const [t,L] of out){if(Math.abs(L-last)>=0.1&&Math.min(L,last)<0.8){tr++;last=L}}
 const span=out[out.length-1][0]-out[0][0];
 return {frames:out.length,span:+span.toFixed(2),flashes_per_s:+(tr/2/span).toFixed(2)}}"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto("http://127.0.0.1:8803/")
        for rate in (1.0, 0.5):
            print(
                f"rate {rate}: video strobe (true 5 flashes/s, 30 fps):",
                await asyncio.wait_for(
                    pg.evaluate(JS, ["strobe5.webm", rate, 2.0]), 30
                ),
            )
        await b.close()


asyncio.run(main())
