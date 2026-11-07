---
tt_test: 4.D
tt_name: 2.4.7-focus-visible
spec_version: 1.3.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 4.D (2.4.7-focus-visible)

The tool gives each page one 4.D outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 4.D does not.

**Citations.** Printed page numbers of TT 5.1.3 ([docs/sources/](../sources/README.md); the PDF file's page index is printed page + 3). HtT = How to Test step; ER = Evaluate Results item. 4.D is all on p. 22: continue from 4.C (HtT 1); determine whether the element with keyboard focus shows a visible indication of focus (HtT 2); a frame showing no focus is not a failure (HtT 2.a and Note).

**W3C sources.** [Understanding 2.4.7](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible), techniques [G149](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G149) and [C15](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/C15), failure [F55](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/F55), and ACT rule [oj04fd](https://www.w3.org/WAI/standards-guidelines/act/rules/oj04fd/), on whose 7 approved test cases DHS reports TT 5.1 fully consistent. They inform OPEN items and fixtures only; the PDF stays the authority.

**Terms.** *Stop*, *OUT*, *BODY*, passes P1 and P2, stop identity and the settle rule are defined in [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) (Terms, section 2). The *region* of a stop is its border box plus `INDICATOR_MARGIN_PX` on every side, joined with the boxes of its associated labels and of any ancestor (up to its nearest block container) whose style changes between the two reads and whose area is at most `ANCESTOR_MAX_FACTOR` times the stop's own region or `ANCESTOR_MAX_AREA` (an indicator on a wrapper or card, as in oj04fd Passed Example 3 and C15 Example 2), clipped to the viewport, in page coordinates. The *on image* is a clip of the region at the step where the stop gains focus; the *off image* is a clip of the same page region at the next step of the same pass, after focus has moved on. A *frame stop* is a stop that is a frame or iframe element itself.

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
2. **Noise read,** only when the page is changing (the step did not settle, the DOM changed during it, or CSS animations are running): a second on image and style read `NOISE_WAIT_MS` later, while focus stays. Pixels and style properties that differ between the two are animation, not a focus indicator, and are left out of the comparison (a slideshow behind a link cannot count as its indicator). The tool's own screenshots are not DOM changes (4.C spec section 2, 1.7.0); before 1.1.0 they were, and on pages with a text field every step took the noise read (1.1.0).
3. **Focus styles,** read through CDP after the on image (read before it, a transition still shows its start state): the whole computed style of the stop, its ancestors up to the nearest block container, its associated labels, and their ::before and ::after, compared as a whole between the two reads rather than property by property. Also the stop's box, the page's scroll offsets, and for text fields whether they are editable and their caret-color (V7).
4. **At the next step of the same pass,** after the settle rule, once the focus subject has changed: the off image of the previous stop's region, captured only if that region is fully inside the viewport, and the previous stop's focus styles again. Pixels inside the next subject's box (the next stop, or the next active item of a widget) are masked out of the comparison.

**Widget pass W** (one fresh replay per composite widget the walk reached: menubar, menu, tablist, grid, treegrid, tree, listbox, toolbar, radio group, and any element with aria-activedescendant). Items inside a widget get focus only from arrow keys, which 4.C's How to Test uses ("arrow keys", p. 21 HtT 1) and 4.D continues from. Replay to the widget's stop, then press ArrowDown (or ArrowRight, if ArrowDown moves nothing) up to `WIDGET_ITEMS_MAX` times, collecting the same on and off images and style reads at each press; at the end of the widget, the opposite arrow once, so the last item gets its off read. The *item* at each press is the element with DOM focus (roving tabindex), or the element its aria-activedescendant names (WAI-ARIA 1.2: the active descendant "is treated as having keyboard focus in the user interface", and the author styles it). Items of one widget share their styling, so the first `WIDGET_ITEMS_MAX` stand for the rest; a page with more than `WIDGET_MAX` widgets is G3. (4.C's widget check, P4, presses one arrow and then Tab at the same stops; the two could share one replay.) The stops pass W's arrows reach are kept for 4.A's arrow probe in the same call (1.1.1).

P1 collects at every stop. P2 collects only at stops (matched by frame chain plus CSS path) that P1 left without complete evidence. Stops reached only by 4.C's own follow-ups (P3, P4, P6) get no extras.

**Images:** PNG, about 1.5 KB each for a link-sized region (measured), two per stop, saved as `evidence/shots/4d/<pass>-<step>-on.png` and `-off.png` and served as run resources while the run is kept.

**Time budget:** measured with the build on Linux (Chromium headless shell): a 100-link page takes 53 s for the walk and 4.D together, of which the walk is about 36 s. Widget pass W adds one replay per widget (about 2–3 s). Earlier estimate, measured on Linux (Chromium headless shell, Playwright 1.63): a clip screenshot takes about 27 ms (median) and a CDP style read about 10 ms, so about 100 ms per stop. On a typical page of 100 stops that is about 10 s for P1 plus a few P2 top-ups, on top of the walk itself. Windows headed Chrome is not yet measured (V8). The whole run stays within `run_limit_s` (4.C spec section 2, Run limits): pass W starts no widget after the checks' deadline (1.1.0); when the walk stops at the limit, stops without complete evidence go to M4 and G3 gives the reason "the page is too large to finish within the time limit".

**Constants.** These decide outcomes, so they live in this spec, not in server config (CLAUDE.md principle 2): changing one is a spec version change. Provisional until the V-checks and fixtures calibrate them.

| Constant | Value | Used by |
| --- | --- | --- |
| `INDICATOR_MARGIN_PX` | 8 CSS px | Region |
| `PIXEL_DELTA_VISIBLE` | 8 (max channel difference, 0–255) | Changed pixel |
| `PIXEL_DELTA_STRONG` | 40 | Strongly changed pixel |
| `MIN_CHANGED_PX` | 12 CSS px² | M6, M7, M8 |
| `MASK_MAX_FRACTION` | 0.5 | Complete evidence |
| `WIDGET_ITEMS_MAX` | 5 items per widget | Widget pass W |
| `ANCESTOR_MAX_FACTOR`, `ANCESTOR_MAX_AREA` | 4, 40,000 CSS px² | Region |
| `NOISE_WAIT_MS` | 150 ms | Noise read |
| `WIDGET_MAX` | 10 widgets per page | Widget pass W, G3 |

## 3. Mechanical checks

Each distinct stop (frame chain plus CSS path; not BODY or OUT), and each widget item from pass W, is an *instance*, evaluated on its first step with complete evidence, P1 before P2. *Complete evidence* is a resolved step, not re-read, with an on image, an off image whose mask covers at most `MASK_MAX_FRACTION` of the region, and focus styles in both states. A pixel is *changed* when it differs between the on and off images by at least `PIXEL_DELTA_VISIBLE`, outside the mask and outside the noise read's changed pixels; *strongly changed* at `PIXEL_DELTA_STRONG`. A *style signal* is any computed-style difference between the two reads on the stop, an ancestor up to its block container, a label or their pseudo-elements, or the stop's box moving between them.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | Every step that reached the stop is unresolved, or was re-read because focus moved after the settle window | NEEDS REVIEW | Spec rule |
| M2 | Frame stop, and the next stop in the same pass is inside that frame | PASS (frame exempt) | p. 22 HtT 2.a; Note |
| M3 | The focus log shows the stop gaining focus from the key press and losing it again before the step settles, with no further key (focus dropped on focus) | FAIL | F55 (Abby, 2026-10-31: fail in 4.D and in 4.E) |
| M4 | No complete evidence. Reasons: reached only after a 4.C bypass; never fully in view; scrolled out of view before the next step; the next stop covers the region; focus never moved on (the pass ended on this stop); the run hit its time limit; it moved on the page between its measure and the pictures, and fewer than `MIN_CHANGED_PX` changed (a layout shift: the region compared was not where it was drawn; 1.2.0, post-round 1 fix 11: NASA's Artemis III links failed at 0 px this way, and the pictures showed the link's focus ring outside the region); fewer than `MIN_CHANGED_PX` changed although its focus style draws something (an outline whose style changed with focus and is not none, with a width and a colour that can be seen; a box-shadow that changed and is not none; or a border that grew), and the element is on top at its own centre (`elementFromPoint`): the indicator is clipped or drawn elsewhere, such as on a card around a title, which the pictures of the element cannot settle (1.2.0, post-round 1 fix 11: NASA's Missions card titles failed at 0 px). A covered element (a fixed header over it, F07) and a style that draws nothing (`outline: none`) still fall to M8 | NEEDS REVIEW, with the reason | Spec rule; p. 5 |
| M5 | The stop is an editable text field (text-like input, textarea or contenteditable), not read-only, with a caret-color that is not transparent | PASS (the caret shows focus) | Understanding 2.4.7, Examples ("a vertical bar is displayed in the field"); G149 |
| M6 | A style signal, and at least `MIN_CHANGED_PX` of strongly changed pixels | PASS | p. 22 ER 1; ACT oj04fd |
| M7 | At least `MIN_CHANGED_PX` of changed pixels, and M6 not met | Ask J1 (M9–M11) | p. 22 HtT 2 |
| M8 | Anything else: fewer than `MIN_CHANGED_PX` of changed pixels | FAIL | p. 22 ER 1 |
| M9 | J1 = yes | PASS (M7's measured change confirms it) | p. 22 ER 1 |
| M10 | J1 = no | FAIL | p. 22 ER 1 |
| M11 | J1 = unsure, or not yet answered | NEEDS REVIEW | Spec rule |

**What counts as an indication.** The change must be on or right around the element, where a keyboard user looks: a change elsewhere on the page, one too faint to see, or one hidden behind other content (a sticky header) leaves fewer than `MIN_CHANGED_PX` changed pixels in the region, so M8 fails it. The indicator may sit on an associated label or a wrapper (C15 Example 2; oj04fd Passed Example 3), which the region and the parent and label style reads cover. An element that appears only when focused, such as a skip link, passes through M6: its box moves and the region changes. A focused element hidden behind a sticky header fails here (no indicator a tester could see, p. 22 ER 1); WCAG 2.2 also covers this as 2.4.11 Focus Not Obscured, which is outside TT 5.1.3 (WCAG 2.0).

**Exceptions (p. 22 HtT 2.a and Note).** A frame or iframe element itself may show no focus; elements inside frames are still tested. M2 applies it. The Note's way of confirming that focus is on the frame (Tab moves into it) is what the walk's next stop shows.

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; or P1 or P2 is incomplete (cap, time limit, error); or more than `WIDGET_MAX` widgets; or the run limit was reached before widget pass W checked every widget (1.1.0); or P1 and P2 ended in different traps, so stops between them were reached only by 4.C's bypass or not at all | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5). Never NOT TESTED (p. 6) |
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
| M3 | "<element> drops keyboard focus as soon as it gets it, so keyboard users never see focus there. To see it, load the page and press <keys>." |
| M4 | "We could not get a clear before-and-after view of <element> (<reason in plain words>), so a person needs to check whether it shows focus: load the page and press <keys>." |
| M5 | "<element> is a text field; when it has focus, the blinking text cursor shows where focus is." |
| M6 | "<element> visibly changes when it gets focus: <change>." |
| M8 | "When <element> gets focus, nothing on or around it changes that we could see, so keyboard users can't tell focus is there. To see it, load the page and press <keys>. If you can see a focus indicator we missed, tell your assistant." |
| M9 | "<element> changes only slightly when it gets focus (<J1's description>); we judged that enough to show where focus is. If you disagree, tell your assistant." |
| M10 | "<element> changes a little when it gets focus (<J1's description>), but we judged that it doesn't show where focus is. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M11 | "<element> changes slightly when it gets focus, but we could not decide whether that shows where focus is. Please look: load the page and press <keys>." |
| G3, unreached part | "Part of the page sits between two keyboard traps, so we could not reach it with the keyboard to check its focus indicators." |

## 4. Judgment questions

One question, asked only for M7. The calling agent answers it once, by the rubric; a person's answer overrides it. A "yes" leads to PASS only with M7's measured change behind it. Page text and element names are evidence in `input`, never part of the question's wording.

### J1. Does this change show where focus is?

**Question:** "Image A shows part of a web page without keyboard focus; image B shows the same part with keyboard focus on the outlined element. Image C marks the pixels that differ. Is there a change on or right around the outlined element in B that a sighted user would notice as showing it has focus? input.changed_pixels counts the pixels that differ, in CSS pixels: on the element, touching it (within 8 pixels of its edge) and elsewhere in the picture. Answer yes, no or unsure, and describe the change in a few plain words."

**Input:** images A (off), B (on, with the stop's box outlined on a copy) and C (changed pixels); the instance ID; the stop's role and accessible name, labelled as untrusted page data; `changed_pixels` (1.3.0): the pixels that differ between A and B, in CSS pixels, on the element's box, touching it (within `INDICATOR_MARGIN_PX`, 8) and elsewhere in the picture, after the pixels that change with focus held (noise) and the masked area are left out, as for M7. These are facts for the judge, so it need not estimate from the pictures where a change sits ([research note](../research/2026-11-07-visual-judgment-and-apijudge.md), section 1); no row reads them. Fixture F16: a faint colour change on the link and a counter beside it.

**Output:** `{indicator: yes|no|unsure, change: "<a few plain words>"}`.

**Rubric.** Yes: an outline, border, underline, background or text color change, or an added icon or marker, on the element or touching it. No: no noticeable change; or the only change is elsewhere in the picture (a slideshow, a video, an animation); or only soft edge pixels around text. Unsure: a pop-up such as a tooltip appears beside the element and nothing on the element changes; or the change is too faint to tell. Mechanical guard: J1 is asked only when M7 measured at least `MIN_CHANGED_PX` changed pixels.

| Example | Answer |
| --- | --- |
| An underline appears under the link text | Yes: "an underline appears" |
| A small square appears just before the link (oj04fd Passed Example 4) | Yes: "a marker appears beside it" |
| The slide behind the link changed; the link looks the same | No |
| A tooltip appears beside the button; the button looks the same | Unsure |
| A 1 px very light gray outline on white | Unsure |

**Use:** M7 asks; M9, M10 and M11 consume the answer.

## 5. Edge cases

Only cases that need a rule of their own; everything else follows sections 2–3. V-numbers are browser checks in [_browser-checks.md](_browser-checks.md#4d).

| Case | Rule | Verify |
| --- | --- | --- |
| Stops inside frames, same- or cross-origin | Tested like any stop; the walk's box is already in top-level coordinates, and the top-level clip shows the frame's content. Only the frame element itself is exempt (M2) | V4, V5 |
| Stops larger than the viewport | The region is clipped to the viewport; both images use the same clipped part | V6 |
| Stops past a keyboard trap | Reached by P2 where possible. Reached only through 4.C's bypass: M4. Between two different traps and never reached: G3 | — |
| Widget items (roving tabindex or aria-activedescendant) | Tested through widget pass W, with the same rows | V10 |
| Element that drops focus as soon as it gets it (F55) | M3; 4.E fails it too (its M7) | V9 |
| Indicator that disappears after a few seconds | Not tested: a known limit (Abby, 2026-10-31). Understanding 2.4.7 says the indicator must not be time limited; the PDF is silent, and the images are taken within about 2 s of focus | — |

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5: the matching row (M8 or M10, in the evidence trace only); location (page URL, frame chain, CSS path, role and accessible name); steps to reproduce from a fresh load ("Tab 7 times"); the on and off images side by side with the changed-pixel image, the box outlined on copies only; every focus style read in both states; J1's answer if asked; and the tool versions the plan requires.

**Continuing past a failure.** The PDF gives no stop rule for 4.D, and ER 1 covers each element, so every stop is evaluated and each failing stop is its own instance.
