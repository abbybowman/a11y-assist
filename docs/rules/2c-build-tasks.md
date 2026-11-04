# Build tasks: 2.A, 2.B, 2.C and 2.D

Specs at 0.1.0 (drafts, no outcome):

- [2c-auto-updating.md](2c-auto-updating.md), which defines pass T,
  regions, elements and the mechanism probe for the batch;
- [2d-change-notify-auto.md](2d-change-notify-auto.md);
- [2b-blinking-moving-scrolling.md](2b-blinking-moving-scrolling.md);
- [2a-audio-control.md](2a-audio-control.md).

Plan, research and measurements:
[plans/2026-11-03-auto-updating-2a-2d.md](../plans/2026-11-03-auto-updating-2a-2d.md).
Order (plan Q8): 2.C and 2.D, then 2.B, then 2.A.

## Status (2026-11-04)

Built, with tests (`tests/test_motion.py`, fixtures `tests/fixtures/2x/t-*.html`):

- `motion.py` pass T: frames, tile diff, regions over the whole watch,
  kinds, the three reads, DOM changes with their live regions, timers, the
  Web Audio hook, animations, media state per frame, dialogs, focus moves,
  polls (HAR and during the watch), and elements (Q6, V13).
- `capture.replay_context(init_scripts=...)` (Q7) and the pipeline's
  `_opener` passing them through.
- `t4e._DIALOGS_JS` moved to `observe.DIALOGS_JS`.
- `checks/t2c.py` and `checks/t2d.py`, registered in `tests/drafts.py`:
  2.C section 1 (A1-A5) and every instance row (K1-K8, E1-E4, the 3c ER 3
  table), J1 and J2 questions and answers; 2.D every row (N1-N6) and its J1
  and J2. `RunContext.open_motion` gives pass T its load
  (`motion.collect`, shared in `ctx.cache["motion"]`).
  - End to end: `tests/test_fixtures_2x.py` (7 pages for both tests, 4
    scripted-answer runs for 2.D J1 and J2).
  - 2.C's K and E rows on hand-built evidence: `tests/test_rows_2x.py`.
- `mechanism.py`: the mechanism probe (2.C section 2) in pass T's
  browser, with the walk's Tab presses; the focus-only probe; Q10's key
  press on J2's answer (`t2c.press_answered_keys`, once per run, modifiers
  plus one key, never the browser's own). 2.C now uses the walk.
  - Fixtures: a working pause button (K3), a carousel that pauses only on
    focus (K2), no control (K6), a pause button outside the windows (K6),
    a hotkey named in the first text (J2, then K4), a frequency control
    (K3 by slowed).
  - Two flaky false paths found under load and fixed: a focus-only probe
    that "slowed" the content fell to K3 (now K2), and "slowed" judged on
    the first change made a running ticker look slowed (now on the time
    between two changes).
- O1 (content that stopped changing before 5 s) is a hint, NEEDS REVIEW,
  with a note saying what was checked (Abby, 2026-11-04).

**Q11 is merged** (from `main`, 2026-11-04), and pass T runs in its own
browser: `browser.launch_for(..., autoplay=True)` is full Chromium, always
headless, with `--autoplay-policy=no-user-gesture-required` (Q1), launched
only when a 2.x check is selected. Pass T starts as a task beside the walk
(Q2; `ctx.cache["motion_task"]`, awaited by `motion.collect`). Pass T's
evidence records its browser (`MotionPass.browser`). Tests:
`tests/test_motion_browser.py` (autoplay plays only with the flag, V2's
first part; regions and live regions inside an out-of-process frame, V7's
pass T part; one watch, started before the walk ends).

Still open from Q2: the extra time allowance for pages with moving content
(set when the probe exists and is measured on a budget page).

- ACT efbfc7 vendored (`tests/test_act_2c.py`): all 11 cases give our
  expected outcome. 6/11 agree with DHS; the other 5 are DHS PASS cases
  that are NEEDS REVIEW here: three gated by ER 3 (the scorer marks them
  "gated"), the frequency field (K5) and the panel of controls (J2, then
  K5 or K8). Two fixes it found: J2's trigger words now include "control"
  and "button" (passed 5 names its control only that way), and A4 now
  asks that each element's own box overlaps changed pixels (a tag rule
  failed inapplicable 5, a page that is only a changing number).
- Judge eval run 15 (`evals/README.md`): 10/10, no false PASS, after 2.C
  J1 got its image (pass T's first frame), box and position in words.
  Follow-up: J1's wording when the mechanism is text naming a key.

Not started: the media store (items 13-14), the scrolled watch, loudness and `ImageDecoder`, 2.B and
2.A (`t2b.py`, `t2a.py`), the vendored ACT cases for 2.A (4c31df, 80f0bf, aaa1bf), the walk
cross-check (A2), and 2.D's note for `aria-live="off"`
carousels (plan risk 11).

## Code changes

| Where | Change | Plan |
| --- | --- | --- |
| `capture.py` | Note cross-site frames while recording (`Capture.cross_site_frames`). Media store: save media bodies in full, up to 50 MB and 15 s per page; serve their byte ranges on replay (a route registered after `route_from_har`). Size files over the cap from `Content-Length` or `Content-Range` | Q9, Q11; items 13–14 |
| `capture.replay_context` | Accept extra init scripts (pass T's mutation log, timer and Web Audio hooks); `traverse.py` untouched | Q7 |
| `browser.py`, `pipeline.py` | When the configured browser is `"chromium"` and the recording has cross-site frames, replay in full Chromium (`channel="chromium"`). A second, headless, full-Chromium browser with `--autoplay-policy=no-user-gesture-required` for pass T and the probes. Pass T starts beside P1. Extra time for pages with a region. The report records which browser replayed the page | Q1, Q2, Q11 |
| `motion.py` (new) | Pass T: frames, tile diff by overlap in every frame, regions and kinds, reads, timer hints, polling from the HAR, live regions, dialogs, focus log, elements with the Q6 rules, the scrolled watch. The mechanism probe | Q3, Q6 |
| `site.py` | Nothing changes for 9.x; `motion.py` reuses `UNITS_FN` and adds the label rule, `aria-hidden` and inline iframe content in its own reader | Q6 |
| `checks/t2c.py`, `t2d.py`, `t2b.py`, `t2a.py` | Rows from the specs; registered in `tests/drafts.py` until 1.0.0 | |
| `t4e._DIALOGS_JS` | Move to a shared module for 2.D | |

## Fixtures

Vendored first (`tests/fixtures/act/sync_act.py`; expected outcomes in
`fixtures/act/manifest.json`):

- **ACT efbfc7 (11 cases; DHS scored all 11 under 2.C).** While the ER 3
  gate holds (2.C section 3c), our expected outcomes differ from DHS's on
  the five passed cases:
  - passed 1–3: E3, NEEDS REVIEW (the control works; 6.A, 13.C and 18.A
    are not built);
  - passed 4 (a frequency field that needs a value): K5;
  - passed 5 (a dialog of controls): K5.

  Failed 1 is FAIL (K6). The five inapplicable cases are DNA. Report the
  difference as "gated", not as disagreement.
- **ACT 4c31df, 80f0bf and aaa1bf** (2.A; media assets via
  `sync_act.py`). Expected outcomes follow the rules, not ACT's alone: the
  silent video is not audio (loudness), and native controls in the top
  window are candidates.

No Baseline Alignment cases exist for any of these tests.

Custom pages in `tests/fixtures/2x/` (starting points:
`docs/research/2026-11-03-2x-experiments/pages/`):

| Case | Covers |
| --- | --- |
| carousel-pause | 2.C K3 then E3 (gated); 2.B the same; 2.D N5 |
| carousel-focus-pause (Slick-style pause on focus, no pause button) | K2 for 2.B and 2.C, never PASS |
| carousel-slow (a slide every 10 s) | 2.C A2 (timer hint) |
| ticker-polling (fetches every 2 s) | 2.C A2 (polling) |
| ticker-live (`aria-live="polite"`) | 2.D N2 PASS; 2.C K6 FAIL (no pause) |
| apg-carousel (`aria-live="off"` while rotating) | 2.D N5, with its note |
| update-moves-focus | 2.D J1 |
| update-dialog | 2.D J2 |
| timer-role (`role=timer` countdown) | 2.D N2, with its note |
| only-content (a page that is just a clock) | 2.C A4, 2.B A3 |
| css-infinite, css-3s | 2.B moving; not moving |
| gif-loop, gif-once | 2.B by G152; not moving |
| marquee | 2.B moving, K6 |
| color-toggle-2 (red and black every 0.5 s, no control) | 2.B K6 FAIL (two-state blinking) |
| color-cycle-4 (four colors every 1 s, no control) | 2.B C1 NEEDS REVIEW |
| canvas-raf | 2.B moving (pixels only) |
| spinner-2s, spinner-forever-with-controls | Not moving; 2.B J1 essential guard |
| video-muted-loop | 2.B moving; 2.A DNA |
| audio-autoplay-pause-first | 2.A K3 then E3 (gated) |
| audio-autoplay-pause-fifth | 2.A K6 FAIL (outside the top window) |
| audio-hotkey-text ("Press Ctrl+Shift+P to stop the sound" as the first element, and the key works) | 2.A J2 then K4 |
| audio-silent-track | 2.A DNA (loudness) |
| audio-in-iframe (cross-site) | 2.A in a frame; Q11 full Chromium |
| video-large-ranges (generated, > 5 MB, several ranges) | Media store; A2 over cap with the rerun offer |
| elements-count (labels stacked and on one line, a data table, an `aria-hidden` block, an iframe, images with and without alt) | The element count (Q6), checked on its own |

## Browser behavior to verify in code

The scratch scripts in `docs/research/2026-11-03-2x-experiments/` checked
most of these on Linux. Each becomes a test with local fixtures and no
network.

| ID | Verify | Rules that depend on it | Status |
| --- | --- | --- | --- |
| V1 | Tab reaches a `<video controls>` element's own buttons in Chrome, and Enter or Space on its play button pauses it | 2.A native controls | Not checked |
| V2 | Autoplay plays on replay only with the flag (item 1); loudness from bytes separates silent from audible (item 4); muted and short audio are not instances | 2.A Terms, A3 | Flag: test (`test_autoplay_plays_only_in_the_motion_browser`; a page's own `play()` on a script-made blob plays even without it, so the test uses `<audio autoplay src>`); loudness and instances not built |
| V3 | `ImageDecoder` gives frames, loops and duration for GIF, APNG and WebP (item 8); pixel diffs separate still-moving from stopped-before-5 s (item 6) | 2.B Terms | Checked (scratch) |
| V4 | Timer hooks catch a period longer than the watch (item 7); the scrolled watch sees a below-the-fold animation | 2.C A2, 2.B | Hook: test (`test_kinds`, a 10 s interval); scrolled watch not built |
| V5 | Polling repeats the first response on replay, and the HAR lists every poll (item 10) | 2.C A2 | Test (`test_polling_is_in_the_har`): the replay repeats the first response; the HAR held only one or two polls (recording stops at network idle), so pass T also counts requests during the watch |
| V6 | Slick and Splide pause on focus and resume when it leaves; four of six libraries pause on hover (item 12). Vendor the libraries for the fixtures | 2.C K2 | Checked (scratch, libraries from the network) |
| V7 | Full Chromium puts cross-site iframes out-of-process; media state, pixels and Tab work through them (items 15–16); a shell recording replays in full Chromium (Q11) | Q11; 2.A–2.D in frames | Out-of-process and replay: `tests/test_full_chromium.py` (main); pass T's regions, live regions and elements in such a frame: `test_cross_site_frame_in_full_chromium`; media and Tab in it not yet |
| V8 | A live region added in the same task as its text is told apart from one present at 0 s | 2.D Terms | Not checked |
| V9 | Home, End and arrows on a volume slider set the media's volume to 0 | 2.A | Not checked |
| V10 | Media fetched in several ranges fails on replay, and the media store fixes it (items 13–14) | 2.A, 2.B A1 | Checked (scratch) |
| V11 | Pass T beside P1 does not slow the walk (item 18), and a second headless browser beside a headed walk takes no focus | Q2 | Linux checked; Windows headed not |
| V12 | Windows headed Chrome: autoplay with the flag; the walk unaffected by the second browser | Q1, Q2 | Not checkable from Linux |
| V13 | The element rules: labels on one line merge, stacked labels do not; `aria-hidden` content and alt-less images are skipped; iframe content counts inline | Q6 | Test (`test_elements`) |

## At 1.0.0 (each test)

- CLAUDE.md:
  - principle 8's list gains 2.B J2, 2.C J1, and 2.D J1 and J2 (settled
    by looking);
  - principle 5 gains the Q10 exception (pressing a key combination named
    in page text);
  - "Other rules" gains Q11 ("Replays of pages with cross-site iframes run
    in full Chromium, never the headless shell");
  - Layout gains `motion.py` and the checks.
- `docs/hackathon/evaluation.md` and the matching deck slide: the tests,
  spec versions and the ACT efbfc7 comparison (gated cases reported
  apart).
- The judge eval on every question (J1, J2 of 2.C; J1 of 2.B; J1, J2 of
  2.D).
- `docs/solutions/`:
  - pass T and why it is its own load;
  - autoplay on replay;
  - the media store;
  - the shell's in-process iframes;
  - the element count.
- ROADMAP: remove 2.B–2.D from "Next".

## Left

- V1, V4 (scrolled watch), V8, V9 and V11 above; V12 needs Windows.
- Real YouTube and Vimeo embeds on a normal network (plan item 17).
- The ER 3 shortlist (6.A, 7.A, 7.E, 12.D, 13.A, 13.B, 13.C, 18.A) before
  any of 2.A–2.C can PASS.
