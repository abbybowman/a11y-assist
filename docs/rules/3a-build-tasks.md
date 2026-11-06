# Build tasks: 3.A Flashing

Spec [3a-flashing.md](3a-flashing.md) at 0.1.0 (a draft, no outcome).
Research and decisions:
[research/2026-11-03-3a-flashing.md](../research/2026-11-03-3a-flashing.md).
Build it after 2.B, which brings pass T, the batch browser, the media store
and the timer hooks
([solutions/watching-a-page-over-time.md](../solutions/watching-a-page-over-time.md)).

## Code changes

| Where | Change |
| --- | --- |
| `motion.py` (2.x) | Triggers: animations, transitions and timers under 334 ms; `requestAnimationFrame` loops (extend the timer hook); animated image frame delays; videos; a 2 s CDP screencast beside pass T |
| `flash.py` (new) | The flash capture: a stepped clock and animations at 1024 × 768 with real-time media masked; images decoded; video decoded at 0.5× with `requestVideoFrameCallback` (first 10 s, full-screen scale) |
| `flash.py` | The counting: per-cell L (WCAG 2.0 formula), peak-to-valley transitions, general and red transitions (2.0, plus 2.2 red for the note), flashes in sliding one-second windows, concurrent flashing area in any 341 × 256 rectangle, the fine-pattern check. Pure functions on frame arrays, unit-tested without a browser |
| `checks/t3a.py` | Rows A1–A4 and the assessment F1–F5; the summary carries the assessment sentence (so SCRT's `TesterComment` keeps it); registered in `tests/drafts.py` until 1.0.0 |
| `models.py`, SCRT export | Check that NOT TESTED with a summary reaches the SCRT file as "Not Tested" with the comment (`scrt.py` maps `Outcome.NOT_TESTED`) |

## Fixtures

No ACT rule, DHS verdict or Baseline Alignment case exists for 2.3.1.
All fixtures are custom pages in `tests/fixtures/3a/`. Media are generated
by a script (as `docs/research/2026-11-03-2x-experiments/make_flash_media.py`),
not committed as large binaries.

| Case | Expected |
| --- | --- |
| none (static page) | A4 DNA, no capture |
| blink-1hz (CSS, 1 per second) | A4 DNA (2.B's) |
| css-5hz-small (40 × 40 px) | A2 NOT TESTED; F5 does not fail |
| css-5hz-large (400 × 300 px, black and white) | A2; F2 fails |
| timer-6hz-large (setInterval 80 ms) | A2; F2 |
| raf-strobe (toggles every frame, full width) | A2; F2 (needs stepping; real-time screenshots alias it) |
| red-strobe (saturated red and black, large) | A2; F3 fails (red) |
| exactly-3 (3 flashes in a second, ending on the start state) | A4 (G19) |
| seven-transitions | A2 |
| gif-5hz-large, gif-2hz | A2 with F2; A4 |
| video-strobe (5 per second, 3 s) | A2; F2 at full-screen scale |
| video-late-flash (flashes from 12 s) | A3 (beyond the 10 s cap) |
| checkerboard-fine (2 px squares alternating) | A2; F1 could not assess |
| two-small-flashers (each under the area, together over it, in one rectangle) | A2; F2 if aligned frame by frame, else F4 |
| strobe-in-iframe (cross-site) | A2; captured through the iframe (run also with full Chromium) |

## Browser behavior to verify in code

| ID | Verify | Status |
| --- | --- | --- |
| V1 | Stepping (clock paused, `run_for`, animations' `currentTime`) measures CSS, timers and `requestAnimationFrame` exactly; real-time screenshots alias a strobe | Checked (research section 4) |
| V2 | The counting on synthetic frame arrays: G19's boundary (6 versus 7 transitions; ending state), peak-to-valley transitions with intermediate frames (fades) | Not checked |
| V3 | The area: the largest concurrent flashing area inside any 341 × 256 rectangle, on a page with flashers of known sizes | Not checked |
| V4 | Red transitions (WCAG 2.0 Note 3 and 2.2) on known colors | Not checked |
| V5 | Video decoded at 0.5× gets every frame (61 of 61 checked), scaled to 1024 × 768 | Decoding checked; scaling not |
| V6 | `ImageDecoder` frames and delays for GIF, APNG and WebP (2.x item 8); two loops | Checked for frames; loops not |
| V7 | `<marquee>` and SMIL: can they be stepped (`SVGSVGElement.pauseAnimations`, `setCurrentTime`)? If not, A3 | Not checked |
| V8 | A strobe in a cross-site iframe is captured, out-of-process (full Chromium) and in the shell | Not checked |
| V9 | Masking real-time media out of stepped frames, and a page mixing both | Not checked |
| V10 | The screencast trigger catches a 30 per second strobe that the other triggers miss (a strobe drawn with `setTimeout(0)` chains, say) | Not checked |

## Optional: IRIS as a cross-check

Only if there is time; not required (Abby, 2026-11-03). See research
section 7:

- build EA's IRIS locally, never as a dependency;
- run it on our frame-exact captures written as lossless 1024 × 768
  video, with its defaults and with `AreaProportion` 0.0278;
- compare.

Its area rule (25% of the whole frame) differs from WCAG's, so its
defaults can pass what WCAG fails.

## At 1.0.0

- CLAUDE.md: Layout gains `flash.py` and `t3a.py`. Principle 2 already
  allows NOT TESTED where the TT names it. Add one line saying 3.A's
  assessment is a note recorded with NOT TESTED, never an outcome.
- `docs/hackathon/evaluation.md` and the deck: 3.A as the first test where
  the tool goes past what the TT can test, with its assessment recorded
  for DHS or W3C to judge. No answer key exists, so accuracy comes from
  the fixtures and held-out pages with flashing, if any.
- `docs/solutions/`: why flashing needs stepped capture (aliasing), and
  how decoding replaces it for images and video.
- ROADMAP: move 3.A from the coverage map's "Tier 1, rank 19 (detection)"
  to built.

## Left

- V2–V4 and V7–V10.
- Whether fine-pattern detection (F1) is reliable enough to keep, or every
  pattern should go to a person.
- Real pages with flashing for the held-out set, which are rare.
