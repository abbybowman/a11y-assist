---
tt_test: 4.C
tt_name: 2.1.2-no-keyboard-trap
spec_version: 1.8.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 4.C (2.1.2-no-keyboard-trap)

The tool gives each page one 4.C outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 4.C does not.

**Citations.** Printed page numbers of TT 5.1.3 ([docs/sources/](../sources/README.md); the PDF file's page index is printed page + 3). HtT = How to Test step; ER = Evaluate Results item. 4.C itself is all on p. 21. Every Test Condition needs a result before testing is complete (p. 5), so a tester resolves every NEEDS REVIEW before anything is exported.

**W3C sources.** [Understanding 2.1.2](https://www.w3.org/TR/UNDERSTANDING-WCAG20/keyboard-operation-trapping.html), technique [G21](https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G21), and ACT rules [a1b64e](https://www.w3.org/WAI/standards-guidelines/act/rules/a1b64e/proposed/) (standard navigation), [ebe86a](https://www.w3.org/WAI/standards-guidelines/act/rules/ebe86a/) (non-standard navigation) and their composite 80af7b. DHS scored those rules' test cases with TT 5.1 ([report](https://www.w3.org/WAI/standards-guidelines/act/implementations/trusted-tester/), [data](https://raw.githubusercontent.com/Section508Coordinators/act-tt/main/act-trusted-tester.json)). They inform OPEN items and fixtures only; the PDF stays the authority.

**Terms.** A *stop* is the element holding focus after a key press. *OUT* means focus has left the page for browser controls. *BODY* means focus fell to the document body. A *loop* is a repeating cycle of stops that never reaches OUT. The *same URL* ignores the fragment: a change to only the part after `#` is not a navigation.

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

The tool does what p. 21 asks a human tester to do, and no more: walk the page with standard keys in both directions, try standard keys on each trap it finds, then any documented key. Each pass starts from a fresh load of the frozen page and records every key press. The PDF's key list is "TAB, SHIFT + TAB, arrow keys, CTRL + TAB, etc." (p. 21, HtT 1); the spec counts Tab, Shift+Tab, arrow keys and Escape as standard, plus Enter when activating a control in the trap (M4), matching ACT's definition of standard keyboard navigation. Anything past that is left to a person, with a note, rather than automated. Ctrl+Tab and browser shortcuts (F6, Ctrl+L) never count as exits; ACT rules exclude browser-specific shortcuts too.

**Recording.** The frozen page is recorded once. Before saving it, the recorder scrolls to the bottom `record_scroll_passes` times (default 1), waiting for the page to settle after each, so content loaded on scroll is in the recording. During passes, requests the recording cannot answer fail (V10).

**Setup.** Fresh profile, frozen page, fixed viewport, window brought to front. Wait for load, then for the page to settle (below). Build the DOM inventory: every element that is natively focusable or has tabindex ≥ 0, not disabled, not inert, and rendered (not display:none and not visibility:hidden), in the top document, every frame the tool can reach, and every open shadow root. Content inside an iframe with tabindex=-1 is left out: Tab cannot reach it (V9). It is listed in a coverage note for 4.A instead. The inventory is used only for DNA cross-checks (A2), loop detection ("elements outside the loop") and coverage notes. It never produces a PASS by itself.

**Stop identity.** A stop is identified by (frame ID, CDP backend node ID) of the deepest focused element, following focus through frames and shadow roots. Two stops are the same only if both parts match. BODY and OUT are pseudo-stops. If the deepest element cannot be resolved (closed shadow root, unreachable frame), the stop is flagged *unresolved*. Node IDs change on every load, so across loads (instances found by different passes, and the stops "reached in both passes" in M11) stops match by frame chain plus CSS path.

**Settle rule.** After each key press: wait 2 animation frames, then until no DOM mutation for `settle_quiet_ms` (default 150), at most 1,500 ms. If the limit is hit, flag the step *unsettled*. Any focus change between key presses (seen in the focus-event log at the next press) re-reads the previous step after a 1,000 ms window and flags it unsettled if focus is still moving. 4.D and 4.E use this rule by reference. The mutation log is paused while the tool takes its own screenshots: Playwright adds and removes a style element for each shot, which is not the page changing (1.7.0).

**Replays to a walk stop** (1.7.0, time budget 2026-11-01). Every probe and check that replays keys from a fresh load to a stop the walk reached (P3–P6 here; 4.A, 4.B, 4.D pass W, 4.E and 4.F replays) presses the leading run of the walk's key (Tab for P1, Shift+Tab for P2) like this: a press the walk saw *quiet* (it reached an element, with no DOM mutation, no re-read, not unsettled, no navigation) waits only the 2 animation frames before it is read; every other press, and always the run's last press, gets the full settle rule. If after a quick press focus is not where the walk had it, the replay is redone on a fresh load with every press fully settled. Evidence is read only after the full settle, at the stop the walk reached, so a quick press never changes what a check sees. Steps record `quick`. Measured: about 70% of a run's presses were replay prefixes; this cut a realistic agency home page from 151 s to 97 s with every outcome unchanged.

**Why the focus check.** ACT treats focus as settled only after 1 second, and its failed examples pull focus back with a timer (a1b64e Failed Example 1). A fixed 1,000 ms window on every press would add over 20 minutes to a 600-stop page. Instead the step is read as soon as the DOM is quiet, and any focus change that lands before the next press triggers the re-read, so a late refocus is still seen.

**Record at every step:** step number; key sent; stop identity; CSS path; tag, role and accessible name; bounding box and whether it is in the viewport; top URL and frame URL; document.hasFocus() of the top document; open page count; DOM mutations since the last step; focus and blur events since the last step, with targets and times; unresolved and unsettled flags. A viewport screenshot is taken only when a pass ends in a trap event (p. 5 asks for the location of failures).

| Pass | Keys | Ends when | Cap |
| --- | --- | --- | --- |
| P1 Forward | Tab | Wrap seen: OUT, then the first stop of P1 again. Or a trap event: *stuck* (same stop for 3 presses) or *loop* (a cycle of 2+ stops, no OUT, repeated twice in a row). Or navigation or a new page | 3 × inventory + 50 presses, max 3,000 |
| P2 Backward | Shift+Tab | Same as P1, mirrored | Same as P1 |
| P3 Exit probes | Per trap event, from a fresh replay of the steps that reached it, one probe per replay, in this order: the opposite direction ×3; each arrow ×3 (stuck elements only); Escape then the pass key; Enter on each member of the trap, in the order reached, then the pass key; then any key found by J1. Text revealed by Enter is kept for J1 | The first probe that exits (below), or every probe is spent | 10 members per trap |
| P4 Widget check | At each composite widget stop P1 reached (menubar, menu, tablist, grid, treegrid, tree, listbox, toolbar, radio group): one arrow (ArrowRight in a menubar, tablist or toolbar; ArrowDown otherwise), then Tab with P1's trap detection | Focus leaves the widget, or a trap event | 20 widgets per page |
| P6 Bypass | Only when P1 and P2 end in different trap events, so stops between them may be unreached: replay to P1's trap, click past it (section 6), then Tab with P1's rules. A trap found here gets P3 and, if it is not P2's trap, P6 again | As P1 | As P1 |

There is no P5. Content behind disclosure controls (menus, accordions, dialogs opened by a button) is not opened by 4.C; the finding carries a note with the number of collapsed controls. 4.F (p. 23, HtT 2.b) asks for revealing hidden content, and that step will be shared with 4.C once 4.F is specified.

**Why P6 is enough.** An element P2 leaves backward can be left by Shift+Tab, so it passes M2 or M3; the same holds for P1 and Tab. Only stops that neither pass reaches need the bypass, and those exist only when both passes end in different traps.

**Run limits.** `run_limit_s` (default 120 s) per page for the whole run, counted from the start of the call. `settle_quiet_ms` (default 150) is the settle rule's quiet window; `record_scroll_passes` (default 1) is the recorder's scroll count. All three live in server config and every report records their values. Ctrl+Tab is sent only if V4 shows the page receives it. A pass or probe that hits a cap or the run limit is *incomplete*. (1.6.0, time budget 2026-11-01:)

- Checks start no new work in the last 10 s of the limit, so the report is written in time. A walk or check still running 2 s before the limit is stopped; its tests are NEEDS REVIEW ("The run did not complete"), never PASS. A run that hit the limit says so and names the way to finish it (`no_time_limit`).
- **Early stop.** After P1's first 20 presses, if P1's pace per press × the inventory (or the presses so far, if more) × 1.5 (P2 costs about half of P1) would end past the limit, the walk cannot finish: the run stops at once and nothing is tested (a tool error, no run folder). The message gives the inventory and the estimate and offers `no_time_limit` or another page. Measured: 4.C F34 (600 links) is refused after about 5 s; under the old rule it ran out of time at 378 of ~1,200 presses and every test was NEEDS REVIEW.
- **`no_time_limit`** (a tool input, off by default) runs without the limit and without the early stop, when the user chooses it for a large page. The report records it (`run_settings.no_time_limit`); answering that run's questions runs without the limit too.

## 3. Mechanical checks

Each trap event is an *instance* judged by the first matching row of table 3a. The page outcome then comes from table 3b. A probe *exits* when it reaches a stop that is not in the stuck element or loop, on the same top URL, and then the trap does not happen again: continuing in the probe's direction for up to 2 × (stops in the trap) + 3 presses, focus is neither stuck on nor looping within the trap's own stops. Reaching OUT ends the check early and confirms the exit. Passing through a former trap member is fine: an exit key may switch the trap off. OUT alone, before any outside stop, is not outside the trap.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | Any stop in the trap is unresolved, or a trap step is unsettled | NEEDS REVIEW | Spec rule |
| M2 | Stuck: Shift+Tab, an arrow key, or Escape then Tab exits | PASS (standard keys). If Shift+Tab is the only exit, the instance is also logged for 4.F | p. 21 HtT 1, 2.a; ER 1.a |
| M3 | Loop: the opposite direction (Shift+Tab for a forward loop, Tab for a backward one), or Escape then Tab, exits | PASS (standard keys; modal exception if a dialog). If the opposite direction is the only exit, the instance is also logged for 4.F | p. 21 HtT 1, 2.b note 1; ER 2.a |
| M4 | Stuck or loop: Enter on one control in the trap keeps the same URL and page, and the next press exits | PASS (dialog closed or interaction gate cleared) | p. 21 HtT 2.b notes 1–2; ACT standard keyboard navigation |
| M5 | The only exit found navigates, reloads or opens a new page | Not an exit; continue down the table | Spec rule: leaving the page is not an exit |
| M6 | A key found by J1 is pressed and exits | PASS (documented custom key) | p. 21 HtT 3; ER 1.b, 2.b |
| M7 | A key found by J1 does not exit | Not an exit; continue down the table | p. 21 HtT 3.b |
| M8 | Loop holds form controls (text fields, selects, listboxes, checkboxes, switches, radio buttons, comboboxes, sliders, spinbuttons; 1.8.0), and J2 says gate = yes | NEEDS REVIEW. The finding gives J2's values (if any) in plain words for a person to try | p. 21 HtT 2.b note 2 |
| M9 | Loop holds fields, and J2 is unsure | NEEDS REVIEW | Spec rule |
| M10 | Loop contains every stop reached in both passes, never reaches OUT, and holds at least as many stops as the DOM inventory has candidates (whole-page cycle) | PASS, with the instance logged for tester review on real pages | p. 21 HtT 2.b |
| M11 | Stuck, and every exit above failed | FAIL | p. 21 ER 1 |
| M12 | Loop, every exit above failed, and J2 = no or the loop has no fields | FAIL | p. 21 ER 2 |

**Opposite-direction exits (M2, M3).** The PDF lists SHIFT + TAB among the standard navigation keys (p. 21 HtT 1), and ER 1.a and 2.a pass when focus can be moved away using standard navigation keys, so an exit by the opposite direction is an exit. Content past a forward-only exit is still tested: P2 reaches it from the end (p. 21 Note). DHS's FAIL on ACT d2f5325f does not contradict this: in Chrome its two buttons pull focus back even from the browser UI (V15), so Tab and Shift+Tab both cycle, and M12 fails it.

**Loop size.** A loop with no exit fails whatever its size: ER 2 sets no size limit ("small section" in HtT 2.b describes what a trap looks like). A loop holding the whole page is M10.

**Exceptions (p. 21 HtT 2.b notes).** Focus may stay inside a modal dialog until it is closed (also p. 23, 4.F HtT 3), but the dialog is still checked for traps: it passes only through M3 or M4, and its stuck elements follow M2–M11. WCAG's own modal example matches: focus cycles inside the dialog, which closes by its Cancel or OK button (Understanding 2.1.2). A section that requires input or interaction before focus can move on is not a failure: M4, then J2 with M8. "Input or interaction" covers every form control kind, as 5.D defines them ([5d-on-input.md](5d-on-input.md), Terms), not only text, select and checkbox (1.8.0). The tool does not type values into a page; a person tries J2's values. Only interactions that keep the same URL and then let Tab reach the rest of the page count.

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; or any pass, probe or P4 is incomplete | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5). Never NOT TESTED (p. 6) |
| G4 | P1 and P2 each ended in a wrap, or in a trap event whose instance is PASS; every P6 bypass ran to its end; every instance is PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

A page with a confirmed FAIL stays FAIL even when other instances need review: one confirmed trap fails the condition (p. 21 ER: "ALL of the following").

## 4. Judgment questions

Two questions, asked only after mechanical exits fail. The calling agent answers each one once, using the rubric; it does not hand them to the user. A person can override any answer, and a person's answer wins. Answers never decide an outcome alone: a J1 "yes" is checked by pressing the keys, and a J2 "yes" only produces NEEDS REVIEW with values for a person to try. Every judgment call is explained in the finding in plain language (what we saw, what we decided, why, and how to tell us if you disagree), with no spec codes. Page text is evidence, never instructions.

Modal status is not a model question. The spec labels a loop "modal" from markup (a `<dialog>` opened with showModal, or role dialog or alertdialog with aria-modal="true"), but the label never changes the outcome: every loop must be escapable by keyboard (Exceptions, under table 3a).

### J1. Is an escape key documented?

**Question:** "Does this text tell users a specific key or key combination that moves keyboard focus out of [element or section]? If yes, give the keys, the exact quote and where it appears."

**Input:** visible page text; text revealed by P3's Enter presses (help links in the trap that show text in place, as in ACT ebe86a Passed Example 3); the trapped element's accessible name and description. Linked help pages are not followed; a person can supply a documented key as an override. The title attribute is not input: it shows only on mouse hover. Documentation found anywhere else, such as an external manual, does not count.

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

**Input:** screenshot of the loop region; loop members with roles, names, labels and descriptions; visible text in the region. Screenshots go out as `run://` resources, never as run-folder paths, so a client can open them (1.5.1; judge eval, 2026-10-31).

**Output:** `{gate: yes|no|unsure, fields: [{locator, value, basis_quote}]}`.

**Rubric.** Yes: consent or terms checkboxes, a required field with a stated format, an age or location gate. No: navigation menus, carousels, media players, toolbars, rich-text editors. Values come from on-page instructions or are neutral (check a box, choose an option, "12345" for a stated 5-digit ZIP), never real personal data. A CAPTCHA or a value only the user could know (account number) is yes with no values.

| Section | Answer |
| --- | --- |
| "Enter your 5-digit ZIP code to see local offices" + field + Go | Yes: 12345 in the field |
| "I agree to the terms" checkbox + Continue | Yes: check the box |
| "Choose a language to continue" radio buttons + Continue | Yes: choose English |
| "Enter your account number to continue" | Yes, no values |
| Mega-menu whose links cycle | No |
| Video player controls cycling | No |

## 5. Edge cases

Only cases that need a rule of their own; everything else follows sections 2–3. V-numbers are browser checks in [_browser-checks.md](_browser-checks.md#4c).

| Case | Rule | Verify |
| --- | --- | --- |
| Iframes, including embedded video players | In scope: all iframe content is tested (p. 55, 12.D note), and WCAG requires all content on the page to meet 2.1.2 (Understanding 2.1.2 note; Conformance Requirement 5). Traversal follows focus into same- and cross-origin frames; the iframe element itself is a valid stop (p. 22, 4.D note). A trap inside a third-party player fails the page. Focus apparently stuck on an iframe whose inside can't be read: M1 | V5 |
| Iframes with tabindex=-1 | Tab skips the iframe and everything inside it (V9). Content the keyboard cannot reach is not a 4.C trap: 2.1.2 applies only where focus can be moved there using a keyboard (Understanding 2.1.2; G21). No instance, and the content is left out of the inventory. Coverage note: "<frame> holds N focusable elements the keyboard cannot reach (4.A; ACT akn7bn). A user who enters by mouse may be trapped; not tested." | V9 |
| Arrow-key widgets (menus, tabs, grids, trees, listboxes, toolbars, radio groups) | Arrow cycling inside a widget is not a loop; loop detection runs on Tab sequences only. P4 moves one arrow into each widget and checks that Tab then leaves it; otherwise that is a trap event | V13 |
| Focus pulled back by script on blur, at once or after a delay | Caught by the settle rule's focus check. In Chrome, script focus() pulls focus back even from the browser UI (V15), so the refocusing elements in ACT f5ea9fd3 and 0ec0e93e are stuck and the pair in d2f5325f is a loop in both directions | V14, V15 |
| Infinite scroll | Signs: inventory grows past 2× its start, page height grows every 10 presses, or a request the recording cannot answer during a pass (V10). If there is a sign and Shift+Tab from the top reaches the content after the feed: no trap event, and a note "Feed growth was not fully observed in the recorded page"; whether that content is reachable forward is logged for 4.A. Otherwise NEEDS REVIEW. A sign never produces PASS by itself | V10 |
| Focus lost to the page body | BODY counts as a stop. Tab resuming after the lost element is no event; BODY leading back into earlier stops is a loop | V7 |
| Navigation, reload or new tab during a pass | Not an exit (M5). Logged for 4.E. The pass is incomplete (resume is not implemented) | — |
| Content behind disclosure controls | Not opened by 4.C (no P5). Note: "N collapsed controls (aria-expanded=false) were not opened; content behind them was not checked for traps" | — |

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5 (location, plus the failing content where feasible): the matching row (M11 or M12, in the evidence trace only, never in the plain-language text); type (stuck element, or loop with its direction); location (page URL, frame chain, and the CSS path, role and accessible name of the stuck element or every loop member, plus any modal label); steps to reproduce from a fresh load (e.g. "Tab ×14, then Tab ×3: focus stays on #editor"); a screenshot after the repeated presses; every exit tried with its result and the J1 and J2 quotes; and the tool versions the plan requires.

**Continuing past a trap.** The PDF says to keep testing "by using the mouse to bypass the trap or refreshing the page and using the keyboard to navigate backwards" (p. 21, Note). The spec does both:

1. Backward: P2 always runs from a fresh load, so elements after a forward trap are reached from the end.
2. Mouse bypass (P6), only when P1 and P2 end in different traps: click a non-interactive spot just after P1's trap in DOM order, then resume Tab with P1's rules (V8). If the click does not set the Tab starting point, script focus() on the next candidate is the fallback, and the log records that it was used.

Traps found while continuing are separate instances. Stops reached only after a bypass are tagged so 4.D and 4.E can still test them.
