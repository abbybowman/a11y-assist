# Plan: 2.A–2.D Auto-playing and auto-updating content (2026-11-03, proposed)

A proposal for Abby's review: nothing is built and no spec is drafted
yet. The open questions at the end come first, because several of them
decide rows. When the plan is approved, the rules go into
`docs/rules/2a-…` to `2d-…` (from `_template.md`, at 0.1.0), and this plan
keeps only the order of work.

## Sources read

| Source | 2.A (1.4.2) | 2.B / 2.C (2.2.2) | 2.D (4.1.2) |
| --- | --- | --- | --- |
| TT 5.1.3 | pp. 13–18 (`md/02-auto-playing-and-auto-updating.md`; Appendix B: 5.1.3 changed setup to "browser **not** set to block autoplay", and 2.B to an "evident" mechanism) | same | same |
| W3C Understanding | [Audio Control](https://www.w3.org/WAI/WCAG22/Understanding/audio-control.html) | [Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) | [Name, Role, Value](https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html) (notification of changes); [Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) for contrast only |
| Sufficient | G60, G170 (control near the start), G171 | G4 (pause, does not restart, resumes), G11, G152 (GIF: frames × delay × loops ≤ 5 s), G186 (control stops it), G191, SCR22, SCR33 | ARIA19/22/23 (via 4.1.3) |
| Failures | F23, F93 (autoplay, no `muted`, > 3 s, no control) | F16, F50, F7, F112 (F4, F47, G187 obsolete) | F103 (4.1.3) |
| W3C ACT | 80f0bf (composite), 4c31df (control), aaa1bf (≤ 3 s): all proposed; 8, 11 and 7 cases | **efbfc7** (text that changes automatically): 11 cases | none |
| DHS ACT data (act-tt, checked 2026-11-03) | none scored | **efbfc7: all 11 cases scored under 2.C, all agree with ACT** (5 pass, 1 fail, 5 inapplicable) | none |
| ICT Testing Baseline 3.1 | [21.D-AudioControl](https://ictbaseline.access-board.gov/web-baselines/21TimedEvents/): the mechanism is "at the beginning of the page content or in platform accessibility features" | 21.B-MovingInfo, 21.C-AutoUpdate (essential excluded; no "three elements" rule) | No changing-content baseline (Baseline 5 is User Controls) |
| Baseline Alignment cases | none | none | none (no TC05 or TC21 cases) |

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
  the opposite on purpose** (change log). TT is the authority, so we allow
  autoplay.

## Verified in this container (Linux, headless, Playwright 1.63 Chromium)

Checked with scratch scripts, not tests yet. Each becomes a V-check in the
build tasks.

1. **Autoplay audio does not start on HAR replay with default settings.**
   Three `<audio autoplay>` elements (WebM/Opus, MP3, WAV) played live, and
   were at `currentTime` 3.0 after 3 s. On replay from the HAR they stayed
   `paused` at 0, with `readyState` 4. With
   `--autoplay-policy=no-user-gesture-required` they play on replay too,
   and an `AudioContext` goes from `suspended` to `running`. Without the
   flag, 2.A would report DOES NOT APPLY on every page: a silent false
   result. TT's setup step ("make sure the browser is not set to block
   auto-playing content") is exactly this flag. Why the live load and the
   replay differ is unknown.
2. **Headless Playwright adds `--mute-audio`.** Playback still advances.
   `webkitAudioDecodedByteCount` and the CDP `Media` domain (`kAudioTracks`,
   `kAudioDecoderName`) show decoded audio. So audio can be detected without
   hearing it.
3. **DOM APIs do not see `<marquee>` or animated GIFs.**
   `document.getAnimations()` listed the CSS animation only. Pixels changed
   between two screenshots taken 1 s apart, on a page that had both a
   marquee and a GIF.
4. **`ImageDecoder` (WebCodecs) reads animated images.** For a looping GIF
   it gave frame count 10, `repetitionCount` ∞ and a total of 2.0 s. That is
   G152's computation, done mechanically.
5. **`<blink>` is `HTMLUnknownElement` in Chrome,** and
   `text-decoration: blink` is not rendered. In Chrome these do not blink,
   so they are not 2.B content. Results are per browser
   ([browser-specific-results.md](../solutions/browser-specific-results.md)).

## What the tool would do (one shared collector, four checks)

### Pass T: watch the page over time (new, `motion.py`)

One fresh load of the recorded page, with no input, watched for about
6.5 s. TT's threshold is "more than 5 seconds" for 2.B. For 2.A it is
"more than 3 seconds". Pass T records facts only:

- **Frames.** A screenshot about every 0.5 s through `traverse.screenshot()`,
  never `page.screenshot()` (the time-budget trap). Pass T diffs the frames
  tile by tile, then maps the changed regions to elements with
  `elementsFromPoint`. This is the only thing that sees marquees, GIFs,
  canvas, video and scroll-position tickers.
- **DOM.** A mutation log with targets: text before and after (capped),
  attribute names, added and removed nodes. Today `INIT_JS` only counts
  mutations, and `traverse.py` is frozen, so pass T adds its own observer at
  load. That needs a small init-script hook in `capture.replay_context`, or
  `ctx.new_page` gaining an `init_scripts` argument (decision Q7).
- **Animations.** `document.getAnimations()` sampled at intervals: target,
  iterations, duration, play state.
- **Media.** Every `audio` and `video` element: paused, muted, volume,
  `currentTime` progress, duration, loop, `error`, and decoded audio bytes.
  Also CDP `Media` domain events. `AudioContext` state is caught by an init
  hook that counts nodes connected to `destination`.
- **Animated images** (`img`, CSS backgrounds): G152 duration from
  `ImageDecoder`, using the bytes already in the HAR.
- **Timers and polling, as hints only.** `setInterval` and recurring
  `setTimeout` calls whose period is longer than the window, and network
  requests repeated after load. These are what a 6.5 s watch can miss (see
  the risks).
- **Live regions, dialogs and focus.** For 2.D: regions that existed before
  each change, using ANDI's own set (`aria-live` polite or assertive, and
  roles `alert`, `status`, `log`, `marquee`, `timer`; see `sandi.js`).
  Dialogs use `t4e._DIALOGS_JS`. Focus moves come from the existing focus
  log.

**Classification (rows, in the spec).** A change region is *moving* (2.B)
when its pixels or geometry change but its text and image sources do not.
It is *auto-updating* (2.C and 2.D) when text, an image source or child
nodes change. It can be both. It is excluded for being the only content
when nothing outside the regions has visible text. What a region is
remains evidence, not an outcome, until the rows read it.

### Mechanism probe (2.A–2.C; reuses `ctx.replay`, `observe.py`)

TT's How to Test is "determine if there is a mechanism… within three
elements, activate it, and test it". Mechanically:

1. **Candidates.** The first three stops of the walk (P1 1–3), plus the
   three stops before and after each content region in tab order. Plus,
   for 2.A, any non-focusable text at the top of the page before the first
   repeated block (TT's note: "text instructions at the top of the page").
   Candidates are chosen by position, not by name, because icon-only pause
   buttons have empty names.
2. **Activation.** Use only operable controls (buttons, `role=button`,
   switches, checkboxes, sliders, and `href="#"` links), with Enter or
   Space, through `observe.py`. A slider gets arrow and Home/End presses
   (volume to zero).
3. **Confirmation**, from a fresh load each time
   ([fresh-load-per-probe.md](../solutions/fresh-load-per-probe.md)). After
   activating, focus moves off the control (Tab, or focus to `body`), and
   the region is watched again for 5.5 s. It counts as stopped only if it
   stays still (G4: it does not restart), is hidden, or its audio is paused,
   muted or at volume 0.
4. **The focus-only control probe.** The same replay, landing on the control
   without activating it. If the region also stops then, the stop came from
   focus or hover, not from the mechanism, and the probe is NEEDS REVIEW,
   never PASS. Common carousel libraries pause on focus, so without this
   probe a carousel's own Next button would read as a working pause: a
   false PASS.

PASS needs a key press that confirms it (principle 8). Each test's ER 3
("the mechanism passes all applicable Test Conditions") is read from this
run's other findings at that stop (4.A, 4.C, 4.D, 4.E, 5.x). There is no new
testing for it (principle 7). Decision Q4.

### Per test

| Test | Applies when (DNA otherwise) | PASS | FAIL | Open questions (by rubric) |
| --- | --- | --- | --- | --- |
| **2.A** Audio control | A media element or `AudioContext` makes audio for more than 3 s on load (decoded audio advancing; not muted; volume above 0; not an ACT "silent" track) | A candidate in the first three elements pauses, stops or mutes the audio (confirmed) | Audio more than 3 s, no candidate stops it, and the first three elements are all operable stops that were probed | J1: text instructions at the top describe a mechanism (by looking) |
| **2.B** Moving, blinking, scrolling | A region moves for more than 5 s continuously from load: an animation with more than 5 s of iterations, a GIF over 5 s (G152), a marquee, playing video, or a pixel region still changing at 5 s. Excluded: the only content; essential (J) | A candidate in either window stops, pauses or hides it (confirmed), and J2 says it is evident | No candidate has any effect on the region and none is untested | J1: essential? (spinner during load, a game). J2: is the mechanism evident (by looking)? |
| **2.C** Auto-updating | Text, image source or children change without input. Excluded only when it is the only content. Never excluded as essential (TT) | As 2.B, or a frequency control changes the period | As 2.B | J1: evident (shared with 2.B when it is the same control) |
| **2.D** Change notification | The changes 2.C found | Every change is in a live region that existed before it (mechanical; ANDI's definition) | A change with no live region, no focus move to it and no dialog | J1: after focus moved to the changed content, does that content describe the change? J2: does the dialog give enough notice? |

**Not performed (NEEDS REVIEW, "This test could not be performed").**
Media that failed to play (`error` set: codec, stream, HAR), third-party
players (YouTube or Vimeo iframes, MSE streams), and hints of updates
slower than the window. The test is never DNA on these. They say what a
person should check.

## Reuse versus new code

| Reused as is | Where |
| --- | --- |
| Recording and HAR replay, the fresh context per load, the egress and navigation guards | `capture.py`, `browser.py` |
| `ctx.replay`, `ctx.out_of_time()`, the replay plan from the walk; P1's first stops and tab order for both windows | `checks/base.py`, `walk.py` |
| Key activation with before and after effects | `observe.py` |
| Screenshots that pause the mutation log; the focus log; `PATH_JS` | `traverse.py` (read only) |
| Dialog detection | `t4e._DIALOGS_JS` (move it to a shared module) |
| Live-region idea and "region present before the change" | `t5f` (`_LIVE`, `live`); widened to ANDI's set |
| Rows, findings, questions, `shared_inputs`, `run://` links, resume and answers | `engine.py`, `models.py`, `judgment.py`, `pipeline.py` |
| The harness, the judge eval, `sync_act.py` (it already fetches `test-assets/`), the time budget | `tests/`, `evals/` |

| New | Estimate |
| --- | --- |
| `motion.py`: pass T (frames, tile diff, region-to-element mapping, mutation targets, animations, media, `ImageDecoder`, timer and polling hints) | ~450 lines; the biggest risk |
| Mechanism probe (candidates by position, slider handling, the focus-only control, the confirm watch), shared by 2.A–2.C | ~250 lines in `motion.py` or `mechanism.py` |
| `t2a.py`, `t2b.py`, `t2c.py`, `t2d.py` (rows, plain text, questions) | ~250–400 lines each; 2.C is the smallest |
| Browser setup: an autoplay-allowed browser for pass T (Q1), recorded in the report's versions | small |
| Specs ×4, build tasks, ~20 custom fixtures, one budget page with a carousel and a ticker | — |

Roughly a third of the work is reuse. There is less reuse than 5.x or 9.x
had, because nothing yet watches a page **over time without input**. Pass T
is the new foundation. Later it can also serve 3.A (DOES NOT APPLY when
nothing changes; its frames are too slow to count flashes), 2.2.1 timeouts
(8.A) and the ROADMAP's 4.E dialog work.

## Where agent-driven testing could fail

Ordered by harm. A false PASS or a false DNA is worse than NEEDS REVIEW.

| # | Failure | Result if unhandled | Mitigation | Left over |
| --- | --- | --- | --- | --- |
| 1 | Replay blocks autoplay (verified above) | 2.A DNA on every page | Pass T's browser allows autoplay (Q1) | Headed Chrome on Windows to check |
| 2 | **A carousel pauses on focus**, so its Next or Previous button "stops" it | **False PASS** (2.B, 2.C) | Move focus away, rewatch, and run the focus-only control probe | Pages that pause on any keydown |
| 3 | Updates slower than the window (a clock every minute, a carousel every 8–10 s), or slides that start only when scrolled into view | False DNA | Timer and polling hints, carousel markup hints (`aria-roledescription=carousel`, common library classes) → NEEDS REVIEW; watch the top viewport, then one scrolled watch if hints are below the fold (Q3) | Long timers with no hint |
| 4 | **HAR replay returns the same data to polling requests** (tickers, scores) | 2.C and 2.D false DNA (content never changes on replay) | Requests repeated after load → NEEDS REVIEW, "updates from the server cannot be replayed" (as 5.F does for server errors) | — |
| 5 | Media that cannot play in the bundled Chromium (H.264/AAC MP4 not verified; MSE/HLS streams; Range requests in the HAR; very large bodies) | False DNA for 2.A and 2.B | A media `error`, or a source with no progress → not performed; the installed-Chrome channel; a size cap on recorded media | Needs V-checks |
| 6 | Cross-origin player iframes (YouTube, Vimeo) | Missed or unprobeable | Detect the embed and its `autoplay=1`; probe controls inside frames only if focus reaches them; otherwise NEEDS REVIEW | Common on .gov pages |
| 7 | Silent audio tracks, or Web Audio nodes that make no sound | 2.A false FAIL | Decoded bytes are not loudness; analyse level with an analyser on `captureStream()` (tainted for cross-origin media) → NEEDS REVIEW when unknown | — |
| 8 | Pixel noise: text cursors, hover styles, font loading, late images | False 2.B applicability | Ignore changes that end before 5 s; need a region still changing at 5 s; a cursor blink is the field's own | Video ads |
| 9 | Moving or updating misclassified (fades, opacity pulsing, a carousel that slides) | Wrong test applied | Both apply when both signals are present (TT's own note); fades go to J1 | — |
| 10 | Judge errors on "evident", "essential", "only content", and 2.D "sufficient description" | Wrong PASS from a judgment | Only by-looking questions can lead to PASS, with "unsure" required; frame strips and before and after crops (one frame cannot show motion); slide text is untrusted (principle 5) | Judge eval needed |
| 11 | 2.D: the APG carousel turns `aria-live` off while rotating, by design | TT reads it as FAIL; users and developers may disagree | Follow TT (principle 7); the plain explanation says why | Q6 |
| 12 | ANDI counts `role=marquee` and `role=timer` as live regions (their implicit `aria-live` is off) | 2.D differs from ARIA | Match ANDI, as TT prescribes, and note it | — |
| 13 | **Autoplay allowed for the whole run** changes other tests' evidence (playing video is neither a mutation nor a Web Animation, so 4.D's noise read would miss it) | 4.D false focus indicator | Allow autoplay only in pass T's browser, or add "media playing" to 4.D's noise signal (Q1) | — |
| 14 | Random and clock-driven pages (`Math.random`, `Date`) | Flaky fixtures | Rows no page triggers reliably get hand-built evidence ([testing-what-no-page-can-trigger.md](../solutions/testing-what-no-page-can-trigger.md)); Playwright's clock in tests only | — |

## Time budget

The agency page uses 108 s of 110, and the budget pages have no moving
content at all, so they would not show this cost.

- **Pass T alone: ~7 s.** It needs no focus, so it can run **in parallel
  with the walk's P1**: a separate context, no keys pressed, and Playwright
  already disables background timer throttling. The pipeline runs collectors
  in sequence, and `pipeline.py` is frozen, so this needs approval (Q2).
- **Mechanism probes: ~1–2 s replay + 5.5 s confirm + 5.5 s control, per
  candidate.** That is up to about 60 s on a carousel page with 6
  candidates. Cap the candidates (activated controls first; stop at the
  first confirmed one), and give pages with moving content their own
  allowance, as `OTHER_PAGE_S` does (Q2).
- Add a budget page with a carousel, a ticker and an autoplay video, and
  measure with `time_budget.py --drafts`.

## Open questions for Abby (multiple choice; recommendation first)

- **Q1. Autoplay.** (a) A separate autoplay-allowed browser for pass T
  only, recorded in the report (recommended: other tests' evidence is
  unchanged). (b) The flag for the whole run, and 4.D's noise signal learns
  about playing media; every fixture is rerun. (c) Leave 2.A not performed.
- **Q2. Time.** (a) Pass T in parallel with P1, plus a fixed allowance
  (e.g. +20 s) when moving content is found (recommended). (b) Sequential,
  inside the 120 s, cutting probes to fit. (c) 2.x runs only when the
  caller selects it.
- **Q3. Watch length and scrolling.** (a) 6.5 s at the top, plus one
  scrolled watch only when hints are below the fold (recommended). (b) The
  top only. (c) A full scroll in steps (slow).
- **Q4. ER 3, "the mechanism passes all applicable Test Conditions".**
  (a) Read this run's other findings at the mechanism's stop; a test not
  run gives a note (recommended). (b) Ignore it, with a note for a person.
  (c) NEEDS REVIEW until a person confirms.
- **Q5. 2.A and browser tab mute** (TT note: it is "acceptable"; ICT
  Baseline: "platform accessibility features"). Chrome can mute a site, so
  counting it would make 2.A never fail in Chrome. (a) It does not satisfy
  ER 2 (the first three elements); it is mentioned in the plain text
  (recommended). (b) It counts: 2.A passes in Chrome whenever ER 3 holds.
  (c) Ask DHS. This needs an answer before 2.A's rows.
- **Q6. "Within three elements before/after the content".** (a) Tab order,
  counting controls inside the region (recommended: that is how keyboard
  users meet it, and carousels put their controls inside). (b) Reading
  order, including text.
- **Q7. Hook for pass T's init script.** (a) `replay_context` takes extra
  init scripts; `traverse.py` is untouched (recommended). (b) Pass T injects
  after load and misses the first changes.
- **Q8. Order.** (a) 2.C and 2.D first (DHS-scored ACT cases, shared
  detection), then 2.B, then 2.A (recommended: media capture has the most
  unknowns). (b) All four at once, as the ROADMAP batch says.

## Order of work (after the answers)

1. V-checks first, in tests, not scratch: autoplay on replay (both
   settings); H.264 MP4 and Range requests replayed in bundled Chromium;
   the CDP `Media` domain in out-of-process iframes; `ImageDecoder` on
   APNG and WebP; pass T alongside P1 with no slowdown of the walk; the
   same on headed Chrome on Windows (listed as not checkable here).
2. Specs 2c, 2d at 0.1.0 (rows above), then 2b, then 2a; build tasks.
3. `motion.py` pass T and the mechanism probe; rows on hand-built
   evidence.
4. Fixtures: ACT efbfc7 (11, with DHS verdicts), 4c31df, 80f0bf and
   aaa1bf (media assets via `sync_act.py`). Custom pages in
   `tests/fixtures/2x/`: a carousel with a working pause; a carousel that
   only pauses on focus (the false-PASS trap); a ticker polling the server;
   a 10 s-interval carousel; an infinite CSS animation and a 3 s one; long
   and short GIFs; a marquee; a muted looping video (2.B, not 2.A); a canvas
   with `requestAnimationFrame`; a live-region ticker; the APG carousel; an
   update that moves focus; an update announced by a dialog; a loading
   spinner; changing content as the only content.
5. Checks registered in `tests/drafts.py`; the judge eval on every
   question; time with the new budget page.
6. 1.0.0 with Abby; ROADMAP, solutions (pass T, the autoplay finding),
   CLAUDE.md layout, and the hackathon evaluation and deck in the same
   commit.
