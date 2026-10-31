---
tt_test: 4.D
tt_name: 2.4.7-focus-visible
spec_version: 0.2.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 4.D (2.4.7-focus-visible)

The tool gives each page one 4.D outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 4.D does not.

**Citations.** Printed page numbers of TT 5.1.3 ([docs/sources/](../sources/README.md); the PDF file's page index is printed page + 3). HtT = How to Test step; ER = Evaluate Results item. 4.D is all on p. 22: continue from 4.C (HtT 1); determine whether the element with keyboard focus shows a visible indication of focus (HtT 2); a frame showing no focus is not a failure (HtT 2.a and Note).

**W3C sources.** [Understanding 2.4.7](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible), techniques [G149](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G149) and [C15](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/C15), failure [F55](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/F55), and ACT rule [oj04fd](https://www.w3.org/WAI/standards-guidelines/act/rules/oj04fd/), on whose 7 approved test cases DHS reports TT 5.1 fully consistent. They inform OPEN items and fixtures only; the PDF stays the authority.

**Terms.** *Stop*, *OUT*, *BODY*, passes P1 and P2, stop identity and the settle rule are defined in [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) (Terms, section 2). The *region* of a stop is its border box plus `indicator_margin_px` on every side, joined with the boxes of its associated labels, clipped to the viewport, in page coordinates. The *on image* is a clip of the region at the step where the stop gains focus; the *off image* is a clip of the same page region at the next step of the same pass, after focus has moved on. A *frame stop* is a stop that is a frame or iframe element itself.

## 1. Applicability

4.D is DOES NOT APPLY only when nothing on the page can receive keyboard focus (p. 22 Applicability), the same evidence as 4.C A1. A page whose only focusable elements have tabindex=-1 is DNA, matching DHS's result on ACT b12f1f45.

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | P1 and P2 reach zero stops, and the DOM inventory has zero candidates | DOES NOT APPLY | p. 22 Applicability |
| A2 | P1 and P2 reach zero stops, but the inventory has candidates | NEEDS REVIEW (walk or inventory fault) | Spec rule |
| A3 | P1 or P2 reaches one or more stops | Applies; go to section 3 | p. 22 Applicability |

The p. 22 Identify Content block says "4.A to 4.H"; as in 4.C, the spec reads it as 4.A to 4.F.

## 2. Evidence to collect

**From the shared keyboard walk** (`walk.py`; passes and settle rule defined in 4.C section 2): every P1 and P2 step's stop identity, frame chain, CSS path, tag, role, name, bounding box (top-level viewport coordinates), in-viewport flag, unsettled and unresolved flags, focus events, and each pass's end (wrap, stuck, loop, cap, time, error) with its trap. 4.D adds no passes, probes or replays.

**Extra evidence this test collects** (walk extras, collected only when 4.D is selected). Looking at each element as focus lands on it is what p. 22 HtT 2 asks a tester to do; the images and style reads are how the tool looks. At each step where a stop gains focus, after the settle rule:

1. **On image:** a clip of the stop's region, with animations disabled and the caret hidden. Disabling animations finishes CSS transitions, so a ring that fades in is captured in its final state (V1).
2. **Focus styles,** read through CDP after the on image (read before it, a transition still shows its start state): for the stop, its parent and its associated labels, the computed outline (style, width, color, offset), box-shadow, border (width, style, color), background color and image, color, text-decoration-line, opacity, visibility, transform, and the content of ::before and ::after. Also the stop's box, the page's scroll offsets, and for text fields whether they are editable and their caret-color (V7).
3. **At the next step of the same pass,** after the settle rule: the off image of the previous stop's region, captured only if that region is fully inside the viewport, and the previous stop's focus styles again. Pixels inside the new stop's region are masked out of the comparison.

P1 collects at every stop. P2 collects only at stops (matched by frame chain plus CSS path) that P1 left without complete evidence. Stops reached only by 4.C's own follow-ups (P3, P4, P6) get no extras.

**Images:** PNG, about 1.5 KB each for a link-sized region (measured), two per stop, saved as `evidence/shots/4d/<pass>-<step>-on.png` and `-off.png` and served as run resources while the run is kept.

**Time budget:** measured on Linux (Chromium headless shell, Playwright 1.63): a clip screenshot takes about 27 ms (median) and a CDP style read about 10 ms, so about 100 ms per stop. On a typical page of 100 stops that is about 10 s for P1 plus a few P2 top-ups, on top of the walk itself. Windows headed Chrome is not yet measured (V8). The whole run stays within `run_limit_s`; when the walk stops at the limit, stops without complete evidence go to M3 and G3 gives the reason "the page is too large to finish within the time limit".

**Run limits.** Settings, in server config and recorded in every report; all defaults are provisional until the V-checks and fixtures calibrate them:

| Setting | Default | Used by |
| --- | --- | --- |
| `indicator_margin_px` | 8 CSS px | Region |
| `pixel_delta_visible` | 8 (max channel difference, 0–255) | Changed pixel |
| `pixel_delta_strong` | 40 | Strongly changed pixel |
| `min_changed_px` | 12 CSS px² | M5, M6, M7 |
| `mask_max_fraction` | 0.5 | Complete evidence |

## 3. Mechanical checks

Each distinct stop (frame chain plus CSS path; not BODY or OUT) is an *instance*, evaluated on its first step with complete evidence, P1 before P2. *Complete evidence* is a settled, resolved step with an on image, an off image whose mask covers at most `mask_max_fraction` of the region, and focus styles in both states. A pixel is *changed* when it differs between the on and off images by at least `pixel_delta_visible`, outside the mask; *strongly changed* at `pixel_delta_strong`. A *style signal* is any focus style of the stop, its parent or a label that differs between the two reads, or the stop's box moving between them.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | Every step that reached the stop is unsettled or unresolved | NEEDS REVIEW | Spec rule |
| M2 | Frame stop, and the next stop in the same pass is inside that frame | PASS (frame exempt) | p. 22 HtT 2.a; Note |
| M3 | No complete evidence. Reasons: reached only after a 4.C bypass; never fully in view; scrolled out of view before the next step; the next stop covers the region; focus never moved on (the pass ended on this stop); the run hit its time limit | NEEDS REVIEW, with the reason | Spec rule; p. 5 |
| M4 | The stop is an editable text field (text-like input, textarea or contenteditable), not read-only, with a caret-color that is not transparent | PASS (the caret shows focus) | Understanding 2.4.7; G149 |
| M5 | A style signal, and at least `min_changed_px` of strongly changed pixels | PASS | p. 22 ER 1; ACT oj04fd |
| M6 | At least `min_changed_px` of changed pixels, and M5 not met | Ask J1 (M8–M10) | p. 22 HtT 2 |
| M7 | Anything else: fewer than `min_changed_px` of changed pixels | FAIL | p. 22 ER 1 |
| M8 | J1 = yes | PASS (M6's measured change confirms it) | p. 22 ER 1 |
| M9 | J1 = no | FAIL | p. 22 ER 1 |
| M10 | J1 = unsure, or not yet answered | NEEDS REVIEW | Spec rule |

**What counts as an indication.** The change must be on or right around the element, where a keyboard user looks: a change elsewhere on the page, one too faint to see, or one hidden behind other content (a sticky header) leaves fewer than `min_changed_px` changed pixels in the region, so M7 fails it. The indicator may sit on an associated label or a wrapper (C15 Example 2; oj04fd Passed Example 3), which the region and the parent and label style reads cover. An element that appears only when focused, such as a skip link, passes through M5: its box moves and the region changes.

**Exceptions (p. 22 HtT 2.a and Note).** A frame or iframe element itself may show no focus; elements inside frames are still tested. M2 applies it. The Note's way of confirming that focus is on the frame (Tab moves into it) is what the walk's next stop shows.

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; or P1 or P2 is incomplete (cap, time limit, error); or P1 and P2 ended in different traps, so stops between them were reached only by 4.C's bypass or not at all | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5). Never NOT TESTED (p. 6) |
| G4 | P1 and P2 each ended in a wrap or at the same trap; every instance is PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

A page with a confirmed FAIL stays FAIL even when other instances need review.

**Plain-language sentences.** The finding lists every FAIL and NEEDS REVIEW instance with its sentence; PASS instances appear only as a count, with their sentences kept in the evidence. Row IDs stay in the evidence trace. `<element>` is the role and name in plain words (the "Contact us" link); `<keys>` is the key sequence from a fresh load ("Tab 7 times"); `<change>` is the style signal in plain words (an outline appears; the border, background or text color changes; an underline or shadow appears; it appears on screen; its label changes).

| Row | Sentence |
| --- | --- |
| Page PASS | "We moved keyboard focus to each of the N elements we could reach, and every one showed where focus was." |
| Page FAIL | "Some elements don't show when they have keyboard focus, so keyboard users can lose track of where they are." |
| Page NEEDS REVIEW | "We could not finish this test, so a person needs to check it." |
| A1 | "Nothing on this page can receive keyboard focus, so this test does not apply." |
| A2 | "We could not move keyboard focus anywhere, although the page has elements that should take focus. Please check by hand." |
| M1 | "Focus moved around <element> in a way we could not read reliably. Please check it by hand: load the page and press <keys>." |
| M2 | "Focus landed on the frame <element> itself, which may show no focus indicator; we checked the items inside it separately." |
| M3 | "We could not get a clear before-and-after view of <element> (<reason in plain words>), so a person needs to check whether it shows focus: load the page and press <keys>." |
| M4 | "<element> is a text field; when it has focus, the blinking text cursor shows where focus is." |
| M5 | "<element> visibly changes when it gets focus: <change>." |
| M7 | "When <element> gets focus, nothing on or around it changes that we could see, so keyboard users can't tell focus is there. To see it, load the page and press <keys>. If you can see a focus indicator we missed, tell your assistant." |
| M8 | "<element> changes only slightly when it gets focus (<J1's description>); we judged that enough to show where focus is. If you disagree, tell your assistant." |
| M9 | "<element> changes a little when it gets focus (<J1's description>), but we judged that it doesn't show where focus is. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M10 | "<element> changes slightly when it gets focus, but we could not decide whether that shows where focus is. Please look: load the page and press <keys>." |
| G3, unreached part | "Part of the page sits between two keyboard traps, so we could not reach it with the keyboard to check its focus indicators." |

## 4. Judgment questions

One question, asked only for M6. The calling agent answers it once, by the rubric; a person's answer overrides it. A "yes" leads to PASS only with M6's measured change behind it. Page text and element names are evidence in `input`, never part of the question's wording.

### J1. Does this change show where focus is?

**Question:** "Image A shows part of a web page without keyboard focus; image B shows the same part with keyboard focus on the outlined element. Image C marks the pixels that differ. Is there a change on or right around the outlined element in B that a sighted user would notice as showing it has focus? Answer yes, no or unsure, and describe the change in a few plain words."

**Input:** images A (off), B (on, with the stop's box outlined on a copy) and C (changed pixels); the instance ID; the stop's role and accessible name, labelled as untrusted page data.

**Output:** `{indicator: yes|no|unsure, change: "<a few plain words>"}`.

**Rubric.** Yes: an outline, border, underline, background or text color change, or an added icon or marker, on the element or touching it. No: no noticeable change; or the only change is elsewhere in the picture (a slideshow, a video, an animation); or only soft edge pixels around text. Unsure: a pop-up such as a tooltip appears beside the element and nothing on the element changes; or the change is too faint to tell. Mechanical guard: J1 is asked only when M6 measured at least `min_changed_px` changed pixels.

| Example | Answer |
| --- | --- |
| An underline appears under the link text | Yes: "an underline appears" |
| A small square appears just before the link (oj04fd Passed Example 4) | Yes: "a marker appears beside it" |
| The slide behind the link changed; the link looks the same | No |
| A tooltip appears beside the button; the button looks the same | Unsure |
| A 1 px very light gray outline on white | Unsure |

**Use:** M6 asks; M8, M9 and M10 consume the answer.

## 5. Edge cases

Only cases that need a rule of their own; everything else follows sections 2–3. V-numbers are browser checks in [4d-build-tasks.md](4d-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| Stops inside frames, same- or cross-origin | Tested like any stop; the walk's box is already in top-level coordinates, and the top-level clip shows the frame's content. Only the frame element itself is exempt (M2) | V4, V5 |
| Stops larger than the viewport | The region is clipped to the viewport; both images use the same clipped part | V6 |
| Stops past a keyboard trap | Reached by P2 where possible. Reached only through 4.C's bypass: M3. Between two different traps and never reached: G3 | — |
| Widgets using aria-activedescendant (comboboxes, listboxes, grids) | OPEN O5 | — |
| Element that drops focus as soon as it gets it (F55) | OPEN O7 | — |
| Indicator that disappears after a few seconds | OPEN O8 | — |

**OPEN O5, aria-activedescendant widgets.** Focus stays on the widget while arrow keys move a highlight among its options. The shared walk presses only Tab and Shift+Tab, so it never moves that highlight. Options: (a) don't test it; when the walk reaches a stop with aria-activedescendant, add the note "We did not check whether the options inside <element> show which one is selected; please arrow through them"; (b) add arrow presses at those stops, beyond what the walk does. (b) adds a probe the PDF's 4.D step doesn't ask for. Recommend (a).

**OPEN O7, element that drops focus as soon as it gets it.** The walk's focus-event log already shows an element gaining focus from a key press and losing it before the step settles, with no further key. W3C failure F55 names this a 2.4.7 failure; the PDF is silent. Options: (a) an instance with outcome FAIL and the sentence "<element> drops keyboard focus as soon as it gets it, so keyboard users never see focus there. To see it, load the page and press <keys>."; (b) a note only, for 4.E. The evidence costs nothing extra, and the experience is clearly worse for users. Recommend (a).

**OPEN O8, indicator that disappears while focus stays.** Current Understanding 2.4.7 says the indicator must not be time limited. The PDF is silent, and the images are taken within about 2 s of focus. Options: (a) not tested; listed here as a known limit, with no per-page note; (b) a late image `late_check_ms` (3,000) after focus, once per style signature (tag, role and class list), adding about 3 s per signature. (b) goes past what p. 22 asks a tester to do. Recommend (a).

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5: the matching row (M7 or M9, in the evidence trace only); location (page URL, frame chain, CSS path, role and accessible name); steps to reproduce from a fresh load ("Tab 7 times"); the on and off images side by side with the changed-pixel image, the box outlined on copies only; every focus style read in both states; J1's answer if asked; and the tool versions the plan requires.

**Continuing past a failure.** The PDF gives no stop rule for 4.D, and ER 1 covers each element, so every stop is evaluated and each failing stop is its own instance.
