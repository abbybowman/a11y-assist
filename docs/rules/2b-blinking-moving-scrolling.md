---
tt_test: 2.B
tt_name: 2.2.2-blinking-moving-scrolling
spec_version: 1.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 2.B (2.2.2-blinking-moving-scrolling)

The tool gives each page one 2.B outcome: PASS, FAIL, DOES NOT APPLY or
NEEDS REVIEW. It never emits NOT TESTED (p. 6). PASS is gated as in 2.C:
a working mechanism gives NEEDS REVIEW until every test that can apply to
it is built ([2c-auto-updating.md](2c-auto-updating.md) section 3c).

1.0.0 (Abby, 2026-11-05): approved and built, from draft 0.2.0. 0.2.0 (2026-11-04), from building it: still moving and colour-only as below; motion below the first screen; content with no element inside is placed by document order; one probe per content shared with 2.C; J1 can only lead to DNA; the text question is J3. Plan:
[research/2026-11-03-auto-updating-2a-2d.md](../research/2026-11-03-auto-updating-2a-2d.md).

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/2.B`). Identify Content, p. 14: before loading, "make sure the browser is not set to block auto-playing content"; visual content that "Starts moving, blinking, or scrolling without user activation (including videos, synchronized media, and scrolling text)", "Moves, blinks, or scrolls continuously for more than 5 seconds", and "Is not the only content on the page"; "EXCLUDE content where the movement, blinking, or scrolling of the content is essential"; none: DNA. Notes, p. 14: content that moves without changing is 2.B only; content that changes is 2.C; both when both. Applicability, p. 14. HtT 1 ("an evident mechanism ... within the first three elements that the user would encounter OR within three elements before/after the moving/blinking/scrolling content"), HtT 2–3, p. 14. ER 1 (an evident mechanism that can pause, stop or hide the content), ER 2 (where), ER 3 (it passes all applicable Test Conditions), p. 14. Appendix B: 5.1.3 made the mechanism "evident".

**Other sources.** [Understanding 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html): moving, blinking and scrolling is content where "the visible content conveys a sense of motion" (motion pictures, animations, scrolling tickers); a preload animation can be essential when no interaction is possible during it (Note 4); a pause must not tie up focus. Sufficient [G4](https://www.w3.org/WAI/WCAG22/Techniques/general/G4), [G11](https://www.w3.org/WAI/WCAG22/Techniques/general/G11) (blinking stops within 5 s), [G152](https://www.w3.org/WAI/WCAG22/Techniques/general/G152) (an animated GIF: frames × delays × loops ≤ 5 s), [G186](https://www.w3.org/WAI/WCAG22/Techniques/general/G186), [G191](https://www.w3.org/WAI/WCAG22/Techniques/general/G191) (reload without blinking), [SCR22](https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR22), [SCR33](https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR33); failures [F16](https://www.w3.org/WAI/WCAG22/Techniques/failures/F16), [F50](https://www.w3.org/WAI/WCAG22/Techniques/failures/F50), F7; F4 and F47 (`text-decoration: blink`, `<blink>`) are obsolete and do not blink in Chrome (plan item 9). No ACT rule for moving content; DHS course issues [#203](https://github.com/Section508Coordinators/DHSA-TT-200-A/issues/203) (a pause control within three elements of a video passes) and [#425](https://github.com/Section508Coordinators/DHSA-TT-200-A/issues/425) (a working disable-animation button passes). ICT Testing Baseline 3.1 21.B-MovingInfo. No Baseline Alignment cases.

**Terms.** Pass T, frame, region, content, kind, element, windows, candidate, period, the mechanism probe and rows K1–K8, E1–E4: [2c-auto-updating.md](2c-auto-updating.md) (Terms, sections 2 and 3). A *moving region* is a region of kind moving, or auto-updating whose children also move, that is *still moving*: it changes in frames after 5 s from the start of the load, and in at least three frames over the watch (0.2.0: 0.1.0 also asked that no gap be longer than its period plus 1 s, which random colours repeating for two seconds broke on ACT efbfc7 inapplicable 3; frames alternate 0.35 s and 0.45 s apart, since at a steady 0.5 s a 0.5 s blink was caught in the same state every frame). It is also moving when the reads show any of these, found anywhere on the page, below the first screen included (`motion.extras`):

- an animation (`getAnimations()`) running at load with more than 5 s of
  active time (iterations × duration, infinite included);
- an animated image whose one play-through times its loop count exceeds
  5 s, by `ImageDecoder` on the recorded bytes (G152; infinite loops
  included). Built: decoded in a tool page of its own at `http://localhost`
  (answered by a route, no network, no page script), because `ImageDecoder`
  exists only in a secure context and `about:blank` is not one;
- a `<marquee>`;
- a video playing at 3.5 s with more than 5 s left, or looping.

A *color-only change* is a region whose text, image sources, boxes and
transforms stay the same while its pixels change, that is not drawn
content (canvas, image, video, SVG, iframe, marquee), and that shows a sign
of styling: computed `color`, `background-color`, `border-color`, `fill`,
`stroke`, `opacity` or `visibility` differ between reads, its style
changed, or an animation runs on it (0.2.0: three reads alone missed a
cycle that came back to its first colour on the reads). Its *states* are
the distinct looks of its box over the frames. It counts as blinking, so it can be a
moving region (Abby, 2026-11-03). Blinking is "switch back and forth
between two visual states in a way that is meant to draw attention" (WCAG
2.0 and 2.2 Key Terms). It has *two states* when its colors alternate
between two sets of values, and *three or more* otherwise (a cycle through
red, green, blue and black, as in ACT efbfc7 inapplicable 3).

For 2.B, *stopped* means no change of the content's pixels during the
confirm time, the content no longer rendered, or (for a video) paused.
"Slowed" does not count: 2.B has no frequency mechanism.

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | Pass T could not run or read the page; or a video could not play from the recording (an `error`, a streaming player such as YouTube or Vimeo, or media over the recording cap) | NEEDS REVIEW, not performed, with the reason. For media over the cap the note gives each file's size and length, and the result offers a run with no time limit (Abby, 2026-11-03, plan Q9) | p. 5; plan items 13–14, 17 |
| A2 | No moving region | DOES NOT APPLY | p. 14 Applicability |
| A3 | Every moving region's content covers all the page's elements | DOES NOT APPLY: it is the only content | p. 14 Applicability |
| A4 | Every moving region is essential (J1 = essential) | DOES NOT APPLY, naming it | p. 14 Identify Content (EXCLUDE essential) |
| A5 | J1 unsure or unanswered for a region, and no other moving region applies | NEEDS REVIEW | Spec rule |
| A6 | Otherwise | Applies to the moving regions that are not essential; go to section 3 | |

## 2. Evidence to collect

Pass T and the mechanism probe as in [2c-auto-updating.md](2c-auto-updating.md) section 2, shared. Pass T's reads add, for each region:

- its animations' timing, from `getAnimations()`;
- for each animated image: frames, loop count and one play-through, from
  `ImageDecoder` on the bytes in the HAR;
- for each video: paused, muted, `currentTime` progress, duration and
  loop, read in its own frame.

The probe uses all four windows, and 2.B's meaning of stopped. A region
that is both moving and auto-updating is probed once, for 2.B and 2.C
together.

**Time budget:** none beyond 2.C's (shared probes).

## 3. Mechanical checks

Each moving region that applies is an *instance*.

**3a. Instance rules.** Rows K1–K8 and E1–E4 of [2c-auto-updating.md](2c-auto-updating.md) section 3a, first match wins, with 2.B's meaning of stopped (K3: stopped only; "slowed" is no effect). E1–E4 read 2.C's J1 (evident) as J2 below, asked once when the same control serves both tests. The text-candidate question is 2.C's J2. One row comes before K6:

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| C1 | The instance is a color-only change with three or more states, and K6's evidence holds (no mechanism) | NEEDS REVIEW: "<content> keeps changing color by itself, and we found no way to stop it. WCAG defines blinking as switching back and forth between two visual states to draw attention. This cycles through <n> colors, so whether it counts as blinking is a call for a person: if it draws attention the way blinking does, it needs a pause control." | Abby, 2026-11-03; WCAG blinking definition; plan (WCAG 2.0 Understanding 2.2.2 review) |

A two-state color change with no mechanism is unambiguous blinking: K6
gives FAIL, as for any blinking content.

**3b. Page outcome.** As [2c-auto-updating.md](2c-auto-updating.md) section 3b, G1–G5.

**3c. ER 3.** As 2.C section 3c.

**Notes (no outcome).** `<blink>` and `text-decoration: blink` found in the page: "they do not blink in Chrome, the browser we test with; other browsers may differ."

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| Page PASS | "<content> moves by itself for more than 5 seconds, and <mechanism> lets users stop it." |
| E3 | "<content> moves by itself, and <mechanism> stops it when pressed with the keyboard. A person still needs to check <mechanism> for <tests>, which this tool does not test yet." |
| K6 | "<content> keeps moving for more than 5 seconds, and we found no way to stop or hide it in the three items before it, the three after it, or the first three on the page. Add a pause button next to it." |
| A2 | "Nothing on this page moved for more than 5 seconds while we watched, so this test does not apply." |
| A4 | "<content> moves, but only while the page loads and nothing can be used yet, so it does not need a pause." |

## 4. Judgment questions

### J1. Is the movement essential?

Asked for each moving region. Not settled by looking for PASS: it can
only lead to DOES NOT APPLY, and the agent answers unsure whenever the
evidence does not settle it (a false DNA is as bad as a false PASS).

**Question:** "input.content moves by itself (images A and B, 1 s apart; input.images_show says what they show, and the content is at input.box on the page; input.timing). Would removing the movement fundamentally change what the content is or does, for example a loading animation shown while nothing on the page can be used yet, or a game or simulation whose motion is the point? Decorative motion, carousels, tickers, banners and background video are not essential. Answer essential, not_essential or unsure."

**Images** (1.1.0). Images A and B are two of pass T's frames, about 5 s and 6 s into the watch, which show the first screen. Content that no frame shows whole (below the first screen, or found by the scrolled watch, whose frames are not kept) gets its own two pictures instead: cut from the whole page around its box (40 px around it, at least 320 by 200 px), about 1 s apart at the end of its watch, with animations running (`motion.Region.crops`; at most 6 regions per watch). `images_show` says which. Judge eval run 16: with no frame showing the badge below the first screen, J1 could only be unsure. Fixture: `2x/t-below-fold.html`.

**Output:** `{choice: essential|not_essential|unsure, reasons}`. Guard: a region still moving at 6.5 s while the page has usable controls cannot be a loading animation; answer essential is then accepted only with a reason other than loading.

**Use:** A4, A5.

### J2. Is the mechanism evident?

2.C's J1, as written there.

## 5. Edge cases

| Case | Rule | Verify |
| --- | --- | --- |
| A muted looping background video | Moving (2.B); not audio (2.A DNA for it) | V2 |
| An animated GIF that loops forever | Moving by G152; the probe as usual (no page mechanism is common: K6) | V3 |
| A play-once GIF of 2 s | Not moving (under 5 s) | V3 |
| A carousel that slides | Moving and auto-updating: one probe, 2.B and 2.C each decide | V6 |
| A spinner removed before 5 s | Not moving | V3 |
| A CSS animation below the first viewport | Moving by its animation timing; the probe as usual | V4 |
| `<blink>`, `text-decoration: blink` | Not rendered by Chrome: a note only | plan item 9 |
| Text whose color changes every second, nothing else (ACT efbfc7 inapplicable 3, which is about 2.C) | A color-only change, so blinking (Abby, 2026-11-03). That case cycles four colors, so with no mechanism it is C1, NEEDS REVIEW. Its "Stop color changes" button is in the after window, so the probe normally finds it (K3). 2.C is DOES NOT APPLY, matching ACT and DHS. No WCAG technique or failure mentions color changes. Every blinking technique toggles visibility or frames (SCR22, F50, F47, F4, G11, G152, FLASH36). SL11 alone notes that Color-valued properties can be animated | ACT efbfc7; WCAG 2.0 Understanding 2.2.2 and its techniques (read 2026-11-03) |
| A color change faster than 3 per second, large and bright enough to be a flash | Also 3.A's concern (Understanding 2.2.2: blinking faster than 3 per second "would also be considered a flash") | 3.A research |

## 6. What a FAIL records

For each instance:

- the content and how it moves (two crops 1 s apart, animation timing, or
  G152 figures);
- every candidate, with its window, position, probe result and row;
- the J1 and J2 answers;
- how to reach each candidate.
