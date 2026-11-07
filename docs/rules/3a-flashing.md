---
tt_test: 3.A
tt_name: 2.3.1-flashing
spec_version: 0.2.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 3.A (2.3.1-flashing)

The tool gives each page one 3.A outcome: DOES NOT APPLY, NOT TESTED or NEEDS REVIEW. It never gives PASS or FAIL, because the TT does not (p. 18). This is the one test whose TT text names NOT TESTED (p. 6; `tt.json` `not_tested_named`).

When flashing is found, the finding also carries the tool's own *assessment* against WCAG 2.0 SC 2.3.1: fails, does not fail, or could not assess, with the evidence. It is kept in the report and in the SCRT export's comment, so the results stay on record (Abby, 2026-11-03, research O1). The assessment is never an outcome.

Draft (0.2.0): no outcome from the server until 1.0.0; the check is built (`checks/t3a.py`, registered in `tests/drafts.py`) and its fixtures pass. 0.2.0 makes the spec match the code; the questions under "Open for Abby" are what is left before 1.0.0. Research: [research/2026-11-03-3a-flashing.md](../research/2026-11-03-3a-flashing.md) ("research" below).

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/3.A`). Identify Content, p. 18: "Visually identify any content that flashes. Flashing is content that rapidly alternates between two or more states that vary significantly in contrast. When flashing content IS found, the result for Test ID 3.A ... is NOT TESTED." Test condition, p. 18: "If NO flashing content is found, then this Test Condition DOES NOT APPLY (DNA). If flashing content IS found, then this test should be recorded as NOT TESTED." Note, p. 18: "a testing tool would be very helpful but is not available at this time. The test process will be updated when a testing tool is identified." Applicable Standards, p. 19 (Conformance Requirement 5: "no definitive statement can be made ... if any flashing content is present"). Test 1.D, p. 11: 3.A must be DOES NOT APPLY for 1.D; NOT TESTED does not meet it.

**Other sources** (details and quotes in the research note, sections 2 and 3):

- **WCAG 2.0 SC 2.3.1** decides the assessment, since Section 508 incorporates WCAG 2.0 (research O3): [Understanding 2.3.1, WCAG 2.0](https://www.w3.org/TR/UNDERSTANDING-WCAG20/seizure-does-not-violate.html) (thresholds, Notes 1-3, the fine-pattern exception).
- **WCAG 2.2** ([Understanding](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html)): its red-flash definition, reported where it differs; analysis at the largest scale a user may view (video at full screen); looping GIFs analyzed while looping.
- **Techniques** [G19](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G19) (seven transitions are 3.5 flashes), [G176](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G176) (21,824 px) and [G15](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G15).
- **No answer key:** no ACT rule, no DHS ACT data, no Baseline Alignment cases. Fixtures are custom pages (`tests/fixtures/3a/`).
- **ICT Testing Baseline 3.1** [9.A-Flashes](https://ictbaseline.access-board.gov/web-baselines/09Flashing/): standard zoom, the larger and looping versions, the same thresholds.

**Terms.**

- *Pass T*, *region*, pass T's browser and the HAR media store: [2c-auto-updating.md](2c-auto-updating.md) Terms and section 2.
- *Measurement window*: 1024 × 768 CSS px at device pixel ratio 1, standard zoom (WCAG 2.0 Note 1's screen). The stepped capture loads the page at this size (its own load; the rest of the run keeps the configured window, recorded in `Versions.display`); images are measured at the size this layout shows them; video is scaled to fill it (contain, black bars). The finding records the window measured (`State3A.window`).
- *Cell*: a 4 × 4 CSS px square. Its colour is the mean of its pixels' linear RGB.
- *Relative luminance* L: WCAG 2.0's sRGB formula (linear threshold 0.03928).
- *Transition*: the change between adjacent peaks and valleys of a cell's L over time (Note 2). A peak is confirmed when L falls back from it by 0.1 (a valley, when it rises by 0.1), so a fade over several frames is one transition and noise under 0.1 is none. It happens at the frame after the last one within 0.05 of the old state (not at the new state's highest frame, which noise moves). It is a *general transition* when the change is at least 0.1 and the darker state is below 0.80.
- *Red transition* (WCAG 2.0 Note 3): the same, on (R−G−B) × 320 with negatives set to 0, changing by more than 20, with R/(R+G+B) ≥ 0.8 in either state. R, G and B are linear values (WCAG 2.0 does not say which; see Open for Abby). WCAG 2.2's rule (to or from R/(R+G+B) ≥ 0.8, a CIE 1976 u′v′ difference over 0.2, black given D65's chromaticity) is counted too and reported where it changes the result.
- *Flashes in a window*: the transitions of a cell in a one-second window [t, t + 1 s), divided by 2; windows start at every frame. Seven transitions are 3.5 flashes (G19); six (three flashes) always end on the starting state, so they are not flashing.
- *Flashing cell*: more than 6 general or more than 6 red transitions in some window.
- *Fine pattern*: a sample of single pixels (every other one across and down) is counted the same way (general only). A flashing pixel with no flashing cell within one cell of it is a fine, balanced pattern that the cells average out (a 2 px checkerboard inverting).
- *Flashing found* (research O2): any flashing cell or fine pattern, whatever its size. Content flashing 3 times a second or less is blinking (2.B).
- *Concurrent flashing area*: in one frame, the flashing cells of a window that are changing in that frame (between the old state's last frame and the new one's first), inside the best 341 × 256 rectangle, rounded up to whole cells (344 × 256). Counted per frame; the largest in the window is used.
- *Over the threshold*: that area exceeds 21,824 px (25% of 341 × 256; G176).

## 1. Applicability and outcome

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | Pass T could not run | NEEDS REVIEW, not performed, with the reason | p. 5 |
| A2 | Flashing found in any source | NOT TESTED, with the assessment (section 3) | p. 18 test condition; research O1, O2 |
| A3 | No flashing found, but something was not measured: a streaming player, media over the recording cap or not recorded, a video that cannot be decoded, a video beyond the first 10 s (O4), a `<marquee>`, a capture that failed or that time cut short, or the screencast saw more flashing than every measurement explains (by more than one transition) | NEEDS REVIEW, not performed, naming what was not measured | p. 5; research section 4 |
| A4 | No flashing found, and every trigger was measured (or there were none) | DOES NOT APPLY | p. 18 test condition |

**O4 (decided).** A video counts in full, but the tool analyzes at most the first 10 s of each one. Beyond that, A3 applies unless flashing was found elsewhere (A2). Every "does not fail" for such a video says how much was analyzed ("the first 10 s of 150 s").

## 2. Evidence to collect

**Triggers** (pass T's own load, `motion.MOTION_INIT_JS`; one screencast):

- a running animation or transition whose keyframes change colour, background (colour, image, position or size), opacity, visibility, filter, fill, stroke, border or outline colour, or shadows more than 3 times a second (each keyframe change, a `steps(n)` easing counting n, per iteration; read at the end of the watch: `MotionPass.fast_animations`);
- more than 6 callbacks in one second of timers under 334 ms (`setTimeout` chains included) or of `requestAnimationFrame` that change the DOM or draw on a canvas (2D or WebGL) (`MotionPass.fast_callbacks`);
- an animated image (`ImageDecoder` on the recorded bytes) with a frame shown for under 334 ms; Chrome shows a frame of 10 ms or less for 100 ms (`animated_images[].min_ms`);
- a video that played during the watch (pass T's media reads);
- a 2 s CDP screencast (frames only when something changed, about 55 a second, 640 px wide) on its own load after pass T, so pass T's timing and 2.A-2.D's outcomes are unchanged (built 2026-11-07; the 0.1.0 draft said beside pass T). More than 6 transitions of a cell in a second is a trigger. Its small frames cannot see fine patterns, and it is never evidence for DOES NOT APPLY on its own (research section 4).

A page with no trigger is A4 with no capture.

**Flash capture** (`flashcap.py`, pass T's browser: full Chromium, autoplay):

- **Stepped** (when an animation, callback or screencast trigger fired): a fresh load at 1024 × 768 with Playwright's clock installed and paused before the page loads; 100 ms of page time first (or up to 200 ms before the first fast callback pass T saw, at most 6 s); then 3 s of page time at 60 steps a second (whole-millisecond steps of 17, 16, 17 ms): run the clock, set every animation's `currentTime` and every SMIL document's time (paused once; what runs at the first step started with the load), take a screenshot. Videos, the animated images being decoded, and marquees are masked out of these frames (they run by the wall clock). Counted inside the box of what changed.
- **Animated images:** every frame decoded with `ImageDecoder`, drawn at the size the page shows it at 1024 × 768 (transparent pixels over white), at 60 frames a second, over two plays and at least 2 s (or as long as it plays, when shorter). An image not shown at this size is not measured (nothing is seen).
- **Video:** decoded from the recorded bytes in a tool page, played at 0.5× with `requestVideoFrameCallback` (every frame), the first 10 s, drawn at full screen on a 256 × 192 canvas (one pixel per 4 × 4 CSS px cell; the canvas averages in sRGB, an approximation). No fine-pattern check. Chromium cannot decode H.264: such a video is A3.
- **Not steppable** (V7): `<marquee>` runs by the wall clock: A3. SMIL steps.

**Time budget.** Only when a trigger fires: the screencast about 3 s (load and 2 s); the stepped capture about 6-7 s of wall time; each video up to 20 s; images under a second. It comes out of the moving-content allowance (`MOVING_ALLOWANCE_S`, 2.x plan Q2) when the run is held to a limit. `ctx.out_of_time()` is checked before the screencast, the capture, every 30 steps, each image and each video; work cut by time is A3.

## 3. The assessment (WCAG 2.0 SC 2.3.1)

Given only with A2. One assessment per flashing source (the stepped capture, an image, a video), then one for the page. The rows are tried in this order: a failing part decides first, and a fine pattern elsewhere in the same source does not undo it.

| # | Evidence | Assessment | Source |
| --- | --- | --- | --- |
| F2 | General flashing over the threshold | Fails (general flash) | WCAG 2.0 SC 2.3.1, definition (1) and (2) |
| F3 | Red flashing over the threshold | Fails (red flash) | WCAG 2.0 Note 3 |
| F1 | A fine pattern (pixels flash where no cell does) | Could not assess: "this may be a fine pattern, which WCAG allows; a person should check" | WCAG 2.0 exception |
| F4 | Two sources on the page (not video, which is analyzed full screen), each under the threshold, whose flashing places fit in one 341 × 256 rectangle and whose areas add up over 21,824 px. Their times cannot be aligned frame by frame (a decoded image beside the stepped capture). Sources in the same stepped capture are aligned and counted together (F2) | Could not assess: "flashing in several places at once may add up; a person should check" | WCAG 2.0 ("combined area of flashes occurring concurrently") |
| F5 | Otherwise | Does not fail | WCAG 2.0 definition (2); G176 |

The page's assessment is fails if any source fails; else could not assess if any could not; else does not fail. Where WCAG 2.2's red rule changes a source's result (F3 or F5), the note says so (research O3).

**Plain-language sentences** (research O1 wording; the note never explains the TT background):

| Case | Sentence |
| --- | --- |
| A2, fails | "The Trusted Tester process records flashing content as Not Tested. According to our experimental flash analysis, this flashing fails WCAG 2.3.1. <Where>: <n> flashes per second, <area> square pixels flashing at once (the limit is 21,824 in any 341 by 256 pixel area), <light and dark, or red> flashing. Flashing like this can cause seizures; fix it so it flashes no more than three times a second, or keep the flashing area small." |
| A2, does not fail | "... this flashing does not fail WCAG 2.3.1. <Where>: <facts>. <We analyzed the first <x> s of <y>.>" |
| A2, could not assess | "... Our experimental flash analysis could not decide whether it fails WCAG 2.3.1. <Where>: <reason>. A person should check it with a flash analysis tool." |
| A2, any | ends "Because flashing was found, the page cannot meet the non-interference test (1.D)." |
| A3 | "We could not check all of this page for flashing (<what>: <why>). A person should watch it." |
| A4 | "Nothing on this page flashes more than three times a second, so this test does not apply." |

*Where* is "an area of <w> by <h> pixels (<its text>) at the <top|middle|bottom> <left|centre|right> of the screen", "an animated image at ...", or "a video (analyzed at full screen)".

**Notes (no outcome).** Flashing slower than 3 per second that lasts more than 5 s is 2.B's concern.

## 4. Judgment questions

None. Every step is a measurement. Where measurement cannot decide (F1, F4), the assessment is "could not assess" and a person checks.

## 5. Edge cases

| Case | Rule | Verify |
| --- | --- | --- |
| Exactly 3 flashes in a second, steadily | Not flashing (G19) | V2; fixture f07 |
| 7 transitions in a second, once | Flashing (G19 Note 2) | V2; fixture f08 (only the screencast triggers it) |
| A small flasher (40 × 40 px) at 5 per second | NOT TESTED; does not fail (area) | V3; fixture f03 |
| Red and a grey of the same luminance | Red transitions only: F3 | V4; fixture f06 |
| A video | Analyzed at 1024 × 768, full screen | V5; fixture f10 |
| A looping GIF | Two plays and at least 2 s | V6; fixture f09 |
| A flash only after 10 s of a video | Not analyzed; A3, or the disclosure when other flashing was found | O4; fixture f11 |
| A strobe in a cross-site iframe | Captured in the viewport (the paused clock reaches it) | V8; fixture f14 |
| A strobe drawn on a canvas every frame | Stepped: about 30 flashes a second, fails | V1; fixture f05 |
| `prefers-reduced-motion` | Not set (pass T's browser uses the default); a page's reduced-motion version is not the content tested | 2.x item 11 |

## 6. What the finding records

`State3A` (the run's evidence file), for each measured source: kind, element, box at 1024 × 768, the analysis (`flash.Analysis`: for general, red and WCAG 2.2 red, the peak transitions in a window, the flashing cells, the largest concurrent area, its rectangle and window; fine pattern; the flashing places; the busiest cell's L over time), the time analyzed and the media's length; for a flashing source, a strip of frames and a plot of L (run-folder pictures in `evidence_refs`). Also the triggers, the screencast's analysis, the stepped capture (frames, page time, wall time, lead, masked boxes, the window measured) and what was not measured. The finding's summary carries the assessment sentence, so the SCRT export keeps it in the tester comment (checked in `tests/test_rows_3a.py`).

## Open for Abby (before 1.0.0)

1. **Fine patterns (F1).** Keep the detection (a pixel sample flashing where no 4 px cell does gives "could not assess"; fixture f12), or send every pattern to a person without detecting it? Detection only changes the note: the outcome is NOT TESTED either way.
2. **Red values.** WCAG 2.0 Note 3 does not say whether R, G and B are linear or gamma-encoded. Built: linear (as luminance, and as 2.2's chromaticity). Encoded values would count more dark reds as changing by more than 20, and fewer as saturated.
3. **The screencast's extra A3.** Built: when the screencast saw more transitions in a second than any measurement (by more than one) and nothing else explains it, the page is A3, not A4. It catches real-time content the capture cannot step (a CSS background GIF) at the cost of a person's look on such pages.
