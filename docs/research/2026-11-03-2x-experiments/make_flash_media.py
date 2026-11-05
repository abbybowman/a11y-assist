"""Write the flash test media into pages/flash/: a GIF alternating black and
white every 100 ms (5 flashes/s) and a 30 fps WebM strobe at 5 flashes/s
(the WebM needs ffmpeg)."""

import pathlib
import subprocess

from PIL import Image

out = pathlib.Path(__file__).parent / "pages" / "flash"
frames = [Image.new("RGB", (200, 200), c) for c in ((0, 0, 0), (255, 255, 255))] * 5
frames[0].save(
    out / "flash5.gif", save_all=True, append_images=frames[1:], duration=100, loop=0
)
subprocess.run(
    [
        "ffmpeg",
        "-nostdin",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=160x120:r=30:d=3",
        "-vf",
        "geq=lum='if(lt(mod(N\\,6)\\,3)\\,16\\,235)':cb=128:cr=128",
        "-c:v",
        "libvpx-vp9",
        "-b:v",
        "200k",
        str(out / "strobe5.webm"),
    ],
    check=True,
)
