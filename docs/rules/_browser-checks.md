# Browser checks (V-checks) for the built tests

A spec's "Verify" column and its V-numbers point here: browser behavior a
rule depends on, which must be shown by a test, never assumed (principle 6).
Each test's table was copied word for word from its build-tasks file when
that file was removed (2026-11-05; the files are in git history). IDs stay
per test: "4.C V5" is V5 in the 4.C section.

While a test is being built, its V-checks live in its
`<id>-build-tasks.md`; at 1.0.0 they move here and that file is deleted
(`_template.md`). Open checks are mostly Windows headed Chrome, which a
Linux container cannot run (`docs/solutions/windows-chrome-results.md`).
Mark a row checked only when a test in a run covers it, and name the test.

<a id="4a"></a>

## 4.A

Spec: [4a-keyboard-access.md](4a-keyboard-access.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | Hit-testing through frames: inert, hidden and 1 × 1 px frames are not pointer targets (covered by ACT 17a371c4, 033e04cc, 63cd20ec); cross-origin frames are counted as unreadable (no fixture) | Pointer scan, M16 |
| V2 | Chrome shows no title tooltip on keyboard focus (assumed from the PDF's note and Baseline's advisory; headless screenshots cannot show native tooltips) | Title check |
| V3 | Delegated click handlers (`document` listeners, React roots) are found by the cursor rule; one without a pointer cursor is missed (no fixture) | Pointer scan |
| V4 | Checked (Windows, installed Chrome 156 headed): every fixture gives the same outcome; ACT 8f9b5bf5 differs because Windows scrollbars make its box scroll (solutions/windows-chrome-results.md) | All rows |

<a id="4b"></a>

## 4.B

Spec: [4b-no-keystroke-timing.md](4b-no-keystroke-timing.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | A held key in headed Chrome sends repeated keydown events (Playwright's `keyboard.down` sends one); pages that count repeats may behave differently | Timing proof |
| V2 | Headed Chrome on Windows: every fixture gives the same outcome | All rows |

<a id="4c"></a>

## 4.C

Spec: [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md).

Each needs a small test in headed Chrome on Windows through Playwright before the rule that depends on it ships. V1–V13 pass on Linux (headless and headed under Xvfb) in `tests/browser/test_v_checks.py`; Windows is still to run.

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | Where the first Tab lands after load, and whether the window must be focused first | P1, P2 start |
| V2 | Tab past the last element: where focus goes (browser toolbar, body), what activeElement and document.hasFocus() report, and whether the next Tab returns to the first element | OUT detection, wrap, G4 |
| V3 | Shift+Tab before the first element: same questions as V2 | P2, G4 |
| V4 | Ctrl+Tab sent by Playwright: does it switch browser tabs or reach the page? | Run limits (Ctrl+Tab) |
| V5 | Tab into cross-origin (out-of-process) iframes; reading the focused element and node IDs inside them | Iframe rule, F19–F21 |
| V6 | Resolving the focused node inside closed shadow roots through CDP | Stop identity, M1, F25 |
| V7 | Where the next Tab goes after the focused element is removed and focus falls to the body | BODY rule, F26–F27 |
| V8 | Whether a click on non-interactive text sets the starting point for the next Tab | P6, mouse bypass |
| V9 | Whether elements inside a tabindex=-1 iframe are in the Tab sequence | Inventory, F33 |
| V10 | What the frozen-page replay does with scroll-triggered requests it never recorded | Recording, infinite scroll rule, F29 |
| V11 | Whether Chrome consumes Escape (stop loading, exit fullscreen) before the page sees it | M3 |
| V12 | Tab sent by Playwright moves focus the same way in headed Chrome as the plan's headless sandbox showed | All passes |
| V13 | Arrow keys on a native select on Windows: change value without opening, and fire change events | P4 |
| V14 | Recording focus and blur events with targets and times across frames and shadow roots, injected before page scripts run. Top-frame log tested (`tests/test_traverse.py`); frames and shadow roots still to test | Settle rule, F35 |
| V15 | Whether script focus() pulls keyboard focus back from the browser UI (toolbar) in headed Chrome. Linux test passes: it does, so d2f5325f cycles both ways | OUT detection, d2f5325f, 0ec0e93e |

<a id="4d"></a>

## 4.D

Spec: [4d-focus-visible.md](4d-focus-visible.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V4 | Whether Chrome makes a frame or iframe element itself a Tab stop (F08 passes, but through which row is not asserted) | M2 |
| V5 | A top-level clip over a cross-origin iframe shows the frame's content, and the walk's box matches it | Frame edge case |
| V6 | Off images by page coordinates when Chrome scrolled between steps; regions larger than the viewport | Section 2, M4 |
| V8 | Cost per stop on Windows headed Chrome; a 100-stop page within the budget together with 4.C | Time budget |
| V11 | Headed Chrome on Windows: ACT cases and F01–F14 give the same outcomes | All rows |

<a id="4e"></a>

## 4.E

Spec: [4e-on-focus.md](4e-on-focus.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V2 | `relatedTarget` and `isTrusted` on focus events across shadow roots and frames (the top frame is covered by F03 and F04) | Section 3, M1, M6, M7 |
| V4 | Headed Chrome on Windows: F01–F08 give the same outcomes | All rows |

<a id="4f"></a>

## 4.F

Spec: [4f-focus-order-meaning.md](4f-focus-order-meaning.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | Right-to-left pages: S3 mirrored (no rtl fixture yet) | S3 |
| V3 | Document order across frames and shadow roots (S2 compares only stops in the same frame; positions use the walk's top-level box, checked on no_trap.html's same-origin frame) | S2, S3 |
| V4 | The order image's badges line up with the stops on long, scrolled pages | Order image |
| V5 | Headed Chrome on Windows: F01–F15 give the same outcomes | All rows |

<a id="5a"></a>

## 5.A and 5.C (also 5.B)

Spec: [5a-label-provided.md](5a-label-provided.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | ANDI's `accName` for placeholder (checked in the spike), `title`, `aria-label`, `aria-labelledby` and label/for (TC10.A) | M3, M5 |
| V2 | Checked (Linux headless Chromium, 2026-11-01): ANDI reports a fieldset legend as `accGroup` (f06) | Programmatic text, M5 |
| V3 | Checked: ANDI does not report table headers for a field in a cell; the tool computes them from the table (f08) | M5, J1 |
| V4 | A page CSP that blocks inline scripts stops ANDI; how it shows | A2 |
| V6 | Checked for 4.F's pass R (f12): ANDI injected at the end of the replay analyses the revealed field. 5.D's fill pass: not covered by a fixture yet | Section 2 (revealed fields) |
| V5 | Checked (Windows, installed Chrome 156 headed, 2026-11-02): every 5.A, 5.B and 5.C fixture gives the same outcome | All rows |

<a id="5d"></a>

## 5.D

Spec: [5d-on-input.md](5d-on-input.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V2 | Windows headed Chrome: ArrowDown on a closed select changes its value and fires `change` (yes in Linux headless Chromium; Mac opens the list) | Completing selects, M2 |
| V3 | `time` and `datetime-local` inputs: typing digits sets the value (checked for `date` in Linux headless Chromium, F14) | Completing dates, J3 |
| V4 | Fields in cross-origin iframes and shadow roots are completed and read back (a same-origin iframe is covered by F09) | Section 2 |
| V5 | Headed Chrome on Windows: every fixture gives the same outcome | All rows |

<a id="5f"></a>

## 5.F, 5.G and 5.H

Spec: [5f-error-identification.md](5f-error-identification.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | A text change outside any live region, with focus left where it was, is told apart from one inside a live region (read at the time of the change) | Notice, M7 |
| V2 | Checked (Linux headless Chromium, 2026-11-01): Playwright records a JS `alert` message; after dismissing it focus is where the page sent it (TC10.D-all-pass-1: the field) | Notice, M6 |
| V3 | Checked (Linux headless Chromium, 2026-11-01): Enter on a submit button fires `invalid` on every invalid field, blocks the submission and focuses the first; `validationMessage` reads "Please fill out this field." and "Please include an '@' in the email address. 'abc' is missing an '@'." (f01). Left: Enter in a text field, headed Chrome's bubble | M2 |
| V4 | Checked (Windows, installed Chrome 156 headed, 2026-11-02): every 5.F, 5.G and 5.H fixture gives the same outcome | All rows |

<a id="9a"></a>

## 9.A, 9.B and 9.C

Spec: [9a-bypass.md](9a-bypass.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | Checked (Linux headless Chromium, 2026-11-02, ACT ye5d6e passed 7 and 8): after Enter on a link to a non-focusable target, `:target` is the target and the next Tab goes to the first stop after it | 9.A landing, M6 |
| V2 | Windows headed Chrome: V1 again, and a hotkey with Alt (Alt+letter can open browser menus there) | 9.A, J1 |
| V3 | ANDI on a page whose Content-Security-Policy blocks inline scripts: 9.C A2 (not performed) | 9.C A2 |

<a id="19a"></a>

## 19.A

Spec: [19a-multiple-ways.md](19a-multiple-ways.md).

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | A real .gov site search: GET forms, result pages that link to the page, and searches that run only in script (W4) | W2–W4 |

<a id="2c"></a>

## 2.A, 2.B, 2.C and 2.D

Spec: [2c-auto-updating.md](2c-auto-updating.md).

The scratch scripts in `docs/research/2026-11-03-2x-experiments/` (removed at 1.0.0; in git history at 9efe907) checked
most of these on Linux. Each becomes a test with local fixtures and no
network.

| ID | Verify | Rules that depend on it | Status |
| --- | --- | --- | --- |
| V1 | Tab reaches a `<video controls>` element's own buttons in Chrome, and Enter or Space on its play button pauses it | 2.A native controls | Test (`t-audio-native`, ACT 0d2dcde8 and 3e932531): Enter on the play button pauses it |
| V2 | Autoplay plays on replay only with the flag (item 1); loudness from bytes separates silent from audible (item 4); muted and short audio are not instances | 2.A Terms, A3 | Flag: test (`test_autoplay_plays_only_in_the_motion_browser`; a page's own `play()` on a script-made blob plays even without it, so the test uses `<audio autoplay src>`); loudness and instances not built |
| V3 | `ImageDecoder` gives frames, loops and duration for GIF, APNG and WebP (item 8); pixel diffs separate still-moving from stopped-before-5 s (item 6) | 2.B Terms | Checked (scratch) |
| V4 | Timer hooks catch a period longer than the watch (item 7); the scrolled watch sees a below-the-fold animation | 2.C A2, 2.B | Hook: test (`test_kinds`, a 10 s interval); scrolled watch: `test_scrolled_watch_finds_content_that_starts_when_seen`, `t-scroll-start` |
| V5 | Polling repeats the first response on replay, and the HAR lists every poll (item 10) | 2.C A2 | Test (`test_polling_is_in_the_har`): the replay repeats the first response; the HAR held only one or two polls (recording stops at network idle), so pass T also counts requests during the watch |
| V6 | Slick and Splide pause on focus and resume when it leaves; four of six libraries pause on hover (item 12). Vendor the libraries for the fixtures | 2.C K2 | Checked (scratch, libraries from the network) |
| V7 | Full Chromium puts cross-site iframes out-of-process; media state, pixels and Tab work through them (items 15–16); a shell recording replays in full Chromium (Q11) | Q11; 2.A–2.D in frames | Out-of-process and replay: `tests/test_full_chromium.py` (main); pass T's regions, live regions and elements in such a frame: `test_cross_site_frame_in_full_chromium`; media and Tab in it not yet |
| V8 | A live region added in the same task as its text is told apart from one present at 0 s | 2.D Terms | Test (`test_live_regions`, `#late`: never `live_at_start`) |
| V9 | Home, End and arrows on a volume slider set the media's volume to 0 | 2.A | Test (`t-audio-volume`): Home on a range input that sets the volume gives 0, stopped (K3) |
| V10 | Media fetched in several ranges fails on replay, and the media store fixes it (items 13–14) | 2.A, 2.B A1 | Store and ranges: `tests/test_media_store.py`; seeking on replay: ACT 80f0bf passed 2 (`#t=8,10`); a large file fetched in several ranges not reproduced in a test |
| V11 | Pass T beside P1 does not slow the walk (item 18), and a second headless browser beside a headed walk takes no focus | Q2 | Linux checked; Windows headed not |
| V12 | Windows headed Chrome: autoplay with the flag; the walk unaffected by the second browser | Q1, Q2 | Not checkable from Linux |
| V13 | The element rules: labels on one line merge, stacked labels do not; `aria-hidden` content and alt-less images are skipped; iframe content counts inline | Q6 | Test (`test_elements`) |
