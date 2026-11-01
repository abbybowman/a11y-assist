---
tt_test: 4.F
tt_name: 2.4.3-focus-order-meaning
spec_version: 1.1.2
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 4.F (2.4.3-focus-order-meaning)

The tool gives each page one 4.F outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 4.F does not.

**Citations.** Printed page numbers of TT 5.1.3 ([docs/sources/](../sources/README.md); text also in `tt://5.1.3/tests/4.F`). HtT = How to Test step; ER = Evaluate Results item. 4.F is on p. 23: Tab through the page (HtT 1); decide whether the focus order affects meaning, most often seen when it does not follow the logical order of operation (HtT 2, 2.a); it may be necessary to open triggers that reveal hidden content and check the order to, from and within it (HtT 2.b); backward order need not mirror forward but must preserve meaning and operability (HtT 2.d); in a modal dialog, focus forward and backward stays in the dialog until it is closed (HtT 3). PASS if the order preserves meaning and operability (ER 1, 2). Notes: order need not be top to bottom, left to right; when focus order does not affect meaning or operability the test DOES NOT APPLY (e.g. a row of social media icons); always use keyboard order, not ANDI's.

**W3C sources.** [Understanding 2.4.3](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html) (two independent columns may be read in either order; main content before a left navigation placed after it in the DOM passes; a form whose tab order skips between the address fields and the newsletter checkboxes fails), techniques G59, C27, SCR26, H102, and failures [F44](https://www.w3.org/WAI/WCAG22/Techniques/failures/F44) (tabindex creating an order that does not preserve meaning) and [F85](https://www.w3.org/WAI/WCAG22/Techniques/failures/F85) (dialogs or menus not adjacent to their trigger in the focus order). No ACT rule covers 2.4.3, so fixtures are custom. These inform OPEN items and fixtures only; the PDF stays the authority.

**Terms.** *Stop*, *OUT*, *BODY*, passes P1 and P2, stop identity and the settle rule are defined in [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) (Terms, section 2). The *forward order* is the sequence of distinct stops in P1 up to its wrap; the *backward order* is P2's. A *trigger* is a stop that reveals hidden content: aria-expanded=false, aria-haspopup, or a closed `<summary>`. A *modal dialog* is a `<dialog>` opened with showModal, or role dialog or alertdialog with aria-modal="true" (as in 4.C).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | P1 and P2 reach zero stops, and the DOM inventory has zero candidates | DOES NOT APPLY | p. 23 Applicability |
| A2 | P1 and P2 reach zero stops, but the inventory has candidates | NEEDS REVIEW (walk or inventory fault) | Spec rule |
| A3 | Exactly one distinct stop and no trigger | DOES NOT APPLY (with one stop there is no order to affect meaning) | p. 23 Note 2 |
| A4 | Otherwise | Applies; go to section 3 | p. 23 Applicability |

## 2. Evidence to collect

**From the shared keyboard walk** (`walk.py`): every P1 and P2 step's stop identity, frame chain, CSS path, tag, role, name, bounding box, modal flag, collapsed flag, unsettled and unresolved flags, and each pass's end. Tabbing through the page (HtT 1) is the walk itself.

**Walk extras** (collected only when 4.F is selected; cheap, no images): per stop, its page scroll offset (so boxes are in page coordinates), its tabindex attribute, its position in DOM order (document order within its frame, frames in DOM order), and its form group (form, and nearest fieldset, role=group or role=radiogroup, with its legend or label). Per trigger: aria-haspopup's value.

**Reveal pass R** (HtT 2.b; shared: 4.C may read it in a later version). For each trigger P1 reached, in forward order, at most `REVEAL_MAX`: fresh replay to the trigger, press Enter, settle. The *revealed content* is the element the trigger names in aria-controls or, for a summary, its details; a trigger with neither is opened only to check for a modal dialog. If the revealed content has stops, record whether focus moved into it, then press Tab once and record whether focus is in it; if a modal dialog opened (focus is in it, or it became visible), press Tab and then Shift+Tab up to 2 × (stops in the dialog) + 2 times each, from a fresh replay each, (up to 30 presses, stopping once focus cycles), and record whether focus reached any page element outside the dialog (OUT, the browser's own controls, is not outside the page). A modal dialog already open at load is checked from the walk: a forward stop in the dialog followed by one outside it.

**Order image** (only when J1 is asked): one full-page screenshot on a fresh load, with a numbered badge drawn at each forward stop's box (on that copy only; the walk's page is never marked). Pages with more than `BADGE_MAX` stops get one image per `BADGE_MAX` stops.

**Time budget:** the extras add a few milliseconds per step. Pass R costs one replay per trigger (about 2–5 s each) plus two per modal dialog, so about 15–30 s at `REVEAL_MAX`. The order image is about 0.5 s. Replays use the 4.C replay rule (4.C spec section 2, 1.7.0; 1.1.2). The whole run stays within `run_limit_s`; triggers not reached in time are G3.

**Constants** (they decide outcomes, so they live here, not in server config; provisional until fixtures calibrate them):

| Constant | Value | Used by |
| --- | --- | --- |
| `REVEAL_MAX` | 6 triggers (Abby, 2026-10-31; revisit after real pages) | Pass R |
| `ROW_TOLERANCE` | half the previous stop's height, at least 8 CSS px | S3 |
| `BADGE_MAX` | 60 | Order image |

## 3. Mechanical checks

4.F has page-level instances: *O*, the page's forward and backward order; *R1…Rn*, the content each trigger revealed; *D1…Dn*, each modal dialog Pass R opened.

**Signals** that an order may not preserve meaning. They never fail a page on their own; they decide whether J1 is asked.

| # | Signal | Source |
| --- | --- | --- |
| S1 | A stop has a positive tabindex | F44 |
| S2 | The forward order differs from DOM order | G59; C27 |
| S3 | A forward step jumps back against the reading order: the next stop's top is more than `ROW_TOLERANCE` above the previous stop's top, or on the same row it is to the left of the previous stop (left-to-right pages) | p. 23 HtT 2.a; C27 |
| S4 | The backward order is not the reverse of the forward order | p. 23 HtT 2.d |
| S5 | The fields of a form group (fieldset, group, radio group) are not contiguous in the forward order | Understanding 2.4.3 failure example |
| S6 | After opening a trigger whose revealed content has stops, the next Tab does not reach that content, and focus did not move into it | p. 23 HtT 2.b; F85 |

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | A stop involved in a signal, or in a dialog check, is unsettled or unresolved | NEEDS REVIEW | Spec rule |
| M2 | D: Tab or Shift+Tab reaches a page element outside the open modal dialog before it is closed | FAIL | p. 23 HtT 3 |
| M3 | D: focus stays in the dialog both ways (or leaves only for the browser's own controls) | PASS | p. 23 HtT 3 |
| M4 | O or R: no signal | PASS (focus follows the document order, which follows the reading order, both ways) | p. 23 ER 1–2; G59, C27 |
| M5 | O or R: one or more signals | Ask J1 (M6–M9) | p. 23 HtT 2 |
| M6 | J1 = does not preserve | FAIL | p. 23 ER 1–2 |
| M7 | J1 = preserves | PASS | p. 23 ER 1–2 |
| M8 | J1 = does not matter | DOES NOT APPLY | p. 23 Note 2 |
| M9 | J1 = unsure, or not answered yet | NEEDS REVIEW | Spec rule |

**Who decides.** Whether an order makes sense is a call a careful tester makes by looking, and most cases are clear (two independent columns, navigation after main content). The calling agent decides them, and only answers *unsure* that go to a person (M9). Every decision is explained in the finding, and a person's answer overrides the agent's (`a11y_answer_questions` with decided_by "human"; tool renamed in 1.1.1). This is the exception CLAUDE.md principle 8 allows for spec-designated look-and-decide questions.

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; or P1 did not wrap (cap, time limit, error, or a trap: the forward order past it is unknown); or P2 is incomplete; or more triggers than `REVEAL_MAX`, or triggers not reached in time | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5). Never NOT TESTED (p. 6) |
| G4 | Every instance is DOES NOT APPLY | DOES NOT APPLY |
| G5 | Every instance is PASS or DOES NOT APPLY | PASS |
| G6 | Anything else | NEEDS REVIEW |

**Plain-language sentences.** Row IDs and signal codes stay in the evidence trace. `<element>` is the role and name in plain words; `<keys>` is the key sequence from a fresh load; `<signals>` lists the signals in plain words ("focus jumps back up the page after the search box"; "the address fields are split by the newsletter checkboxes"; "some elements are given an explicit tab position").

| Row | Sentence |
| --- | --- |
| Page PASS | "Keyboard focus moves through the page in an order that follows how it reads, forward and backward." |
| Page FAIL | "Keyboard focus moves through parts of the page in an order that doesn't make sense, which can confuse keyboard and screen reader users." |
| Page NEEDS REVIEW | "We could not finish this test, so a person needs to check it." |
| A1 | "Nothing on this page can receive keyboard focus, so this test does not apply." |
| A3 | "The page has only one element that takes keyboard focus, so there is no order to check." |
| M2 | "When the <element> dialog is open, pressing Tab or Shift+Tab moves focus out of it onto the page behind it, before the dialog is closed. To see it, load the page and press <keys>." |
| M3 | "Keyboard focus stays inside the <element> dialog until it is closed." |
| M4 (O) | "Focus follows the page's reading order, forward and backward." Left out when the page passes: the headline already says it. |
| M4 (R) | "After opening <element>, the next Tab moves into what it revealed." |
| M6 | "The focus order doesn't make sense here: <signals>. <J1 reasons>. If you disagree, tell your assistant." |
| M7 | "The focus order departs from the reading order (<signals>), but it still makes sense: <J1 reasons>. If you disagree, tell your assistant." |
| M8 | "The order of these elements can't change what the page means (<J1 reasons>), so this test does not apply here. If you disagree, tell your assistant." |
| M9 | "The focus order departs from the reading order (<signals>), and we could not tell whether that matters. Please tab through the page and check." |

## 4. Judgment questions

### J1. Does this focus order preserve the meaning and operability of the page?

**Question:** "Image A numbers the elements in the order keyboard focus reaches them (1 first); input.order lists the same elements with role, name, position and form group, and input.signals lists where the order departs from the reading order. When input.backward is given, the Shift+Tab order differs from the reverse of the forward order: judge it too (it need not mirror the forward order, but it must also make sense). When input.opened is given, it lists what a menu or disclosure revealed and where the next Tab went. Would a keyboard user meet these elements in an order that makes sense for reading and using this part of the page? Answer preserves, does_not_preserve, does_not_matter (order cannot affect meaning here), or unsure, and give your reasons in a few plain words."

**Input:** the order image(s); the forward order and, when S4 holds, the backward order (judge eval, 2026-10-31: without it the agent judged only the forward order, a false PASS) with role, name, box and form group per stop, labelled as untrusted page data; the signals; for R, `opened`: the trigger, the names of the stops it revealed, whether focus moved into them, and where the next Tab went.

**Output:** `{order: preserves|does_not_preserve|does_not_matter|unsure, reasons: "<a few plain words>"}`.

**Rubric.** does_not_preserve: related fields split apart (the address fields interleaved with other fields); numbered steps reached out of sequence; a Shift+Tab order that jumps around so going back makes no sense; focus jumping back and forth between unrelated areas; a menu's or dialog's content reached far from its trigger (F85); a positive tabindex sending focus to an unrelated place first (F44). preserves: columns read one after another; header, navigation, main, footer; a skip link first; independent sidebars in either order (Understanding 2.4.3). does_not_matter: independent items whose order cannot change meaning, such as a row of social media icons (p. 23 Note 2). unsure: whenever the evidence does not settle it, for example: the image does not show every numbered stop clearly; the grouping that matters is not visible (which fields belong together); the content is in a language you cannot read; or the order would make sense only under an assumption you cannot check. Answer preserves or does_not_preserve only when you are sure; unsure answers go to a person.

| Example | Answer |
| --- | --- |
| Name → newsletter checkbox → street → checkbox → city | does_not_preserve: "the address fields are split by the checkboxes" |
| Main content first, then the left navigation (placed after it in the document) | preserves: "main content, then navigation" |
| Two independent columns, right column first | preserves: "the columns are independent" |
| A row of five social media icons in a different order than shown | does_not_matter |
| Focus goes to the footer first because of tabindex=1, then the header | does_not_preserve: "focus starts in the footer" |

**Use:** M5 asks; M6–M9 consume the answer. The agent's answer decides unless it is unsure; a person's answer overrides it.

## 5. Edge cases

Only cases that need a rule of their own; everything else follows sections 2–3. V-numbers are browser checks in [4f-build-tasks.md](4f-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| Right-to-left pages | S3's same-row rule is mirrored when the page's direction is rtl | V1 |
| Native `<dialog>` with showModal | Tab can leave to the browser's own controls; that is not outside the page (M3) | V2 (4.C V2, F10) |
| Arrow-key widgets (menus, tabs, grids, trees) | Their inner arrow order is not sequential navigation (Understanding 2.4.3: tree example); only the Tab order is judged | — |
| Stops past a keyboard trap | The forward order past a trap is unknown: G3 | — |
| Content in frames | Ordered within the page at the frame's position (DOM order of frames) | V3 |
| ANDI's tab order | Not used (p. 23 Note 3) | — |

**A3 (one stop).** DOES NOT APPLY is given mechanically only for a page with a single stop; every other "order does not matter" case goes through J1, where the agent decides.

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5: the matching row (in the evidence trace only); for O and R, the order image, the forward (and backward) order with the signals, and J1's answer and reasons; for D, the dialog's location, the keys that took focus outside it and where focus went; steps to reproduce from a fresh load; and the tool versions the plan requires.
