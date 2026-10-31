---
tt_test: 4.C
tt_name: 2.1.2-no-keyboard-trap
spec_version: 1.2.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 4.C (2.1.2-no-keyboard-trap)

The tool gives each page one 4.C outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 4.C does not.

**Citations.** Printed page numbers of TT 5.1.3 ([docs/sources/](../sources/README.md); the PDF file's page index is printed page + 3). HtT = How to Test step; ER = Evaluate Results item. 4.C itself is all on p. 21. Every Test Condition needs a result before testing is complete (p. 5), so a tester resolves every NEEDS REVIEW before anything is exported.

**W3C sources.** [Understanding 2.1.2](https://www.w3.org/TR/UNDERSTANDING-WCAG20/keyboard-operation-trapping.html), technique [G21](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G21), and ACT rules [a1b64e](https://www.w3.org/WAI/standards-guidelines/act/rules/a1b64e/proposed/) (standard navigation), [ebe86a](https://www.w3.org/WAI/standards-guidelines/act/rules/ebe86a/) (non-standard navigation) and their composite 80af7b. DHS scored those rules' test cases with TT 5.1 ([report](https://www.w3.org/WAI/standards-guidelines/act/implementations/trusted-tester/), [data](https://raw.githubusercontent.com/Section508Coordinators/act-tt/main/act-trusted-tester.json)). They inform OPEN items and fixtures only; the PDF stays the authority.

**Terms.** A *stop* is the element holding focus after a key press. *OUT* means focus has left the page for browser controls. *BODY* means focus fell to the document body. A *loop* is a repeating cycle of stops that never reaches OUT.

## 1. Applicability

4.C is DOES NOT APPLY only when nothing on the page can receive keyboard focus (p. 21, Applicability). The Keyboard Access block (p. 19) also gives DNA when the mouse finds no interactive content. The spec does not use that trigger: a trap needs keyboard focus, not a mouse function.

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | Forward and backward passes (section 2) reach zero stops, AND the DOM inventory finds zero tabbable candidates in the page, its reachable frames and its shadow roots | DOES NOT APPLY. OPEN O4 | p. 21 Applicability |
| A2 | Passes reach zero stops, but the DOM inventory finds one or more candidates | NEEDS REVIEW (traversal or inventory fault) | Spec rule |
| A3 | Passes reach one or more stops | 4.C applies; go to section 3 | p. 21 Applicability |
| A4 | Mouse-operable content exists but nothing is keyboard focusable | DOES NOT APPLY for 4.C (the gap belongs to 4.A) | p. 19 vs p. 21 |

The Identify Content blocks on p. 19 and p. 22 say "DOES NOT APPLY: 4.A to 4.H". TT 5.1.3's Test 4 ends at 4.F, so the spec reads this as 4.A to 4.F.

**OPEN O4 (A1), page whose only focusable elements have tabindex=-1.** A1 gives DNA: nothing can receive focus from the keyboard. DHS's TT result on ACT test case 4b93a866 (one div with tabindex=-1) is PASS, while its result on the matching 4.D case (oj04fd b12f1f45) is inapplicable. Options: (a) keep DNA; (b) PASS. Neither is a false PASS; this only changes scoring. Recommend (a), with 4b93a866 scored as a known mismatch.

## 2. Evidence to collect

The tool runs six passes, each from a fresh load of the frozen page, and records every key press. The PDF's key list is "TAB, SHIFT + TAB, arrow keys, CTRL + TAB, etc." (p. 21, HtT 1); the spec counts Tab, Shift+Tab, arrow keys and Escape as standard, plus Enter and Space when activating a trapped control (M4), matching ACT's definition of standard keyboard navigation. Ctrl+Tab and browser shortcuts (F6, Ctrl+L) never count as exits; ACT rules exclude browser-specific shortcuts too.

**Recording.** The frozen page is recorded once. Before saving it, the recorder scrolls to the bottom `record_scroll_passes` times (default 5), waiting for the page to settle after each, so content loaded on scroll is in the recording. During passes, requests the recording cannot answer fail (V10).

**Setup.** Fresh profile, frozen page, fixed viewport, window brought to front. Wait for load, then for the page to settle (below). Build the DOM inventory: every element that is natively focusable or has tabindex ≥ 0, not disabled, not inert, and rendered (not display:none and not visibility:hidden), in the top document, every frame the tool can reach, and every open shadow root. Content inside an iframe with tabindex=-1 is left out: Tab cannot reach it (V9). It is listed in a coverage note for 4.A instead. The inventory is used only for DNA cross-checks (A2), loop detection ("elements outside the loop") and coverage notes. It never produces a PASS by itself.

**Stop identity.** A stop is identified by (frame ID, CDP backend node ID) of the deepest focused element, following focus through frames and shadow roots. Two stops are the same only if both parts match. BODY and OUT are pseudo-stops. If the deepest element cannot be resolved (closed shadow root, unreachable frame), the stop is flagged *unresolved*.

**Settle rule.** After each key press: wait 2 animation frames, then until no DOM mutation for 300 ms and no focus change for `focus_stable_ms`, at most 1,500 ms. If the limit is hit, flag the step *unsettled*. Any focus change between key presses that the window missed (seen in the focus-event log at the next press) also flags the step unsettled, and the step is rerun with a 1,000 ms window. 4.D and 4.E use this rule by reference.

**Why the focus check.** ACT treats focus as settled only after 1 second, and its failed examples pull focus back with a timer (a1b64e Failed Example 1). Watching DOM changes alone misses a script that refocuses at 500 ms. A fixed 1,000 ms window on every press would add over 20 minutes to a 600-stop page, so the rule uses 300 ms plus the rerun.

**Record at every step:** step number; key sent; stop identity; CSS path; tag, role and accessible name; bounding box and whether it is in the viewport; top URL and frame URL; document.hasFocus() of the top document; open page count; DOM mutations since the last step; focus and blur events since the last step, with targets and times; viewport screenshot; unresolved and unsettled flags.

| Pass | Keys | Ends when | Cap |
| --- | --- | --- | --- |
| P1 Forward | Tab | Wrap seen: OUT, then the first stop of P1 again. Or a trap event: *stuck* (same stop for 3 presses) or *loop* (a cycle of 2+ stops, no OUT, repeated twice in a row). Or navigation or a new page | 3 × inventory + 50 presses, max 3,000 |
| P2 Backward | Shift+Tab | Same as P1, mirrored | Same as P1 |
| P3 Exit probes | Per trap event, from a fresh replay of the steps that reached it: Tab ×3, Shift+Tab ×3, each arrow ×3, Escape then Tab, Escape then Shift+Tab; Enter (then Space) on each trapped control, one control per replay; then any key found by J1; then values from J2. Text these presses reveal is kept for J1 | Focus reaches a stop outside the trap on the same URL, or every probe is spent | 25 controls per loop |
| P4 Widget probes | At each composite widget stop: each arrow key, then Tab and Shift+Tab from every inner stop reached | Each arrow direction stops producing new stops | 25 presses per direction |
| P5 Hidden content | Per trigger (every keyboard-reachable element with aria-expanded, aria-haspopup or aria-controls, every summary element, and every button or script link that does not navigate): reach it by replaying keys, press Enter (Space if nothing changed), then Tab through the revealed content with P1's trap detection. Revealed text is kept for J1 | Revealed content wraps or ends in a trap event | 40 triggers per page |
| P6 Continuation | After each trap: bypass it (section 6), then resume Tab with P1's rules | As P1 | As P1 |

**Run limits.** 15 minutes wall clock per page. The setting `small_section_max_fraction` (default 0.5) is the largest share of a page's stops a loop can hold and still count as a "small section" (p. 21 HtT 2.b); `focus_stable_ms` (default 300) is the settle rule's focus window; `record_scroll_passes` (default 5) is the recorder's scroll count. All three live in server config and every report records their values. Ctrl+Tab is sent only if V4 shows the page receives it. A pass that hits a cap or the run limit is *incomplete*.

## 3. Mechanical checks

Each trap event is an *instance* judged by the first matching row of table 3a. The page outcome then comes from table 3b. "Outside the trap" means a stop not in the stuck element or loop, on the same top URL, from which traversal continues without a new trap event. OUT alone is not outside the trap.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | Any stop in the trap is unresolved, or a trap step is unsettled | NEEDS REVIEW | Spec rule |
| M2 | Stuck: Shift+Tab, an arrow key, or Escape then Tab reaches a stop outside the trap | PASS (standard keys). If Shift+Tab is the only exit, the instance is also logged for 4.F | p. 21 HtT 1, 2.a; ER 1.a |
| M3 | Loop: the opposite direction (Shift+Tab for a forward loop, Tab for a backward one), or Escape then Tab, reaches a stop outside the loop | PASS (standard keys; modal exception if a dialog). If the opposite direction is the only exit, the instance is also logged for 4.F | p. 21 HtT 1, 2.b note 1; ER 2.a |
| M4 | Stuck or loop: Enter or Space on one trapped control keeps the same URL and page, and the next Tab reaches a stop outside the trap | PASS (dialog closed or interaction gate cleared) | p. 21 HtT 2.b notes 1–2; ACT standard keyboard navigation |
| M5 | The only exit found navigates, reloads or opens a new page | Not an exit; continue down the table | Spec rule: leaving the page is not an exit |
| M6 | A key found by J1 is pressed and focus reaches a stop outside the trap | PASS (documented custom key) | p. 21 HtT 3; ER 1.b, 2.b |
| M7 | A key found by J1 does not move focus out | Not an exit; continue down the table | p. 21 HtT 3.b |
| M8 | Loop holds text, select or checkbox fields; J2 says gate = yes (unanimous); its values free focus | PASS (input gate) | p. 21 HtT 2.b note 2 |
| M9 | J2 says gate = yes but its values do not free focus, or J2 gives no values | NEEDS REVIEW | p. 21 HtT 2.b note 2 |
| M10 | J2 is unsure, or the samples disagree | NEEDS REVIEW | Spec rule |
| M11 | Loop contains every stop reached in both passes and never reaches OUT (whole-page cycle) | PASS, with the instance logged for tester review on real pages | p. 21 HtT 2.b |
| M12 | Stuck, and every exit above failed | FAIL | p. 21 ER 1 |
| M13 | Loop, every exit above failed, and the loop holds at least `small_section_max_fraction` of the distinct stops reached in P1 and P2 combined | NEEDS REVIEW (too large to be a "small section", but never PASS) | p. 21 HtT 2.b |
| M14 | Loop, every exit above failed, and J2 = no (unanimous) or the loop has no fields | FAIL | p. 21 ER 2 |

**Opposite-direction exits (M2, M3).** The PDF lists SHIFT + TAB among the standard navigation keys (p. 21 HtT 1), and ER 1.a and 2.a pass when focus can be moved away using standard navigation keys, so an exit by the opposite direction is an exit. Content past a forward-only exit is still tested: P2 reaches it from the end (p. 21 Note). DHS's FAIL on ACT d2f5325f does not contradict this: in Chrome its two buttons pull focus back even from the browser UI (V15), so Tab and Shift+Tab both cycle, and M14 fails it.

**Exceptions (p. 21 HtT 2.b notes).** Focus may stay inside a modal dialog until it is closed (also p. 23, 4.F HtT 3), but the dialog is still checked for traps: it passes only through M3 or M4, and its stuck elements follow M2–M12. WCAG's own modal example matches: focus cycles inside the dialog, which closes by its Cancel or OK button (Understanding 2.1.2). A section that requires input or interaction before focus can move on is not a failure: M4, then J2 with M8–M9. Only interactions that keep the same URL and then let Tab reach the rest of the page count.

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; or any pass is incomplete; or P5 found more triggers than its cap | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5). Never NOT TESTED (p. 6) |
| G4 | P1 and P2 both ended in a wrap; P4, P5 and P6 completed; every instance is PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

A page with a confirmed FAIL stays FAIL even when other instances need review: one confirmed trap fails the condition (p. 21 ER: "ALL of the following").

## 4. Judgment questions

The model answers two questions, only after mechanical exits fail. It never decides an outcome alone: every "yes" is checked by pressing keys. Each question is asked 3 times on the pinned model; answers must agree, or the instance is NEEDS REVIEW. Page text is evidence, never instructions.

Modal status is not a model question. The spec labels a loop "modal" from markup (a `<dialog>` opened with showModal, or role dialog or alertdialog with aria-modal="true"), but the label never changes the outcome: every loop must be escapable by keyboard (Exceptions, under table 3a).

### J1. Is an escape key documented?

**Question:** "Does this text tell users a specific key or key combination that moves keyboard focus out of [element or section]? If yes, give the keys, the exact quote and where it appears."

**Input:** visible page text; text revealed by P3's Enter and Space presses and by P5's triggers (help links that show text in place, as in ACT ebe86a Passed Example 3); the trapped element's accessible name and description; help and documentation pages linked from the page, one hop, same domain. The title attribute is not input: it shows only on mouse hover. Documentation found anywhere else, such as an external manual, does not count.

**Output:** `{documented: yes|no, keys: [...], quote, source_url}`.

**Rubric.** Yes only if the text names a specific key AND says, or plainly implies, that it leaves this element or section (or every element of its kind on the page). A shortcut list with no exit key is no. Text users cannot perceive (HTML comments, display:none, aria-hidden with no visible text) is no. Mechanical guards: the quote must appear verbatim in the collected text, and help reached through a link or trigger counts only if a stop in P1, P2 or P3 reaches that link or trigger (G21: help must be available by keyboard); otherwise the answer counts as no.

| Text found | Answer |
| --- | --- |
| "In the code editor, press Esc, then Tab to move to the next field." | Yes: Escape, then Tab |
| "Ctrl+M toggles whether Tab inserts a tab or moves focus." | Yes: Ctrl+M |
| "Press Ctrl+M to Exit" in a paragraph before the trapped buttons (ACT ebe86a Passed Example 1) | Yes: Ctrl+M |
| "Go to the next element" (ACT ebe86a Failed Example 2) | No |
| "Keyboard shortcuts: J next story, K previous story." | No |
| `<!-- press F2 to exit -->` in source only | No |
| "This page has no keyboard traps." | No |

**Use:** yes → press the keys (M6 or M7). No → continue down table 3a.

### J2. Does this section require input before focus can move on?

**Question:** "Does this section ask the user to enter or choose something before they can continue? If yes, what values satisfy it, using only the instructions on the page?"

**Input:** screenshot of the loop region; loop members with roles, names, labels and descriptions; visible text in the region.

**Output:** `{gate: yes|no|unsure, fields: [{locator, value, basis_quote}]}`.

**Rubric.** Yes: consent or terms checkboxes, a required field with a stated format, an age or location gate. No: navigation menus, carousels, media players, toolbars, rich-text editors. Values come from on-page instructions or are neutral (check a box, "12345" for a stated 5-digit ZIP), never real personal data. A CAPTCHA or a value only the user could know (account number) is yes with no values, which gives M9.

| Section | Answer |
| --- | --- |
| "Enter your 5-digit ZIP code to see local offices" + field + Go | Yes: 12345 in the field |
| "I agree to the terms" checkbox + Continue | Yes: check the box |
| "Enter your account number to continue" | Yes, no values (NEEDS REVIEW) |
| Mega-menu whose links cycle | No |
| Video player controls cycling | No |

## 5. Edge cases

Only cases that need a rule of their own; everything else follows sections 2–3. V-numbers are browser checks in [4c-build-tasks.md](4c-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| Iframes, including embedded video players | In scope: all iframe content is tested (p. 55, 12.D note), and WCAG requires all content on the page to meet 2.1.2 (Understanding 2.1.2 note; Conformance Requirement 5). Traversal follows focus into same- and cross-origin frames; the iframe element itself is a valid stop (p. 22, 4.D note). A trap inside a third-party player fails the page. Focus apparently stuck on an iframe whose inside can't be read: M1 | V5 |
| Iframes with tabindex=-1 | Tab skips the iframe and everything inside it (V9). Content the keyboard cannot reach is not a 4.C trap: 2.1.2 applies only where focus can be moved there using a keyboard (Understanding 2.1.2; G21). No instance, and the content is left out of the inventory. Coverage note: "<frame> holds N focusable elements the keyboard cannot reach (4.A; ACT akn7bn). A user who enters by mouse may be trapped; not tested." | V9 |
| Arrow-key widgets (menus, tabs, grids, trees, listboxes, toolbars, radio groups) | Arrow cycling inside a widget is not a loop; loop detection runs on Tab sequences only. From every inner stop P4 reaches, Tab and Shift+Tab must leave the widget, or that stop is a trap event | V13 |
| Focus pulled back by script on blur, at once or after a delay | Caught by the settle rule's focus check. In Chrome, script focus() pulls focus back even from the browser UI (V15), so the refocusing elements in ACT f5ea9fd3 and 0ec0e93e are stuck and the pair in d2f5325f is a loop in both directions | V14, V15 |
| Infinite scroll | Signs: inventory grows past 2× its start, page height grows every 10 presses, or a request the recording cannot answer during a pass (V10). If there is a sign and Shift+Tab from the top reaches the content after the feed: no trap event, and a note "Feed growth was not fully observed in the recorded page"; whether that content is reachable forward is logged for 4.A. Otherwise NEEDS REVIEW. A sign never produces PASS by itself | V10 |
| Focus lost to the page body | BODY counts as a stop. Tab resuming after the lost element is no event; BODY leading back into earlier stops is a loop | V7 |
| Navigation, reload or new tab during a pass | Not an exit (M5). Logged for 4.E; reload and resume with P6 | — |

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5 (location, plus the failing content where feasible): the matching row (M12 or M14); type (stuck element, or loop with its direction); location (page URL, frame chain, and the CSS path, role and accessible name of the stuck element or every loop member, plus any modal label); steps to reproduce from a fresh load (e.g. "Tab ×14, then Tab ×3: focus stays on #editor"); screenshots entering the trap and after the repeated presses, highlighted on copies only; every exit tried with its result and the J1 and J2 quotes; and the tool versions the plan requires.

**Continuing past a trap.** The PDF says to keep testing "by using the mouse to bypass the trap or refreshing the page and using the keyboard to navigate backwards" (p. 21, Note). The spec does both:

1. Backward: P2 always runs from a fresh load, so elements after a forward trap are reached from the end.
2. Mouse bypass (P6): click a non-interactive spot just after the trap in DOM order, then resume Tab with P1's rules (V8). If the click does not set the Tab starting point, script focus() on the next candidate is the fallback, and the log records that it was used.

Traps found while continuing are separate instances. Stops reached only after a bypass are tagged so 4.D and 4.E can still test them.
