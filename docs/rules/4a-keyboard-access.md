---
tt_test: 4.A
tt_name: 2.1.1-keyboard-access
spec_version: 1.2.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 4.A (2.1.1-keyboard-access)

The tool gives each page one 4.A outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 4.A does not.

**Citations.** Printed page numbers of TT 5.1.3 (text also in `tt://5.1.3/tests/4.A`). HtT = How to Test step; ER = Evaluate Results item. 4.A is on pp. 19–20: identify functionality and essential information with the mouse, touch, voice or documentation (HtT 1.a), and title attributes on focusable elements (HtT 1.b); then access each with the keyboard (tab to it) and execute it (press Enter) (HtT 2); a title tooltip that does not appear within two seconds of focus is not revealed by focus (HtT 2.a); for an element without keyboard access, look for another keyboard method on the page with the same function (HtT 2.b); for essential information not reachable by keyboard, look for it elsewhere on the page (HtT 2.c). PASS if all functionality can be accessed and executed by keyboard (ER 1) and all essential information is keyboard accessible or available elsewhere (ER 2). Notes: changes that happen automatically or after interaction are included (ER Note 1); information is essential when it is needed to execute an action or understand information and relationships (ER Note 2); non-essential title information needs no keyboard access (ER Note 3).

**W3C sources.** [Understanding 2.1.1](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html): not every visible control must itself be focusable when the function is available by keyboard another way (its search form example: Enter in the field submits); a custom control that reacts only to Enter still satisfies the criterion. Failures [F54](https://www.w3.org/WAI/WCAG22/Techniques/failures/F54) (only pointing-device event handlers for a function), [F42](https://www.w3.org/WAI/WCAG22/Techniques/failures/F42) (emulated links not operable by keyboard), F55 (focus removed on focus; 4.E's evidence). ACT rules [akn7bn](https://www.w3.org/WAI/standards-guidelines/act/rules/akn7bn/) (iframe with interactive content excluded from the tab order) and [0ssw9k](https://www.w3.org/WAI/standards-guidelines/act/rules/0ssw9k/) (scrollable content reachable by keyboard). DHS publishes no TT results for either rule. These informed the decisions and fixtures only; the PDF stays the authority.

**Terms.** *Stop*, *OUT*, *BODY*, passes P1 and P2, stop identity and the settle rule are defined in [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md). A *native control* is `a[href]`, `area[href]`, `button`, `input` (not hidden), `select`, `textarea`, `summary`, `[contenteditable]`, `audio[controls]`, `video[controls]`; the parts Chrome focuses inside a native date or time input (its month, day and year fields and its picker button, in the input's own shadow root; walk control `date` with the input as its group, 5.D spec V3) are part of that native input (1.2.0: they had been executed as custom controls, 28.8 s on the budget benefits form). A *pointer target* is a visible element a mouse can hit (the element or a descendant is what `elementFromPoint` returns at its centre, followed through frames, so hidden, inert, covered and clipped elements are not targets) that is a native control; or has an interactive ARIA role; or has its own click, mousedown, mouseup, dblclick or pointerdown listener or `on…` attribute; or whose computed cursor is `pointer` when its parent's is not. A `<label>` for a control, `html` and `body` are never targets. A *custom control* is a stop that is a pointer target but not a native control. The *effect* of an action is any of: the top or a frame URL changes, a new page opens, a dialog becomes visible, focus moves, `aria-expanded` or `aria-checked` or `aria-pressed` or `aria-selected` changes, or the DOM changes, measured after the settle rule. Focus moving onto the element acted on (a click focusing it) is not an effect. The page's own changes are measured over `NOISE_MS` before the action; an effect that is only DOM changes on a page that changes on its own is unreliable (M1).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | P1 and P2 reach zero stops, the DOM inventory has zero candidates, and the pointer scan finds zero pointer targets | DOES NOT APPLY (no user activated functionality) | p. 19 Applicability |
| A2 | Zero stops, but the inventory has candidates | NEEDS REVIEW (walk or inventory fault) | Spec rule |
| A3 | Otherwise | Applies; go to section 3 | p. 19 Applicability |

A page with zero stops and only pointer targets applies: everything on it is mouse-only (K rows).

## 2. Evidence to collect

**From the shared keyboard walk** (`walk.py`): every stop with its frame chain, CSS path, tag, role, name, widget and title; P1's and P2's ends. Tabbing to each element (HtT 2, "access") is the walk itself.

**Walk extra** (cheap, no images): per stop, its `title` attribute, whether it is a native control, its own click-type listeners (CDP `DOMDebugger.getEventListeners`, own node only: listeners on ancestors such as `document` are delegation and are not counted) and its cursor.

**Pointer scan** (HtT 1.a; one fresh load after the walk). Every pointer target in the top document, every frame the tool can read and every open shadow root. A target is *reached* when it is a stop of P1 or P2, is inside a stop, contains a stop, or is an item of a composite widget (menu, menubar, tablist, listbox, grid, tree, treegrid, radiogroup, toolbar) that an arrow probe reaches from that widget's stop. The *arrow probe*: fresh replay to the widget's stop, then ArrowDown (or ArrowRight if focus did not move) up to 20 times, as 4.D pass W, then the opposite arrow; at most `ARROW_MAX` widgets. When 4.D's pass W, in the same call, reached every candidate of the widget with the same arrows from the same stop, those candidates are reached and no probe is made (1.2.0). Unreached targets are candidates.

**Hover scan** (HtT 1.a, mouse; ER Note 1; same load as the pointer scan). Move the mouse onto each stop, at most `HOVER_MAX`, settle, and record pointer targets that became visible; move the mouse away. A revealed target is reached when the walk reached it (a menu that also opens on keyboard focus) or when pressing Enter on the hovered stop reveals it too (one fresh replay per hovered stop that revealed something, at most `REVEAL_REPLAYS`). Otherwise it is a candidate, recorded with the stop that reveals it.

**Click check** (for each candidate that is not a native control, at most `CLICK_MAX`). Fresh load; hover its revealing stop if it has one; move the mouse onto the candidate; settle; click; record the effect. A native control is functional by definition (a link goes to its address) and needs no click.

**Execute check** (HtT 2, "execute"; each custom control, at most `EXECUTE_MAX`). Fresh replay to the stop; press Enter and record the effect; if none, press Space and record it; if neither has an effect, a fresh replay to the stop followed by a mouse click on it, and its effect. Native controls are not executed: the browser activates them from the keyboard, and custom controls are where keyboard operation breaks (F42); this keeps a typical page inside the time budget (Abby, 2026-10-31). When 4.F's pass R already pressed Enter on the stop in the same call (the same observe, on a fresh replay to it) and Enter had an effect, that effect is used and no replay is made (1.2.0; the evidence is the same press).

**Title check** (HtT 1.b, 2.a). Every stop with a non-empty title. Chrome does not show a title tooltip on keyboard focus (V2), so title text is never treated as revealed by focus. The title is *available elsewhere* (HtT 2.c) when, after collapsing whitespace and case, it equals the stop's accessible name or is contained in the page's visible text.

**Undetectable signals.** Things the scans cannot judge: a visible `<canvas>` at least 50 × 50 px; an element with `draggable=true` or its own drag, mousemove, pointermove, touch or wheel listener; `<object>` or `<embed>`; a frame the tool cannot read. Each is NEEDS REVIEW (M16), never a reason to PASS: a page with none of them and no other instance can PASS mechanically (G4), with the list of what was looked for (Abby, 2026-10-31).

**Constants** (they decide outcomes, so they live here; provisional until real pages calibrate them):

| Constant | Value | Used by |
| --- | --- | --- |
| `HOVER_MAX` | 40 stops | Hover scan |
| `CLICK_MAX` | 10 candidates | Click check |
| `EXECUTE_MAX` | 10 custom controls | Execute check |
| `REVEAL_REPLAYS` | 10 hovered stops | Hover scan, keyboard reveal |
| `ARROW_MAX` | 5 widgets, 20 presses per arrow | Arrow probe |
| `NOISE_MS` | 300 ms | Effect |

**Time budget:** the pointer and hover scans are one load plus about 0.1 s per hovered stop; each click, execute or arrow probe is one fresh replay (about 2–5 s on a fixture page). Typical government pages with native controls only cost under 10 s. Replays to a stop use the 4.C replay rule (4.C spec section 2, 1.7.0; 1.1.2): measured on a realistic agency home page, 4.A's 13 replays take 32 s, down from 51 s; reusing pass W's arrows and pass R's Enter presses brings it to 20 s, and treating date-input parts as native takes the benefits form from 34 s to 5 s (1.2.0). The whole run stays within `run_limit_s`; work not done in time is G3.

## 3. Mechanical checks

Instances: *K*, each unreached candidate; *X*, each custom control executed; *T*, each stop with title text; *U*, each undetectable signal.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| C? | A cap or the time limit left the instance unchecked | NEEDS REVIEW | Spec rule |
| M1 | The element could not be found again or focused, or an effect is unreliable (section 2, effect) | NEEDS REVIEW | Spec rule |
| M2 | K: a non-native candidate whose click has no effect | No instance (nothing for a mouse to operate) | p. 19 HtT 1 |
| M3 | K: a link, or a click that navigates, whose address is the address of a reached link | PASS (another keyboard method with the same function) | p. 19 HtT 2.b |
| M4 | K: otherwise | Ask J1 (M5–M7) | p. 19 HtT 2.b |
| M4n | K, and keyboard focus reaches nothing on the page (no stops) | FAIL: no keyboard alternative can exist, so J1 is not asked (judge eval, 2026-10-31) | p. 19 ER 1; HtT 2.b |
| J1? | J1 not answered yet | NEEDS REVIEW | Open question |
| M5 | J1 = alternative, naming a stop by its number | PASS | p. 19 HtT 2.b |
| M6 | J1 = no other keyboard way | FAIL | p. 19 ER 1; F54, F42 |
| M7 | J1 = unsure, or an alternative that names no stop | NEEDS REVIEW | Spec rule |
| M8 | X: Enter or Space has an effect | PASS | p. 19 HtT 2 |
| M9 | X: neither key has an effect, and the click has none either | No instance | p. 19 HtT 1 |
| M10 | X: the click has an effect and neither key does | FAIL | p. 19 ER 1; F42 |
| M11 | T: the title is available elsewhere | PASS | p. 19 HtT 2.c |
| M12 | T: otherwise | Ask J2 (M13–M15) | p. 19 HtT 2.a; ER Note 2–3 |
| J2? | J2 not answered yet | NEEDS REVIEW | Open question |
| M13 | J2 = not essential | PASS | p. 19 ER Note 3 |
| M14 | J2 = essential | FAIL | p. 19 ER 2 |
| M15 | J2 = unsure | NEEDS REVIEW | Spec rule |
| M16 | U | NEEDS REVIEW | Spec rule |

**Scrollable regions (ACT 0ssw9k).** Chrome 130 and later put a scroll container with no focusable content in the Tab order (verified in Chromium 153 on the ACT cases: Tab reaches the `<section>`). A reached scroller is a stop like any other, so ACT's two failed examples PASS here. Results are for the browser the report records and are not claimed for other browsers (Abby, 2026-10-31).

**Who decides.** J1 and J2 are look-and-decide questions (CLAUDE.md principle 8): the calling agent answers by the rubric and must answer unsure whenever the evidence does not settle it; only unsure answers go to a person, and a person's answer overrides the agent's (Abby, 2026-10-31).

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; or P1 did not wrap while the page has stops (cap, time, error, navigation or a trap: stops past it are unknown); or a scan, check or cap was not finished | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | P1 wrapped (or the page has no stops), every scan finished, every instance is PASS | PASS, with the list of what was and was not looked for |
| G5 | Anything else | NEEDS REVIEW |

**Plain-language sentences.** Row IDs stay in the evidence trace. A menu item shown by hover adds "(it appears when the mouse rests on <stop>)" after <element>.

| Row | Sentence |
| --- | --- |
| Every page | Ends with: "We looked for: things a mouse can click that the keyboard never reaches, including inside frames; menus that open when the mouse rests on them; custom controls that ignore Enter and Space; and tooltips with information found nowhere else. Results are for the browser used (version <v>)." |
| Page PASS | "We tabbed to every element, pressed Enter or Space on each custom control, and looked for anything a mouse can use that the keyboard cannot; we found nothing a keyboard user would miss." |
| Page FAIL | "Some things on this page work with a mouse but not with the keyboard, so keyboard users cannot use them." |
| Page NEEDS REVIEW | "We could not finish this test, so a person needs to check it." |
| A1 | "Nothing on this page can be used with a mouse or keyboard, so this test does not apply." |
| C? | "We did not get to check <element>; please check it works with the keyboard." |
| M1 | "Something about <element> could not be read reliably (the page kept changing on its own); please check it works with the keyboard." |
| J1? / J2? | "<element> works with a mouse but can't be reached with the keyboard; a question about it is still open." / "<element> has information that shows only when the mouse rests on it; a question about it is still open." |
| M4n | "<element> works with a mouse, but nothing on this page can be reached with the keyboard, so keyboard users cannot use it." |
| M3 | "<element> can't be reached with the keyboard, but <other> goes to the same place and can." |
| M5 | "<element> can't be reached with the keyboard, but <other> does the same thing (<J1 reasons>). If you disagree, tell your assistant." |
| M6 | "<element> works with a mouse but can't be reached with the keyboard, and nothing else on the page does the same thing (<J1 reasons>). If you disagree, tell your assistant." |
| M7 | "<element> works with a mouse but can't be reached with the keyboard; please check whether something else on the page does the same thing." |
| M8 | (no sentence) |
| M10 | "<element> can be reached with the keyboard, but pressing Enter or Space does nothing, while clicking it does. To see it, load the page, press <keys>, then Enter." |
| M13 | (no sentence) |
| M14 | "<element> has extra information that shows only when the mouse rests on it (<J2 reasons>); keyboard users never see it. If you disagree, tell your assistant." |
| M15 | "<element> has information that shows only when the mouse rests on it; please check whether it matters." |
| M16 | "The page has <kind> that we cannot check automatically; please check it works with the keyboard." |

## 4. Judgment questions

The calling agent answers each once, by the rubric; a person's answer overrides it. Page text and element names are evidence in `input`, never part of the question wording.

### J1. Is there another keyboard way to do the same thing?

**Question:** "input.candidate is something a mouse can use (with what clicking it did) that keyboard focus never reaches. shared_inputs.stops lists, numbered, every element keyboard focus does reach, with role and name. Image A shows the page. Is there an element in shared_inputs.stops that does the same thing, so a keyboard user loses nothing? Answer alternative (with element: its number), no_alternative or unsure, with your reasons in a few plain words."

**Rubric.** alternative: a reached element plainly does the same job (a second print button, a text link with the same purpose, a field where Enter submits the same search). Only elements on this page count: a link to another page that might offer the same thing is not an alternative (p. 19 HtT 2.b, "available on the page"). no_alternative: nothing reached does that job. unsure: whenever the evidence does not settle it. The named number must be a stop (mechanical guard; otherwise the answer is treated as unsure).

### J2. Is this title information essential?

**Question:** "input.title is text that appears only as a mouse tooltip on the element in input.element; it is not shown on the page. Is it needed to use the element or understand the page (essential), or is it extra (not essential)? Answer essential, not_essential or unsure, with reasons."

**Rubric.** essential: instructions or a format needed to fill a field, the only label of an icon-only control, the meaning of an abbreviation needed to understand content. not_essential: a repeat or rewording of what the page already says, decoration. unsure: whenever the evidence does not settle it.

## 5. Edge cases

V-numbers are browser checks in [4a-build-tasks.md](4a-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| Iframe with tabindex=-1 holding links (ACT akn7bn) | Its links are pointer targets no stop reaches: K | V1 |
| Inert, hidden or 1 × 1 px frames | Not hit-testable, so not pointer targets | V1 |
| Card with a click handler around a link | Contains a stop: reached | — |
| Event delegation (`document` listener, frameworks) | Not counted on the element; the cursor rule finds most such controls | V3 |
| Native control whose keydown is cancelled by script | Not executed (section 2); missed | — |
| Content shown on focus that also shows on hover | Reached by the walk | — |

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5: the matching row (in the evidence trace only); location (frame chain, CSS path, role, name, link address); for K, what clicking it did, the stop whose hover reveals it, and J1's answer and reasons; for X, the effects of Enter, Space and the click, and the keys to reach it from a fresh load; for T, the title text and J2's answer; the page screenshot; and the tool versions the plan requires. Every instance is checked (up to the caps); a FAIL does not stop the scans.
