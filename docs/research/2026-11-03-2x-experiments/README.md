# 2.A–2.D experiments (2026-11-03)

These scratch scripts back the "Verified" items in
[plans/2026-11-03-auto-updating-2a-2d.md](../../plans/2026-11-03-auto-updating-2a-2d.md).
They are research evidence, not tests. They start their own local HTTP
servers, use plain Playwright (not the tool's pipeline), and some load
pages from the network. The build turns each one into a V-check in
`tests/` with no network.

Results are from Linux, 4 CPUs, Playwright 1.63:

- "shell" is the default headless shell.
- "full" is `channel="chromium"`, new headless mode.

## Setup

The media files are generated, not committed. Create them once (needs
ffmpeg; this container has it):

```bash
cd docs/research/2026-11-03-2x-experiments/pages
ffmpeg -nostdin -y -f lavfi -i "sine=frequency=440:duration=10" -c:a libopus site/a.webm
ffmpeg -nostdin -y -f lavfi -i "sine=frequency=440:duration=10" site/a.mp3
ffmpeg -nostdin -y -f lavfi -i "sine=frequency=440:duration=10" site/a.wav
ffmpeg -nostdin -y -f lavfi -i "testsrc=duration=2:size=40x40:rate=5" -loop 0 site/anim.gif
ffmpeg -nostdin -y -f lavfi -i "testsrc=duration=2:size=40x40:rate=5" -plays 0 -f apng site/anim.png
ffmpeg -nostdin -y -f lavfi -i "testsrc=duration=2:size=40x40:rate=5" -loop 0 -c:v libwebp site/anim.webp
ffmpeg -nostdin -y -f lavfi -i "testsrc=duration=10:size=160x120:rate=25" -f lavfi -i "sine=frequency=440:duration=10" -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest site/v264.mp4
ffmpeg -nostdin -y -f lavfi -i "testsrc=duration=10:size=160x120:rate=25" -f lavfi -i "sine=frequency=440:duration=10" -c:v libvpx-vp9 -c:a libopus -shortest -b:v 200k site/v9.webm
cp site/v9.webm site/a.webm ifr/
cp site/anim.gif det/long.gif
ffmpeg -nostdin -y -f lavfi -i "testsrc=duration=2:size=60x60:rate=5" -loop -1 det/once.gif
ffmpeg -nostdin -y -f lavfi -i "testsrc=duration=4:size=120x90:rate=15" -c:v libvpx-vp9 -b:v 100k -an det/loop.webm
ffmpeg -nostdin -y -f lavfi -i "testsrc2=duration=60:size=1280x720:rate=30" -f lavfi -i "sine=frequency=440:duration=60" -c:v libvpx-vp9 -b:v 4M -deadline realtime -cpu-used 8 -c:a libopus -shortest big/big.webm
```

`loudness.py` also needs ACT's rabbit videos: put `silent.webm` and
`video.webm` from
`https://www.w3.org/WAI/content-assets/wcag-act-rules/test-assets/rabbit-video/`,
plus `site/v264.mp4`, in one folder and pass that folder.

## Scripts (run from the repo root with `uv run python <script> …`)

| Plan item | Script | Arguments | Result (2026-11-03) |
| --- | --- | --- | --- |
| 1, 2 | `autoplay_replay.py` | `pages/site <har.zip>` | shell, default flags: audio plays live, stays paused at 0 on HAR replay |
| 1, 5 | `autoplay_policy.py` | `pages/site <har.zip> [--autoplay-policy=no-user-gesture-required]` | with the flag: plays on replay; `AudioContext` running |
| 6 (part), 8, 9 | `marquee_gif_decoder.py` | `pages/site` | marquee and GIF not in `getAnimations()`; `ImageDecoder` frames/loops/duration; `<blink>` unknown |
| 3, 8, 10 | `codecs_ranges_polling.py` | `pages/site <har.zip>` | H.264 and VP9 play on replay; small media, one range each, replays; polling stuck at the first response on replay; APNG/WebP decoded |
| 4 | `loudness.py` | `<folder with the media files>` | silent -180 dBFS, audible -10 to -12 dBFS |
| 15, 16, 17 | `iframe_media.py` | `pages/ifr <har.zip>` (`CH=chromium` for full) | cross-site iframe media plays live and on replay; YouTube/Vimeo do not play through this container's proxy |
| 15 | `iframe_process.py` | `pages/ifr` (`CH=chromium` for full) | shell: all iframes in-process; full: 3 out-of-process iframes; CDP `Media` sees no players there |
| 16 | `iframe_probe.py` | `pages/ifr` | full: pixels change inside the iframe; Tab reaches its Pause button; Enter pauses the video |
| 12 | `carousels.py` | `pages/car` (loads the libraries from jsdelivr) | Slick and Splide pause on focus; four of six pause on hover |
| 6, 7, 11 | `detection.py` | `pages/det` | 12 kinds of motion classified from pixels; 8 s period caught by the timer hook; reduced motion off by default |
| 13 | `large_media.py` | `pages/big <har.zip>` | 21 MB video in three ranges: HAR has no bodies; replay error 4 |
| 14 | `large_media_store.py` | `pages/big <har.zip>` | with the full body saved and ranges served on replay: plays from 40 s with audio |
| 18 | `parallel_watcher.py` | `<absolute path to a page> <seconds>` | run beside `evals/time_budget.py budget/agency-home.html`; the walk was not slowed |
| Q11 | `browser_costs.py` | none | launch 68 vs 139 ms, context+page+load 61 vs 151 ms, Tab 2.8 vs 4.7 ms (shell vs full) |
| Q11 | `cross_browser_replay.py` | `pages/ifr <har.zip>` | recorded in the shell, replayed in full Chromium: out-of-process iframe, video plays, Tab+Enter pauses it |

**What feeds the build directly:** the tile diff in `detection.py`
(pass T), the media store in `large_media_store.py` (`capture.py`), and
the pages in `pages/car/`, `pages/det/` and `pages/ifr/` (the starting
point for fixtures; the carousel pages need their libraries vendored
first, since tests do not use the network).

Some scripts read helpers from another by `exec` (`iframe_process.py` and
`iframe_probe.py` use `iframe_media.py`'s server; `large_media_store.py`
uses `large_media.py`'s). Keep them in the same folder.
