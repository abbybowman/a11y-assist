"""3.A's fixture media. GIFs are made by the test server when asked
(`gif`, from tests/conftest.py); the two WebM files are written here once
with ffmpeg and committed (a few KB each), so tests need no ffmpeg:

    uv run python tests/fixtures/3a/make_media.py

Nothing random: every frame is a fixed colour."""

from __future__ import annotations

import io
import pathlib
import subprocess

from PIL import Image

HERE = pathlib.Path(__file__).parent / "media"

# name: (size, frame delay ms, colours); every one loops forever.
GIFS = {
    "gif-5hz-large.gif": ((400, 300), 100, [(0, 0, 0), (255, 255, 255)]),
    "gif-5hz-small.gif": ((120, 100), 100, [(0, 0, 0), (255, 255, 255)]),
}


def gif(name: str) -> bytes | None:
    if name not in GIFS:
        return None
    size, ms, colours = GIFS[name]
    frames = [Image.new("RGB", size, c) for c in colours]
    out = io.BytesIO()
    frames[0].save(
        out, format="GIF", save_all=True, append_images=frames[1:], duration=ms, loop=0
    )
    return out.getvalue()


def _webm(name: str, seconds: int, lum: str) -> None:
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
            f"color=c=black:s=160x120:r=30:d={seconds}",
            "-vf",
            f"geq=lum='{lum}':cb=128:cr=128",
            "-c:v",
            "libvpx-vp9",
            "-b:v",
            "60k",
            "-g",
            "30",
            str(HERE / name),
        ],
        check=True,
    )


def main() -> None:
    HERE.mkdir(exist_ok=True)
    # 5 flashes a second for 3 s (black and white, 3 frames each at 30 fps).
    _webm("video-strobe.webm", 3, "if(lt(mod(N\\,6)\\,3)\\,16\\,235)")
    # Grey for 12 s, then 5 flashes a second for 2 s: past the 10 s analyzed.
    _webm(
        "video-late-flash.webm",
        14,
        "if(lt(N\\,360)\\,128\\,if(lt(mod(N\\,6)\\,3)\\,16\\,235))",
    )


if __name__ == "__main__":
    main()
