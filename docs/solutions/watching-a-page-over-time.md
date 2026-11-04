# Watching a page over time (pass T, 2.A-2.D)

Lessons from building pass T (`motion.py`), the mechanism probe
(`mechanism.py`) and the media store (`capture.py`). Each one cost a failing
test or a false result first; each has a test now.

## Pass T is its own load, in its own browser

Every other load presses a key within a second, and some carousels pause
while one of their own controls has focus (Slick, Splide), so watching during
the walk would show them stopping: a false DOES NOT APPLY. Pass T is one load
with no input, beside the walk (no measurable cost to it), in a second,
headless full-Chromium browser with `--autoplay-policy=no-user-gesture-required`
(`browser.launch_for`). Only that browser gets the flag: the walk and every
other test see the page as before. Without the flag, a recorded
`<audio autoplay src>` stays at 0 s on replay; with it, it plays (a page's own
`play()` on a blob it builds plays even without the flag, so test with a file).

## Regions: over the whole watch, not frame by frame

- Map the union of each tile's changed pixels over the whole watch, once, at
  the end. Frame by frame, a spinning square landed on the square in one frame
  and on its box in the next, and slides taking turns gave one region per
  slide.
- An element covers the changed pixels only if it covered them at the first
  read too; otherwise the slide in view at the end of a sliding carousel
  "covers" it.
- A running animation's target, grown by half its size, wins over the element
  around it: a rotating square's pixels poke past its box and made a region of
  `<main>`.
- 4 px of slack: a focus ring is drawn just outside its element.
- An element replaced every second (innerHTML) gives way to its nearest
  ancestor that was there at the first read.
- A frame where more than half the page changed (a dialog's backdrop) is
  noted, not mapped.

## Sampling

- Frames alternate 0.35 s and 0.45 s apart. At a steady 0.5 s, a blink of 0.5 s
  per state was caught in the same state every frame (a false DOES NOT APPLY).
- Three reads (0, 3.5, 6.5 s) are too few to judge colour: a four-colour cycle
  came back to its first colour on the reads. Colour-only changes are judged
  on text, boxes and transforms staying the same, with a sign of styling.
- Content below the first screen shows in no frame: long animations,
  marquees, playing videos and the DOM log (text that really changes, at least
  three times, the last after 5 s) add regions for it. A replayed poll writes
  the same value each time, which is not an update.

- Decode media and images in a tool page, never the tested page. Loudness
  (`OfflineAudioContext`) works on `about:blank`; `ImageDecoder` (G152) does
  not exist there, because `about:blank` is not a secure context: the image
  tool page is a fresh context at `http://localhost`, answered by a route.

## The probe

- Watch a fixed clip of the page, not an element screenshot: Playwright waits
  for an element to stop moving before it screenshots it, which a spinning
  badge never does.
- Judge "slowed" on the time between two changes, never on the first change:
  where a watch starts in the cycle is chance (a 1 s ticker's first change came
  1.6 s in).
- Focus-only: if focus alone stops or slows the content, it is a pause on
  focus (K2). Only a focus-only probe that saw no effect lets a control count
  as working.
- One probe per content, shared by 2.B and 2.C, stopping early only on a real
  stop: a 2.C "slowed" must not end the probe 2.B needs.
- Focus a control the walk reached directly instead of replaying every Tab
  press to it: 80 presses per load for a ticker at the bottom of a page.
- Audio: a clip that reached its end during the probe is unreliable, never
  credited to a control.

## The media store

- A large video is fetched in byte ranges; the HAR keeps ranges with no body,
  so it never plays on replay. Each media file is also fetched in full while
  recording (50 MB and 15 s per page), stored inside the HAR zip (so frozen
  pages keep it), and its ranges are served on replay.
- Key files without the `#fragment`: requests never carry it, and a file the
  replay cannot range-serve cannot seek, so `#t=8,10` played from 0 s (a false
  FAIL on ACT 80f0bf).
- Trust a HEAD only when it succeeded: the test server's 501 page has a length
  too.

## Time: content that keeps changing slows everything

A ticker changes the DOM every second, so every key press waited for the
settle rule and no replay prefix was quick: the agency page with a ticker and
a carousel went from 102 s to over 120 s for the existing tests alone. The
settle rule now ignores DOM changes inside content pass T found still
changing (pushed to every open page when pass T ends), and the run gets 45 s
more (T1, Abby 2026-11-04). See the build tasks' Timing section.

## Questions

The judge eval caught two question gaps the scripted tests could not: 2.C J1
named an image it did not carry, and 2.A borrowed 2.C's "pause, stop, hide or
slow", which leaves out muting (a likely false FAIL). Check that every image a
question names is in its input, and that its verbs match the test's ER.
