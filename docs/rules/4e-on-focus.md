---
tt_test: 4.E
tt_name: 3.2.1-on-focus
spec_version: 0.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 4.E (3.2.1-on-focus)

The tool gives each page one 4.E outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 4.E does not.

**Citations.** Printed page numbers of TT 5.1.3 ([docs/sources/](../sources/README.md); text also in `tt://5.1.3/tests/4.E`). HtT = How to Test step; ER = Evaluate Results item. 4.E is on pp. 22–23: continue from Test 4.D (HtT 1); when the interface component receives focus, evaluate whether an unexpected change of context occurs, "e.g., a new window is launched, or focus is moved to another interface component" (HtT 2); PASS if an unexpected change of context is not initiated when a component receives focus (ER 1).

**W3C sources.** [Understanding 3.2.1](https://www.w3.org/WAI/WCAG22/Understanding/on-focus.html) (its examples: a form submitted, a new window launched, or focus changed to another component when a component receives focus), the definition of *change of context* (changes of user agent, viewport, focus, or content that changes the meaning of the page; "a change of content is not always a change of context", e.g. an expanding outline, dynamic menu or tab control), technique G107, and failure [F55](https://www.w3.org/WAI/WCAG22/Techniques/failures/F55) (script removes focus when focus is received). No ACT rule covers 3.2.1, so fixtures are custom. These inform OPEN items and fixtures only; the PDF stays the authority.

**Terms.** *Stop*, *OUT*, *BODY*, passes P1 and P2, stop identity and the settle rule are defined in [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) (Terms, section 2). The *target* of a step is the element that first receives focus after the key press (the first trusted focus-in in the step's focus log). A *context signal* is one of: the top URL changes (ignoring the fragment) or the page reloads; a new page or window opens; focus moves on its own (below); a dialog becomes visible.

## 1. Applicability

The same evidence as 4.C and 4.D: 4.E is DOES NOT APPLY only when nothing on the page can receive keyboard focus (p. 22 Applicability).

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | P1 and P2 reach zero stops, and the DOM inventory has zero candidates | DOES NOT APPLY | p. 22 Applicability |
| A2 | P1 and P2 reach zero stops, but the inventory has candidates | NEEDS REVIEW (walk or inventory fault) | Spec rule |
| A3 | P1 or P2 reaches one or more stops | Applies; go to section 3 | p. 22 Applicability |

## 2. Evidence to collect

**From the shared keyboard walk** (`walk.py`): every P1 and P2 step's stop, top URL, open page count, DOM mutation count, unsettled and unresolved flags, focus log, and each pass's end. The walk already ends a pass on navigation or a new page, so those steps are its last. A tester watching each element receive focus (HtT 2) sees exactly these events; 4.E adds no passes.

**Walk extras** (collected only when 4.E is selected; cheap, no images):

1. **Richer focus log.** For each focus-in and focus-out: whether the event is trusted, the element's CSS path, and for focus-out whether the element receiving focus (`relatedTarget`) is inside the one losing it. The current log records only tag and id.
2. **Dialog visibility.** After each step, whether a dialog is visible that was not visible before the key press (`<dialog open>`, role dialog or alertdialog), and its CSS path.

**Confirmation replays** (4.E's own follow-up, only for steps with a context signal other than a dialog): (a) *reproduce*: fresh load, replay the keys up to that step, press the key, and check that the same signal happens again; (b) *control*, for navigation and new pages only: fresh load, replay the keys before that step, then wait as long as the original step took, without the final key. A signal that also happens in the control is caused by time, not by focus. At most 10 steps get replays; more is G3.

**Time budget:** the extras add a few milliseconds per step. Each confirmation is one fresh replay (about 2–5 s on a fixture page). Pages without context signals cost nothing more. The whole run stays within `run_limit_s`.

## 3. Mechanical checks

Each step with a context signal is an *instance*. Focus *moves on its own* when, after one key press and with no further key, the focus log shows the target losing focus to another element or to the page body. It does not count when focus moves into the target (a widget handing focus to its active item), or back to the stop focus was on before the key (that is the element being left pulling focus back: 4.C's evidence, initiated by its blur, not by the target receiving focus).

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | The step is unsettled or unresolved, or a focus event in it is untrusted | NEEDS REVIEW | Spec rule |
| M2 | The control replay shows the same navigation or new page without the key | No instance (caused by time, not focus); note for test 8.A | Spec rule |
| M3 | The reproduce replay does not show the signal again | NEEDS REVIEW | Spec rule |
| M4 | The top URL changes or the page reloads after a Tab or Shift+Tab | FAIL | p. 22 HtT 2; Understanding 3.2.1 (change of user agent / viewport) |
| M5 | A new page or window opens after a Tab or Shift+Tab | FAIL | p. 22 HtT 2 ("a new window is launched") |
| M6 | Focus moves on its own to another element | FAIL | p. 22 HtT 2 ("focus is moved to another interface component") |
| M7 | Focus moves on its own to the page body (the target drops focus) | FAIL | p. 22 HtT 2; F55 |
| M8 | Only a dialog becomes visible; focus stays on the target | NEEDS REVIEW: a person decides whether it changes the meaning of the page | Definition of change of context; Spec rule |

**Not instances.** Content that changes without any context signal (a menu expanding on focus, a tooltip, a hint, an accordion opening) is a change of content, not of context (WCAG definition, Note). Scrolling the focused element into view is the browser's default, not the page's.

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; or P1 or P2 is incomplete (cap, time limit, error); or P1 and P2 ended in different traps, so stops between them were not reached; or more than 10 steps needed replays | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5). Never NOT TESTED (p. 6) |
| G4 | P1 and P2 each ended in a wrap or at the same trap, and there is no instance | PASS |
| G5 | Anything else | NEEDS REVIEW |

A pass that ends on navigation is complete for 4.E only when that navigation is an M4 instance; G2 then decides the page.

**Plain-language sentences.** Row IDs stay in the evidence trace. `<element>` is the role and name in plain words; `<keys>` is the key sequence from a fresh load.

| Row | Sentence |
| --- | --- |
| Page PASS | "We moved keyboard focus to each of the N elements we could reach, and none of them opened a new page or window or moved focus somewhere else on its own." |
| Page FAIL | "Moving keyboard focus onto some elements changes what the user is doing without their asking, which can disorient keyboard and screen reader users." |
| Page NEEDS REVIEW | "We could not finish this test, so a person needs to check it." |
| A1 | "Nothing on this page can receive keyboard focus, so this test does not apply." |
| A2 | "We could not move keyboard focus anywhere, although the page has elements that should take focus. Please check by hand." |
| M1 | "Something happened when <element> got focus that we could not read reliably. Please check it: load the page and press <keys>." |
| M2 (note) | "The page goes to another page on its own after a while, even without any key press; that is not caused by focus, but it may matter for the time limits test." |
| M3 | "When <element> got focus, <signal in plain words> once, but not when we tried again. Please check it: load the page and press <keys>." |
| M4 | "When <element> gets keyboard focus, the page goes to another address without the user choosing to. To see it, load the page and press <keys>." |
| M5 | "When <element> gets keyboard focus, a new window or tab opens. To see it, load the page and press <keys>." |
| M6 | "When <element> gets keyboard focus, focus jumps on its own to <other element>, so keyboard users cannot stay where they meant to be. To see it, load the page and press <keys>." |
| M7 | "<element> drops keyboard focus as soon as it gets it, so keyboard users can't use it. To see it, load the page and press <keys>." |
| M8 | "When <element> gets keyboard focus, a dialog appears. If it takes over the page or changes what the page is for, that is a problem; if it is only a hint, it is fine. Please look: load the page and press <keys>." |

## 4. Judgment questions

None. Every signal is mechanical, and the one case that needs a person's eyes (M8) goes to NEEDS REVIEW with a plain sentence rather than a model question.

## 5. Edge cases

Only cases that need a rule of their own; everything else follows sections 2–3. V-numbers are browser checks in [4e-build-tasks.md](4e-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| Navigation in the frozen page | The replay serves only recorded responses; a navigation to an unrecorded page still changes the top URL, which is the signal | V1 |
| Focus pulled back by the element being left (4.C refocus on blur) | Not an instance (section 3); 4.C judges it | V2 |
| Composite widget handing focus to its active item | Not an instance (focus moved into the target) | V2 |
| Focus moving into a dialog that the target opened | M6 (focus moved to another element) | V2 |
| Stops past a keyboard trap | Reached by P2 where possible; between two different traps: G3 | — |
| Change of context on mouse focus | Out of scope: 4.E continues from the keyboard tests (HtT 1) | — |

**OPEN O1, "unexpected".** ER 1 fails an *unexpected* change of context. WCAG 3.2.1 has no exception for changes the user was warned about (unlike 3.2.2 On Input), and Understanding 3.2.1 lists the examples without one. Options: (a) every context signal on focus is unexpected; (b) pass changes the page documents beforehand, through a model question. (b) adds a judgment the PDF's example list does not suggest. Recommend (a).

**OPEN O2, focus pulled back to the element just left.** Options: (a) not a 4.E instance (initiated by the left element's blur; 4.C judges the trap); (b) an M6 instance against the left element. Recommend (a): the target did not initiate it, which is what 3.2.1 is about.

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5: the matching row (in the evidence trace only); location (page URL, frame chain, CSS path, role and accessible name of the target, and of the element focus moved to, if any); the signal (new URL, new page, focus moved, focus dropped) with the focus log of the step; steps to reproduce from a fresh load ("Tab 7 times"); the reproduce replay's result; and the tool versions the plan requires.

**Continuing past a failure.** A navigation or new page ends the walk's pass at that step (4.C section 2); P2 covers the rest from the end. Each failing step is its own instance.
