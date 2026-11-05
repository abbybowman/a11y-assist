---
tt_test: 3.A
tt_name: 2.3.1-flashing
spec_version: 0.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 3.A (2.3.1-flashing)

The tool gives each page one 3.A outcome: DOES NOT APPLY, NOT TESTED or
NEEDS REVIEW. It never gives PASS or FAIL, because the TT does not (p. 18).
This is the one test whose TT text names NOT TESTED (p. 6; `tt.json`
`not_tested_named`).

When flashing is found, the finding also carries the tool's own
*assessment* against WCAG 2.0 SC 2.3.1: fails, does not fail, or could not
assess, with the evidence. It is kept in the report and in the SCRT
export's comment, so the results stay on record (Abby, 2026-11-03,
research O1). The assessment is never an outcome.

Draft (0.1.0): no outcome until 1.0.0. Built after 2.B, on its pass T,
media store and timer hooks (research O5). Research:
[research/2026-11-03-3a-flashing.md](../research/2026-11-03-3a-flashing.md)
("research" below).

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/3.A`). Identify Content, p. 18: "Visually identify any content that flashes. Flashing is content that rapidly alternates between two or more states that vary significantly in contrast. When flashing content IS found, the result for Test ID 3.A ... is NOT TESTED." Test condition, p. 18: "If NO flashing content is found, then this Test Condition DOES NOT APPLY (DNA). If flashing content IS found, then this test should be recorded as NOT TESTED." Note, p. 18: "a testing tool would be very helpful but is not available at this time. The test process will be updated when a testing tool is identified." Applicable Standards, p. 19 (Conformance Requirement 5: "no definitive statement can be made ... if any flashing content is present"). Test 1.D, p. 11: 3.A must be DOES NOT APPLY for 1.D; NOT TESTED does not meet it.

**Other sources** (details and quotes in the research note).

- **WCAG 2.0 SC 2.3.1:** Section 508 incorporates WCAG 2.0, so its
  definitions decide the assessment (research O3). Sources:
  [Understanding 2.3.1, WCAG 2.0](https://www.w3.org/TR/UNDERSTANDING-WCAG20/seizure-does-not-violate.html):
  - the general and red flash thresholds;
  - Note 1 (341 × 256 px at 1024 × 768);
  - Note 2 (transitions);
  - Note 3 (saturated red);
  - the fine-pattern exception.
- **WCAG 2.2** ([Understanding](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html)):
  - its red-flash definition, reported too where it differs;
  - analysis "at the largest scale at which a user may view the content"
    (video at full screen);
  - looping GIFs analyzed while looping.
- **Techniques** [G19](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G19)
  (seven transitions are 3.5 flashes), [G176](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G176)
  (21,824 px) and [G15](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G15).
- **No answer key:** no ACT rule ("No ACT Rules available for this
  criterion yet"), no DHS ACT data, no Baseline Alignment cases.
- **ICT Testing Baseline 3.1**
  [9.A-Flashes](https://ictbaseline.access-board.gov/web-baselines/09Flashing/):
  standard zoom, the larger and looping versions, and the same thresholds.

**Terms.**

- *Pass T*, *region*, the batch browser, the HAR media store and the timer
  hooks: [2c-auto-updating.md](2c-auto-updating.md) Terms and section 2.
- *Flash capture*: section 2's frame-exact capture of the triggered
  regions at a 1024 × 768 viewport (WCAG 2.0's reference resolution).
- *Cell*: a 4 × 4 px square of the capture. A region's cells are
  analyzed one by one.
- *Relative luminance* L of a pixel: WCAG 2.0's sRGB formula (linear
  threshold 0.03928). A cell's L is the average of its pixels.
- *Transition*: the change in L between a peak and the next valley (or a
  valley and the next peak) of a cell's L over time (Note 2). It is a
  *general transition* when the change is at least 0.1 and the darker
  state is below 0.80.
- *Red transition* (WCAG 2.0 Note 3): either state has R/(R+G+B) ≥ 0.8,
  and (R−G−B)×320, with negatives set to 0, changes by more than 20.
  WCAG 2.2's rule (to or from R/(R+G+B) ≥ 0.8, and a CIE 1976 u′v′
  difference over 0.2) is computed too and reported where it differs.
- *Flashes in a window*: the general (or red) transitions of a cell within
  a one-second window, divided by 2; seven transitions are 3.5 flashes
  (G19). Windows slide in steps of one capture frame (the stricter
  reading; research, open points).
- *Flashing cell*: a cell with more than 3 general or more than 3 red
  flashes in some window.
- *Flashing found* (research O2): any flashing cell, whatever its size.
  Content flashing 3 times a second or less is blinking (2.B), not
  flashing ("If blinking occurs faster than 3 per second, it would also be
  considered a flash", Understanding 2.2.2).
- *Flashing area* of a window and a time: the number of pixels in
  flashing cells that change in the same frame, inside any 341 × 256 px
  rectangle.
- *Over the threshold*: in some one-second window, the flashing area of
  general (or red) flashing cells exceeds 21,824 px, 25% of the
  rectangle (WCAG 2.0 definition and Note 1; G176). The concurrently
  flashing area is counted per frame, and the largest in the window is
  used.

## 1. Applicability and outcome

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | The flash capture or pass T could not run | NEEDS REVIEW, not performed, with the reason | p. 5 |
| A2 | Flashing found (any flashing cell, anywhere) | NOT TESTED, with the assessment (section 3) | p. 18 test condition; research O1, O2 |
| A3 | No flashing found, but a trigger could not be measured: a streaming player, media over the recording cap, video beyond the analysis cap (see O4 below), a `<marquee>` or SMIL animation the capture cannot step, or time ran out | NEEDS REVIEW, not performed, naming what was not measured | p. 5; research section 4 |
| A4 | No flashing found, and every trigger was measured (or there were none) | DOES NOT APPLY | p. 18 test condition |

**O4 (decided).** A video counts in full, but the tool analyzes at most
the first 10 s of each one. Beyond that, A3 applies unless flashing was
found elsewhere (A2). Every assessment of "does not fail" for such a page
says how much was analyzed ("the first 10 s of 2 min 30 s").

## 2. Evidence to collect

**Triggers** (cheap, from evidence 2.x already collects):

- an animation or transition (`getAnimations()`) whose keyframes change
  color, background, opacity, visibility, filter or a fill faster than
  every 334 ms (a step or iteration under 334 ms);
- a timer with a period under 334 ms, or a `requestAnimationFrame` loop,
  whose callback changes styles, attributes or a canvas (the 2.x timer
  hook, extended to `requestAnimationFrame`);
- an animated image (`ImageDecoder` on the HAR bytes) with any frame delay
  under 334 ms whose frames differ in L by at least 0.1;
- any video that plays (pass T's reads);
- a 2 s CDP screencast (about 55 frames per second) beside pass T. Any
  cell whose L alternates by at least 0.1 more than 6 times in a second
  is a trigger. This is a net for what the other triggers miss, never
  evidence for DOES NOT APPLY on its own (research section 4).

A page with no trigger is A4 at no further cost.

**Flash capture** (on its own fresh load in the batch browser, viewport
1024 × 768, standard zoom):

- **Driven by the page's clock** (CSS and Web Animations, transitions,
  timers, `requestAnimationFrame`, canvas and WebGL):
  - install Playwright's clock and pause it before the page loads;
  - then for 3 s of page time, at 60 steps per second: `run_for` one
    step, set every paused animation's `currentTime`, and take a
    screenshot (`traverse.screenshot()`).

  Regions that are real-time media (GIFs, video, marquee) are masked out
  of these frames.
- **Animated images:** every frame decoded with `ImageDecoder`, analyzed
  over two full loops at the image's rendered size.
- **Video:** decoded in a tool page from the HAR or media-store bytes,
  played at 0.5× with `requestVideoFrameCallback`, for at most its first
  10 s. Frames are scaled to 1024 × 768, full screen (WCAG 2.2: analyze at
  the largest scale a user may view).
- **Not steppable yet** (`<marquee>`, SMIL): A3 unless V7 (in
  [3a-build-tasks.md](3a-build-tasks.md)) shows they can be stepped.

**Time budget.** Only when a trigger fires:

- the stepped capture: about 6 s of wall time for 3 s of page time;
- each video: up to 20 s (10 s at 0.5×);
- decoding images: fast.

This comes out of the extra allowance for pages with moving content (2.x
plan Q2). Checks call `ctx.out_of_time()` before each capture, and work
cut by time is A3.

## 3. The assessment (WCAG 2.0 SC 2.3.1)

Given only with A2. One assessment per flashing source (a region of the
stepped capture, an image, a video), then one for the page.

| # | Evidence | Assessment | Source |
| --- | --- | --- | --- |
| F1 | The flashing cells form a fine, balanced pattern (alternating cells smaller than 5 px, about 0.1 degree, with equal light and dark) | Could not assess: "this may be a fine pattern, which WCAG allows; a person should check" | WCAG 2.0 exception |
| F2 | General flashing over the threshold | Fails (general flash) | WCAG 2.0 SC 2.3.1, definition (1) and (2) |
| F3 | Red flashing over the threshold | Fails (red flash) | WCAG 2.0 Note 3 |
| F4 | Several sources each under the threshold, flashing in the same seconds, whose flashing areas would exceed it together inside one rectangle (only when their times cannot be aligned frame by frame) | Could not assess: "flashing in several places at once may add up; a person should check" | WCAG 2.0 ("combined area of flashes occurring concurrently") |
| F5 | Otherwise | Does not fail: "it flashes more than three times a second, but over a small enough area" | WCAG 2.0 definition (2); G176 |

The page's assessment is fails if any source fails; else could not assess
if any could not; else does not fail. Where WCAG 2.2's red rule gives a
different answer, the note says so (research O3).

**Plain-language sentences** (research O1 wording; the note never
explains the TT background):

| Case | Sentence |
| --- | --- |
| A2, fails | "The Trusted Tester process records flashing content as Not Tested. According to our experimental flash analysis, this flashing fails WCAG 2.3.1: <where>, <n> flashes per second, <area>, <general or red>. Flashing like this can cause seizures; fix it so it flashes no more than three times a second, or keep the flashing area small." |
| A2, does not fail | "The Trusted Tester process records flashing content as Not Tested. According to our experimental flash analysis, this flashing does not fail WCAG 2.3.1: <where>, <n> flashes per second, <area>, <general or red>. <We analyzed the first <x> s of <y>.>" |
| A2, could not assess | "The Trusted Tester process records flashing content as Not Tested. Our experimental flash analysis could not decide whether it fails WCAG 2.3.1: <reason>. A person should check it with a flash analysis tool." |
| A3 | "We could not check all of this page for flashing (<what>). A person should watch it." |
| A4 | "Nothing on this page flashes more than three times a second, so this test does not apply." |

**Notes (no outcome).** NOT TESTED does not meet Test 1.D (Non-Interference). Flashing slower than 3 per second that lasts more than 5 s is 2.B's concern.

## 4. Judgment questions

None. Every step is a measurement. Where measurement cannot decide (F1,
F4), the assessment is "could not assess" and a person checks.

## 5. Edge cases

| Case | Rule | Verify |
| --- | --- | --- |
| Exactly 3 flashes in a second, ending on the starting state | Not flashing (G19 passes it) | V2 |
| 7 transitions in a second (3.5 flashes) | Flashing (G19 Note 2) | V2 |
| A small flasher (one 40 × 40 px cell group) at 10 per second | Flashing found: NOT TESTED; assessment does not fail (area) | V3 |
| A red-to-black strobe with little luminance change | Red transitions: flashing found; F3 if over the area | V4 |
| A video that could go full screen | Analyzed at 1024 × 768, full screen | V5 |
| A looping GIF | Analyzed over two loops | V6 |
| A flash only after 10 s of a video | Not analyzed; A3, or the disclosure when other flashing was found | O4 |
| A strobe in a cross-site iframe | Captured in the viewport like any other pixels; its video decoded from the HAR | V8 |
| `prefers-reduced-motion` | Not set (the batch browser uses the default); a page's reduced-motion version is not the content tested | 2.x item 11 |

## 6. What the finding records

For each flashing source:

- where it is (its element, the box at 1024 × 768);
- the cells over 3 per second and their peak flashes per second;
- the largest concurrent flashing area, and the 341 × 256 rectangle it is
  in;
- general or red, and the WCAG 2.2 red result if different;
- the analyzed span (and for video, its length);
- a strip of frames and a plot of the brightest cell's L over the
  window.

The finding's summary carries the assessment sentence, so the SCRT export
keeps it in the tester comment.
