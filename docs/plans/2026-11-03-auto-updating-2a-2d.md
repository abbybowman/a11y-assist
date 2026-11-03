# Plan: 2.A–2.D Auto-playing and auto-updating content (2026-11-03, approved; specs at 0.1.0)

Approved by Abby on 2026-11-03. The draft specs are
[2c-auto-updating.md](../rules/2c-auto-updating.md), which defines pass T,
elements and the mechanism probe for the batch;
[2d-change-notify-auto.md](../rules/2d-change-notify-auto.md);
[2b-blinking-moving-scrolling.md](../rules/2b-blinking-moving-scrolling.md);
and [2a-audio-control.md](../rules/2a-audio-control.md). All are at
0.1.0, and the build checklist is
[2c-build-tasks.md](../rules/2c-build-tasks.md). Nothing is built yet.
The specs now hold the rules; this plan keeps the research, the
measurements and the order of work.

**Decided (Abby, 2026-11-03):**

- **Q1:** a second, headless, autoplay-allowed browser for pass T and the
  mechanism probes (full Chromium, Q11).
- **Q2:** pass T runs in parallel with the walk, which changes
  `pipeline.py`. Pages with moving content get extra time.
- **Q5:** browser tab mute does not satisfy 2.A.
- **Q6:** elements are what a screen reader reads as one unit, in reading
  order, not tab order. That means text, headings, images with alt text and
  controls. A control and its label are one element when they share a
  line, and two when the label is stacked above. Each data-table cell is
  one element. An iframe's content counts inline. Images without alt text,
  and content hidden from assistive technology, do not count.
  "Before/after" is counted around the whole carousel, its own controls
  included.
- **Q3:** watch 6.5 s at the top, plus one scrolled watch only when hints
  are below the fold.
- **Q4:** ER 3 ("the mechanism passes all applicable Test Conditions")
  stays NEEDS REVIEW until the tests it needs are built. See "ER 3: the
  tests a mechanism needs" for the shortlist.
- **Q7:** `replay_context` takes extra init scripts; `traverse.py` is
  untouched.
- **Q8:** 2.C and 2.D first, then 2.B, then 2.A.
- **Q9:** the media store keeps up to 50 MB and 15 s per page. Over the
  cap, the result gives each file's size and length and offers a run with
  no media limit.
- **Q10:** a key combination named in page text may be pressed, as an
  approved exception to principle 5, within the limits in Q10 below.
- **Q11:** replays run in full Chromium only for pages whose recording
  has cross-site iframes (when the configured browser is `"chromium"`).
  Pass T and the 2.x probes always use full Chromium.

Nothing is left open in this plan. Questions that come up while building
go in the specs as OPEN marks.

The experiments behind every "verified" below are in
[research/2026-11-03-2x-experiments/](../research/2026-11-03-2x-experiments/README.md).
They are scratch scripts that can be rerun, not tests.

## Sources read

| Source | 2.A (1.4.2) | 2.B / 2.C (2.2.2) | 2.D (4.1.2) |
| --- | --- | --- | --- |
| TT 5.1.3 | pp. 13–18 (`md/02-auto-playing-and-auto-updating.md`; Appendix B: 5.1.3 changed setup to "browser **not** set to block autoplay", and 2.B to an "evident" mechanism) | same | same |
| TT 5.0 (2019 PDF) | Same "three elements" wording, but setup said "configured to **disable** auto-play" | same wording | — |
| DHS TT course, public issue tracker and FAQ wiki ([DHSA-TT-200-A](https://github.com/Section508Coordinators/DHSA-TT-200-A); 2019–2020; issues and wiki only, no license, course itself behind a login) | [Wiki](https://github.com/Section508Coordinators/DHSA-TT-200-A/wiki/Element-to-Pause-or-Stop-Audio-or-to-Control-Volume) and #114: "Mechanism is specifically defined to include any element, including text or images. For example, text could be an effective element to provide a keyboard shortcut…" | #203: a pause control "within three elements of the video" passes 2.B; #425: a working disable-animation button passes 2.B | [Wiki](https://github.com/Section508Coordinators/DHSA-TT-200-A/wiki/2.D-ARIA-Live-Region-in-Change-Notification-(Auto-updating)): "You are not required to make any other determination except whether change notification appears within the live region." |
| W3C Understanding | [Audio Control](https://www.w3.org/WAI/WCAG22/Understanding/audio-control.html) | [Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) | [Name, Role, Value](https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html) (notification of changes); [Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) for contrast only |
| Sufficient | G60, G170 (control near the start), G171 | G4 (pause, does not restart, resumes), G11, G152 (GIF: frames × delay × loops ≤ 5 s), G186 (control stops it), G191, SCR22, SCR33 | ARIA19/22/23 (via 4.1.3) |
| Failures | F23, F93 (autoplay, no `muted`, > 3 s, no control) | F16, F50, F7, F112 (F4, F47, G187 obsolete) | F103 (4.1.3) |
| W3C ACT | 80f0bf (composite), 4c31df (control), aaa1bf (≤ 3 s): all proposed; 8, 11 and 7 cases | **efbfc7** (text that changes automatically): 11 cases | none |
| DHS ACT data (act-tt, checked 2026-11-03) | none scored | **efbfc7: all 11 cases scored under 2.C, all agree with ACT** (5 pass, 1 fail, 5 inapplicable) | none |
| ICT Testing Baseline 3.1 | [21.D-AudioControl](https://ictbaseline.access-board.gov/web-baselines/21TimedEvents/): the mechanism is "at the beginning of the page content or in platform accessibility features" | 21.B-MovingInfo, 21.C-AutoUpdate (essential excluded; no "three elements" rule) | No changing-content baseline (Baseline 5 is User Controls) |
| Baseline Alignment cases | none | none | none (no TC05 or TC21 cases) |

No source defines how the "three elements" are counted. A search found
nothing on tab order versus reading order, or on carousels:

- the TT site and its GitHub repos;
- the TT 5.0 and TT 4 PDFs;
- the DHS course's issues and wiki (23 pages);
- section508.gov and dhs.gov;
- DHS's ACT report.

DHS's current Q&A board is inside the course's Moodle, so it is not public.
The only written ruling is #114: any element, text or images included, can
be the mechanism.

What the sources settle, so it is not asked:

- **2.C has no "essential" judgment.** TT says to include all auto-updating
  content (p. 16 note), unlike 2.B, which excludes essential motion.
- **A pause that holds only while the control has focus is not a mechanism**
  (Understanding 2.2.2: it must not "tie up the user or the focus").
- **The control must stop the content for good.** G4 and SCR33: after
  pausing, it does not restart by itself.
- **A carousel is auto-updating** (2.C). It is also 2.B when its slides
  visibly move. TT's own note says both apply.
- **Starting when scrolled into view, or on hover or focus, counts as
  starting automatically** (Understanding 2.2.2).
- **Muting the system volume is not a mechanism.** Reducing a volume control
  to zero is (Understanding 1.4.2).
- **The ICT Baseline says to disable autoplay before testing. TT 5.1.3 says
  the opposite on purpose:** TT 5.0 said "disable" and 5.1.3 changed it. TT
  is the authority, so we allow autoplay.
- **2.D's live-region path is mechanical** (the DHS wiki above). Only the
  focus-move and dialog paths need a look.

## Verified in this container

Linux, 4 CPUs, Playwright 1.63. "Shell" means Playwright's default headless
shell, which the test suite uses. "Full" means full Chromium in new-headless
mode (`channel="chromium"`), which behaves like installed Chrome. Each item
becomes a V-check in the build tasks.

**Autoplay and audio**

1. **Autoplay audio does not start on replay with default settings.** Three
   `<audio autoplay>` elements (WebM/Opus, MP3, WAV) played live but stayed
   paused at 0 on HAR replay. With `--autoplay-policy=no-user-gesture-required`
   they play on replay, and an `AudioContext` runs. Without the flag, 2.A
   would be DOES NOT APPLY on every page. The flag is TT's own setup step.
   Why the live load and the replay differ is unknown.
2. **Headless Playwright adds `--mute-audio`, but playback still advances.**
   `webkitAudioDecodedByteCount` shows decoded audio.
3. **H.264/AAC MP4 plays** in the shell, live and on replay, as VP9/Opus
   WebM does.
4. **Loudness from the recorded bytes, with no new dependency.** ACT's own
   "silent" video has a real audio track (Vorbis at -91 dB), so track
   presence would give a false FAIL. Chromium's
   `OfflineAudioContext.decodeAudioData` on the bytes tells them apart:
   silent peaks at -180 dBFS with no samples above -40 dB; audible files
   peak at -10 to -12 dBFS.
5. **A Web Audio hook works.** An init script wrapping
   `AudioNode.prototype.connect` counted the oscillator connected to
   `destination`.

**Motion and updates**

6. **Pixel differences classify motion; DOM signals do not.** One page had
   twelve kinds of motion. Screenshots every 0.5 s for 6.5 s (75 ms each),
   diffed in 20 px tiles:
   - **Still changing after 5 s:** an infinite CSS animation, a marquee, a
     looping GIF, a canvas drawn with `requestAnimationFrame`, a muted
     looping video, a ticker updated every 1 s, and news scrolled with
     `scrollLeft`.
   - **Stopped before 5 s:** a 3 s CSS animation, a play-once GIF, and a
     spinner removed at 2 s.
   - **Never changed:** a focused text field (Playwright hides the caret).

   DOM mutations missed most of these: the marquee, GIF, canvas, video,
   CSS animation and `scrollLeft` ticker gave at most a mutation or two
   each. `getAnimations()` saw only the CSS animation. One fault: mapping a
   tile to an element by its centre missed edge tiles, so the build maps by
   overlap.
7. **A 6.5 s watch misses slower updates, but a timer hook catches them.**
   A slide changing every 8 s showed no change, but the `setInterval`
   wrapper recorded its 8000 ms period. Timer hooks run before page
   scripts.
8. **`ImageDecoder` reads animated images** (GIF, APNG, animated WebP:
   frames, loops, duration per loop). That is G152's computation.
9. **`<blink>` and `text-decoration: blink` do not blink in Chrome.** They
   are not 2.B content there; results are per browser.
10. **Polling freezes on replay.** A counter fetched every 0.7 s went 1, 2,
    3, 4, 6 live and stayed at 1 on replay: the replay answers every repeat
    with the first recorded response. The HAR still lists every poll, so
    polling is detectable without a load.
11. **`prefers-reduced-motion` is `no-preference`** in a default context, so
    pages show their normal motion.

**Carousels** (the libraries' defaults, autoplay 1.5 s, measured from
pixels):

12. **Two of six common libraries pause when focus is on their own
    Previous button,** with nothing pressed, and resume when focus leaves:

    | Library | Pauses on focus | Pauses on hover |
    | --- | --- | --- |
    | Slick 1.8.1 | **yes** | yes |
    | Splide 4.1.4 | **yes** | yes |
    | Swiper 11.1.14 | no | no |
    | Bootstrap 5.3.3 | no | yes |
    | Glide 3.6.0 | no | yes |
    | Flickity 2.3.0 | no | yes |

    The focus-only control probe and "watch after focus leaves" are
    required. The mouse must never be over the page, which a headless
    browser guarantees and a headed one does not.

**Media in recordings**

13. **Large media does not replay.** A 21 MB video was fetched live in
    three byte ranges. The browser cancelled the open-ended `bytes=0-`
    request when it seeked, so the HAR saved two ranges with no body and
    the whole HAR was 22 kB. On replay the video failed with error 4 and
    never played. Small files, fetched in one range, replay fine.
14. **Fix, verified:** during recording, also fetch each media URL once in
    full through the context's request API (4.2 s for 21 MB locally). On
    replay, answer byte-range requests for those URLs from the saved body,
    with a route registered after `route_from_har`. The video then played
    from its 40 s seek point, with audio. It needs a size cap and a time
    cap.

**Iframes** (TT and ANDI treat each iframe as its own page):

15. **The shell runs cross-site iframes in-process.** Full Chromium runs
    them out-of-process (3 iframe targets), as installed Chrome does. So the
    default test suite never exercises the out-of-process path. 2.x
    fixtures with media in iframes should also run with
    `channel="chromium"`, which needs no installed Chrome.
16. **In full Chromium, with out-of-process iframes:**
    - Media state in a cross-site iframe can be read with `frame.evaluate`.
      The video was playing at 9.2 s, live and on replay.
    - Screenshots capture motion inside the iframe.
    - Tab went from "Top link" straight to the iframe's Pause button, and
      Enter paused the video.

    So pass T and the probes work through iframes. CDP's `Media` domain
    reported no players from out-of-process frames, on the page's session
    or on the frames' own sessions, so pass T reads media state per frame
    instead.
17. **Real YouTube and Vimeo embeds did not play even live** in this
    container: YouTube stayed paused at 0, and Vimeo started but did not
    advance. Their segment requests failed through the sandbox's proxy, so
    this says nothing about a normal network. They stream (MSE) like item
    13, so they need the item 14 store or a "not performed" result.

**Time** (item 18):

18. **A parallel watcher does not slow the walk.** `time_budget.py
    budget/agency-home.html` was run alone, then beside a second headless
    browser screenshotting every 0.5 s for the whole run:
    - Walk: 45.8 s alone, 43.9 s with the watcher.
    - Total: 102.5 s alone, 99.8 s with the watcher.

    One run each. Headed Chrome on Windows is not checked.

## What the tool would do (one shared collector, four checks)

### Why pass T needs its own load, and what it takes from the others

Pass letters name a purpose, not a count. Today there are seven: P1 and P2
(the walk), W (4.D widgets), R (4.F reveals), F (5.D fills), E (5.F
errors) and L (5.A–5.C labels). T is for time.

Each of those loads presses a key within about a second. TT's question is
what the page does **with no input for more than 5 s**. Watching during P1
would be free, but P1's focus reaches a top carousel within a few presses,
and Slick and Splide pause on focus (item 12). We would see the carousel
stop and call it shorter than 5 s: a false DNA. Delaying P1's first press
by 6.5 s adds 6.5 s to every run. So pass T is one extra load, at the same
time as P1, at no measurable cost (item 18).

What it takes from evidence that already exists, at no extra cost:

- **The HAR (no load):** media bytes for loudness (item 4), animated image
  bytes for G152 durations (item 8), and repeated requests for polling
  hints (item 10).
- **The walk:** the first stops (P1), the tab order around each region, and
  the replay plan for every probe. The per-step `mutations`, `unsettled`
  and 4.D's `getAnimations()` reads are a free cross-check: if the walk saw
  changes but pass T saw none, the result is NEEDS REVIEW, not DNA.
- **4.A's Enter and Space presses** (`observe.py` measures page noise for
  300 ms before and after each): a control after which the noise stops is
  tried first. That only orders candidates; it never decides.

What stays new: the mechanism probes. A candidate is rejected as soon as
the region changes again (within one of its own update periods, measured by
pass T). Only a candidate that holds gets the full 5.5 s watch and the
focus-only control probe. A page with nothing moving pays only pass T.

### Pass T: watch the page over time (new, `motion.py`)

One fresh load of the recorded page with no input, watched for 6.5 s. It
runs in a second, headless browser with the autoplay flag (Q1; full
Chromium, Q11), so the
walk's browser and every other test's evidence are unchanged. In headed
runs, a second window could take focus from the walk; a headless browser
opens no window and has no pointer over the page (item 12). TT's
thresholds are "more than 5 seconds" (2.B) and "more than 3 seconds" (2.A).
Pass T records facts only:

- **Frames:** a screenshot every 0.5 s through `traverse.screenshot()` (the
  time-budget trap), diffed by tile. Tiles map to elements by overlap and
  `elementsFromPoint`, in every frame (items 6 and 16).
- **DOM:** a mutation log with targets, from an init script (Q7). Today's
  `INIT_JS` only counts mutations, and `traverse.py` stays frozen.
- **Animations:** `getAnimations()` sampled: target, iterations, duration,
  play state.
- **Media,** per frame through `frame.evaluate`, not CDP `Media` (item 16):
  paused, muted, volume, `currentTime` progress, duration, loop, `error`,
  and decoded bytes. Loudness comes from the recorded bytes, decoded in a
  tool page, never the tested page (item 4). `AudioContext` use comes from
  the connect hook (item 5).
- **Animated images:** G152 durations from `ImageDecoder` on the recorded
  bytes.
- **Hints only:** `setInterval` and long `setTimeout` periods (item 7),
  polls in the HAR (item 10), carousel markup
  (`aria-roledescription=carousel`, library classes).
- **For 2.D:**
  - live regions present before each change, using ANDI's own set:
    `aria-live` polite or assertive, and roles `alert`, `status`, `log`,
    `marquee`, `timer` (`sandi.js`), read per frame;
  - dialogs, through `t4e._DIALOGS_JS`;
  - focus moves, from the existing focus log.

**Recording change (`capture.py`):** save media bodies in full, within a
size and time cap, and serve their byte ranges on replay (items 13–14).
Media over the cap leads to "not performed", never DNA.

**Classification (rows, in the spec).** A region is *moving* (2.B) when its
pixels change but its text and image sources do not. It is *auto-updating*
(2.C, 2.D) when its text, image sources or children change. It can be
both. It is excluded as the only content when nothing outside the regions
has visible text.

### Mechanism probe (2.A–2.C; reuses `ctx.replay`, `observe.py`)

TT's How to Test is "determine if there is a mechanism… within three
elements, activate it, and test it".

1. **Candidates, by position and never by name** (icon-only pause buttons
   have empty names). Positions are counted in *elements*: the units of
   `site.UNITS_FN` in reading order, with a label that names a control
   merged into it (Q6). Reading them costs one `evaluate` on pass
   T's load.
   - **2.A, 2.B and 2.C:** the first three elements of the page.
   - **2.B and 2.C, also:** the content is the whole carousel, ticker or
     player, its own controls included. Candidates are every element inside
     it, the three elements before its first element, and the three after
     its last.
   - **Controls** among the candidates are pressed (step 2).
   - **Text and images** among them may be the mechanism ("any element,
     including text or images", DHS #114). They go to a
     by-looking question: does this describe a way to pause, stop or hide
     it? If the text names a key combination, the combination is pressed
     to confirm (Q10).
2. **Activation.** Operable controls only (buttons, `role=button`,
   switches, checkboxes, sliders, and `href="#"` links), with Enter or
   Space, through `observe.py`. A slider gets arrow and Home/End presses
   (volume to zero). Controls inside iframes are reached by Tab as usual
   (item 16).
3. **Confirmation, on a fresh load each time.** After activating, focus
   moves off the control, and the region is watched for 5.5 s. It counts
   as stopped only if it stays still (G4: no restart), is hidden, or its
   audio is paused, muted or at volume 0.
4. **The focus-only control probe.** The same replay, landing on the control
   without activating it. If the region stops then too, the stop came from
   focus, so the result is NEEDS REVIEW, never PASS. Slick and Splide would
   otherwise turn their own Previous button into a false PASS (item 12).

A key press must confirm the mechanism (principle 8). Even then, 2.A–2.C
stay NEEDS REVIEW until ER 3 can be checked (Q4, below).

### ER 3: the tests a mechanism needs (Q4)

ER 3 asks that the mechanism pass "all applicable Test Conditions in this
test process". Until each test that can apply to it is built, a confirmed
mechanism gives NEEDS REVIEW. The note says the mechanism works by keyboard
and names the tests a person must still check it against. FAIL is
unaffected: no working mechanism is FAIL whatever ER 3 says. Names are from
`tt.json`.

| Test | Applies to the mechanism when | Built |
| --- | --- | --- |
| 4.A keyboard access | always (it is operated) | yes |
| 4.B no keystroke timing | always | yes |
| 4.C no keyboard trap | always | yes |
| 4.D focus visible | it takes focus | yes |
| 4.E on focus | it takes focus | yes |
| 4.F focus order | it takes focus | yes |
| 5.A label provided, 5.B label descriptive, 5.C programmatic label, 5.D on input | it is a form element (a toggle, a volume slider, a frequency field) | yes |
| 6.A link purpose | it is a link or a button | **no** |
| 7.A meaningful image name, 7.E image of text | it is, or contains, an image or icon | **no** |
| 12.D iframe name | it is inside an iframe | **no** |
| 13.A color meaning | its state (playing or paused) is shown by color | **no** |
| 13.B sensory info | it is a text instruction ("press the red button") | **no** |
| 13.C contrast | it has text, or is text | **no** |
| 18.A resize text | it has text, or is text | **no** |

The shortlist to build before 2.A–2.C can PASS: **6.A, 7.A, 7.E, 12.D,
13.A, 13.B, 13.C and 18.A**. Each one only for the mechanisms it applies
to: a plain text "Pause" button needs 6.A, 13.A, 13.C and 18.A, not 7.x or
12.D. Until then, ER 3 is read from this run's findings for the built tests
at the mechanism's element. A FAIL there is shown in the note, and the
result stays NEEDS REVIEW.

### Per test

The PASS column applies once Q4's shortlist is built. Until then, a row
that would PASS gives NEEDS REVIEW.

| Test | Applies when (DNA otherwise) | PASS | FAIL | Open questions (by rubric) |
| --- | --- | --- | --- | --- |
| **2.A** Audio control | Media or Web Audio makes audible sound (item 4) for more than 3 s on load | A candidate among the first three elements pauses, stops or mutes the audio (confirmed by a key press) | Audible for more than 3 s, every control candidate probed, none stops it, and J1 says no text or image candidate describes a mechanism | J1: does a text or image candidate describe a mechanism (by looking)? |
| **2.B** Moving, blinking, scrolling | A region still changing at 5 s from load, or with more than 5 s of animation (CSS, G152). Excluded: the only content; essential (J1) | A candidate in either window stops, pauses or hides it (confirmed by a key press), and J2 says it is evident | Every control candidate probed with no effect, and J3 says no text or image candidate describes a mechanism | J1: essential (a spinner during load, a game)? J2: is the mechanism evident (by looking)? J3: as 2.A's J1 |
| **2.C** Auto-updating | Text, image sources or children change without input. Excluded only as the only content (TT: never as essential) | As 2.B, or a frequency control changes the period | As 2.B | J1: evident (shared with 2.B when it is the same control) |
| **2.D** Change notification | The changes 2.C found | Every change is inside a live region that existed before it (mechanical; DHS wiki) | A change with no live region, no focus move to it and no dialog | J1: after focus moved to the changed content, does that content describe the change? J2: does the dialog give enough notice? |

**Not performed (NEEDS REVIEW, "This test could not be performed").**

- Media that failed to play, or was over the recording cap (Q9: the note
  gives each file's size and length, and the result offers a run with no
  media limit).
- Third-party streaming players (item 17).
- Polls found in the HAR (2.C and 2.D can't see new data).
- Hints of updates slower than the watch.
- Web Audio with no bytes to measure.

The test is never DNA on these, and each note says what a person should
check.

## Reuse versus new code

| Reused as is | Where |
| --- | --- |
| Recording and HAR replay, the fresh context per load, the egress and navigation guards | `capture.py`, `browser.py` |
| `ctx.replay`, `ctx.out_of_time()`, the replay plan; P1's stops and tab order | `checks/base.py`, `walk.py` |
| Key activation with before and after effects, and its noise measure | `observe.py` |
| Screenshots that pause the mutation log; the focus log; `PATH_JS`; focus into out-of-process iframes (V5) | `traverse.py` (read only) |
| Dialog detection | `t4e._DIALOGS_JS` (move to a shared module) |
| "Region present before the change" | `t5f` (`_LIVE`, `live`), widened to ANDI's set |
| Elements in reading order, for "three elements", plus the label merge | `site.UNITS_FN` (9.A–9.C, 19.A), unchanged; the merge is a few lines in the 2.x reader |
| Rows, findings, questions, `shared_inputs`, `run://` links, resume and answers | `engine.py`, `models.py`, `judgment.py` |
| The harness, the judge eval, `sync_act.py` (fetches `test-assets/` already), the time budget | `tests/`, `evals/` |

| New or changed | Estimate |
| --- | --- |
| `motion.py`: pass T (frames, tile diff by overlap, region mapping in every frame, mutation targets, animations, per-frame media, loudness, `ImageDecoder`, hints) | ~450 lines; the biggest piece |
| Mechanism probe (Q6 windows, text candidates, sliders, rejection by period, the confirm watch, the focus-only control) | ~250 lines |
| `t2a.py` to `t2d.py` (rows, plain text, questions) | ~250–400 lines each; 2.C smallest |
| `pipeline.py`: a second autoplay browser; pass T started beside P1; the extra time for moving content (Q2) | ~60 lines |
| `capture.py`: the media store and its byte-range route (items 13–14) | ~80 lines |
| Init-script hook for pass T (Q7) | small |
| Specs ×4, build tasks, ~20 custom fixtures (plus `channel="chromium"` runs for the iframe ones), one budget page with a carousel, a ticker and a video | — |

Roughly a third is reuse, less than 5.x or 9.x had, because nothing yet
watches a page over time without input. Pass T is the new foundation. Later
it can serve 3.A (DOES NOT APPLY when nothing changes; 0.5 s frames are too
slow to count flashes), 8.A timeouts and the ROADMAP's 4.E dialog work. The
media store also helps 16.x and 17.x (media tests), whose videos would
otherwise not replay either.

## Where agent-driven testing could fail

Ordered by harm. A false PASS or a false DNA is worse than NEEDS REVIEW.

| # | Failure | Result if unhandled | Mitigation | Left over |
| --- | --- | --- | --- | --- |
| 1 | Replay blocks autoplay (item 1) | 2.A DNA on every page | The autoplay browser (Q1) | Headed Chrome on Windows |
| 2 | **Large or streamed media is not in the HAR** (item 13) | 2.A and 2.B DNA for most real video | The media store (item 14); over the cap → not performed | Real YouTube/Vimeo on a normal network (item 17) |
| 3 | **A carousel pauses on focus** (Slick, Splide; item 12) | **False PASS** (2.B, 2.C) | Watch after focus leaves; the focus-only control probe | Pages that pause on any keydown |
| 4 | Updates slower than the watch, or starting only when scrolled into view | False DNA | Timer hooks (item 7), polls, carousel markup → NEEDS REVIEW; one scrolled watch when hints are below the fold (Q3) | Long timers with no hint |
| 5 | **Replay gives polling requests the same data** (item 10) | 2.C and 2.D false DNA | Polls in the HAR → NEEDS REVIEW | — |
| 6 | Silent audio tracks (item 4), or Web Audio that makes no sound | 2.A false FAIL | Loudness from the bytes; Web Audio → NEEDS REVIEW | — |
| 7 | Out-of-process iframes in real Chrome, never exercised by the shell (item 15) | Code that works in tests fails for users | Per-frame reads (item 16); iframe fixtures also run with `channel="chromium"` | — |
| 8 | Pixel noise: font loading, late images, hover styles | False 2.B applicability | Only regions still changing at 5 s count; the caret is hidden (item 6); no pointer on the page | Video ads |
| 9 | Moving or updating misclassified (fades, sliding carousels) | Wrong test applied | Both apply when both signals are present (TT's note); fades go to J1 | — |
| 10 | Judge errors on "evident", "essential", "only content", 2.D "sufficient description", text mechanisms | Wrong PASS from a judgment | Only by-looking questions lead to PASS, with "unsure" required; frame strips and before/after crops (one frame cannot show motion); page text is untrusted (principle 5) | Judge eval |
| 11 | W3C's own carousel pattern (APG) sets `aria-live="off"` while it rotates, to avoid an announcement every few seconds | TT 2.D gives FAIL: no live region, no focus move, no dialog | Follow TT (principle 7); the plain explanation says why, and that pausing the rotation turns announcements on | — |
| 12 | ANDI counts `role=marquee` and `role=timer` as live regions (their implicit `aria-live` is off) | 2.D differs from ARIA | Match ANDI, as TT prescribes; note it | — |
| 13 | Autoplay for the whole run would change other tests' evidence (4.D's noise read cannot see playing video) | 4.D false focus indicator | Autoplay only in the second browser (Q1) | — |
| 14 | Random and clock-driven pages | Flaky fixtures | Hand-built evidence for timing rows; Playwright's clock in tests only | — |

## Time budget

- **Pass T: ~7 s, beside P1, no measurable cost** (item 18). The agency
  page is at 102.5 s of 110 here (108 s on the machine in the ROADMAP), and
  it has no moving content.
- **Probes:** ~1–2 s replay, then a rejection within one update period, or
  5.5 s confirm + 5.5 s control for the candidate that holds. Pages with
  moving content get an extra allowance (Q2, decided; e.g. +20 s, as
  `OTHER_PAGE_S`).
- **Media store:** one full fetch per media URL while recording, up to
  50 MB and 15 s per page (Q9; 4.2 s for 21 MB on loopback, and real
  networks are slower). The size of a file over the cap is known without
  downloading it, from `Content-Length` or the total in `Content-Range`.
  Its length comes from the element's `duration` once its metadata has
  loaded. The result states both, and the tool offers a run with no media
  limit. Recommended: lift the media cap with the existing `no_time_limit`
  option instead of adding a second option, since a long recording is
  also a long run.
- Add a budget page with a carousel, a ticker and a video, and measure with
  `time_budget.py --drafts`.

## Full Chromium instead of the headless shell (Q11)

Which browser runs where today:

- **Real runs:** installed Chrome (`browser_channel="chrome"`, the
  default), which puts cross-site iframes out-of-process.
- **Tests and `time_budget.py`:** `"chromium"`, which `browser.py` maps to
  Playwright's headless shell. The shell runs those iframes in-process
  (item 15).
- **A hosted, headless deployment** set to `"chromium"` would also get the
  shell, so it would differ from what users' Chrome does.

Measured 2026-11-03 on this container. A temporary local switch to full
Chromium (`channel="chromium"`) was used and not committed. Scripts:
`research/…/browser_costs.py`, `cross_browser_replay.py`.

| | Headless shell | Full Chromium |
| --- | --- | --- |
| Test suite (`pytest -n 4`) | 762 passed, 1 xfailed, **10.0 min** | 762 passed, 1 xfailed, **14.2 min (+42%)** |
| ACT and DHS agreement lines, mismatches | — | identical to the shell |
| `time_budget.py budget/agency-home.html` | 102.5 s | 102.6 s |
| Browser launch (median of 5) | 68 ms | 139 ms |
| New context, page and load (median of 15) | 61 ms | 151 ms |
| Tab press | 2.8 ms | 4.7 ms |

So full Chromium costs about 90 ms more per page load. A real run hides
that behind the walk's settle waits (~190 ms per press), which is why the
agency page came out the same. The suite makes thousands of short loads,
so there it adds up to +42%.

**Recording happens once, before any test, and its HAR does not depend on
the browser.** So the browser that replays it can be chosen after
recording. Verified: a page with a cross-site iframe was recorded in the
shell and replayed in full Chromium. The iframe was out-of-process, its
video played, and Tab, Tab, Enter reached its Pause button and paused it.
No request failed.

**The rule (decided):**

- **The recorder notes cross-site frames.** It lists the frames whose site
  differs from the top page's, while it loads the page (it already waits
  for the page to go idle and scrolls it). This becomes a new
  `Capture.cross_site_frames` field.
- **Choosing the replay browser.** When that list is not empty, and the
  configured browser is `"chromium"`, the replays run in full Chromium.
  Otherwise they keep the shell. Installed Chrome (`"chrome"`) is
  unaffected: it is already out-of-process.
- **Pass T and the 2.x probes always use full Chromium,** in the second,
  autoplay-allowed browser (Q1). That browser is separate anyway, its few
  loads make the ~90 ms negligible, and media and motion behave as in
  Chrome.
- **The report records which browser replayed the page,** as it records
  versions today.
- **What it costs.** Only pages with cross-site iframes pay the extra
  ~90 ms per load. In the suite that is the 17 fixture files with iframes
  (9 ACT cases, 8 custom pages), so CI should stay near 10 min (an
  estimate, not measured).
- **What is left.** A cross-site iframe that appears only after a click
  is not seen while recording. Its content is still reached, since V5
  handles in-process frames, but the replay runs in the shell. The walk
  can log any cross-site frame it meets, so this case shows in the
  report.

A rule for CLAUDE.md (approved; added when the change is built):
"Replays of pages with cross-site
iframes run in full Chromium, never the headless shell."

## Q10's limits (decided)

A key combination that page text names (for example, "press Ctrl+S to stop
the animation") may be pressed, as an approved exception to principle 5
like 19.A's search, and only:

- on a fresh replay load, with no live network;
- if the combination matches a fixed pattern (modifiers plus one key);
- never as a combination the browser itself uses (Ctrl+W, Ctrl+T, Ctrl+N,
  Ctrl+L, Alt+F4 …);
- once per run.

Only J1 (by looking) decides that the text describes a mechanism. The key
press only confirms that it works. CLAUDE.md records the exception when 2.B
is built.

## Order of work

1. V-checks as tests (fixtures served locally, no network): items 1–16 and
   18. Item 17 (real YouTube/Vimeo) and headed Windows can't be checked
   here.
2. Specs 2c, 2d, 2b and 2a at 0.1.0, and the build tasks (done,
   2026-11-03).
3. `capture.py` media store; `pipeline.py` second browser and parallel
   start; `motion.py` pass T and the probe; rows on hand-built evidence.
4. Fixtures:
   - ACT efbfc7 (11, with DHS verdicts), 4c31df, 80f0bf and aaa1bf (media
     assets via `sync_act.py`).
   - Custom pages in `tests/fixtures/2x/`:
     - carousels: one with a working pause; one that pauses only on focus
       (Slick-style); one changing every 10 s; the APG carousel;
     - updates: a ticker polling the server; a live-region ticker; an
       update that moves focus; an update announced by a dialog;
     - motion: an infinite CSS animation and a 3 s one; long and short
       GIFs; a marquee; a canvas with `requestAnimationFrame`; a loading
       spinner;
     - media: a muted looping video (2.B, not 2.A); a large video fetched
       in several ranges; media in a cross-site iframe (also run with
       `channel="chromium"`);
     - changing content as the only content;
     - our own pages for the element count: labels stacked and wrapping,
       data tables, layout tables and columns.
5. Checks registered in `tests/drafts.py`; the judge eval on every question;
   time with the new budget page.
6. 1.0.0 with Abby. In the same commit: ROADMAP; solutions (pass T, autoplay
   on replay, the media store, the shell's in-process iframes); CLAUDE.md
   layout; the hackathon evaluation and deck.
