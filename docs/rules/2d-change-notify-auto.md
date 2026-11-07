---
tt_test: 2.D
tt_name: 4.1.2-change-notify-auto
spec_version: 1.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 2.D (4.1.2-change-notify-auto)

The tool gives each page one 2.D outcome: PASS, FAIL, DOES NOT APPLY or
NEEDS REVIEW. It never emits NOT TESTED (p. 6). It reads the changes 2.C's
pass T found; it presses no keys.

1.1.0 (Abby, 2026-11-07): J1 and J2 are settled by reading, so their pictures are evidence for a person, no longer question input (agents asked to say what a picture showed for a question its words settle). 1.0.0 (Abby, 2026-11-05): approved and built, from draft 0.2.0. 0.2.0 (2026-11-04): slides shown by a class count as changes (Terms); instances are 2.C's, still changing at 5 s. Plan:
[research/2026-11-03-auto-updating-2a-2d.md](../research/2026-11-03-auto-updating-2a-2d.md).

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/2.D`). Identify Content, p. 16: "content that changes automatically on the page as part of auto-update"; none: DNA (also p. 15: no auto-updating content makes 2.C and 2.D DNA). Applicability, p. 16. HtT 1.a (dialogs that alert the user; whether they give "sufficient programmatic notification"), 1.b (focus moved to the changed content; whether that is "sufficient to notify the user ... e.g., by describing the change directly in the content to which the focus moved"), 1.c (ANDI structures, "live regions": "Determine whether the changing content is contained within the Live Region"), p. 16. ER, pp. 16–17: PASS if any is true: 1, "a keyboard-accessible dialog"; 2, focus moves to the changed content "AND the content that has changed provides sufficient description about the change"; 3, "The content that has changed is contained in an ARIA Live Region". Note, p. 17: changes caused by user interaction are tested elsewhere.

**Other sources.** DHS course FAQ, [2.D ARIA Live Region in Change Notification](https://github.com/Section508Coordinators/DHSA-TT-200-A/wiki/2.D-ARIA-Live-Region-in-Change-Notification-(Auto-updating)) (Ann Marie Davis, 2019): "you should assume that the screen reader will present the information to the user if it is within the live region ... You are not required to make any other determination except whether change notification appears within the live region." ANDI 29.2.2 (`sandi.js`) counts as live regions `aria-live` polite or assertive, and roles `alert`, `status`, `log`, `marquee` and `timer`. [Understanding 4.1.2](https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html) (notification of changes to states and values); [Understanding 4.1.3](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) (ARIA19, ARIA22, ARIA23) for contrast only: WCAG 2.1, outside Section 508. No ACT rule, no DHS ACT data, no ICT Baseline test (Baseline 5 is User Controls), no Baseline Alignment cases.

**Terms.** Pass T, region, content and element: [2c-auto-updating.md](2c-auto-updating.md) Terms. A *change* is one mutation record inside an auto-updating region during pass T that alters visible text, an image source or rendered children (attribute-only style changes, such as a slide's transform, are not changes of content). When a region showed new content with no such record (a carousel that shows each slide by changing a class), its class and other non-style attribute changes are its changes: otherwise N2 would hold with no change at all, a false PASS. A *live region* is an element ANDI counts as one (above) whose `aria-live` is not `off`. It must be present and rendered at 0 s of pass T, before the change; a region added with the change does not count. A change is *in* a live region when its target is inside one.

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | 2.C's section 1 gives NEEDS REVIEW (A1, A2) | The same, with its reason | p. 16 Identify Content |
| A2 | 2.C's section 1 gives DOES NOT APPLY (A3, A4) | DOES NOT APPLY | p. 15 ("DOES NOT APPLY: 2.C and 2.D"); p. 16 Applicability |
| A3 | Otherwise | Applies; go to section 3 | |

## 2. Evidence to collect

Nothing of its own beyond pass T (2c section 2):

- **The live regions at 0 s:** path, role, `aria-live`, and whether
  rendered. They are read per frame, since an iframe is its own document.
- **Each change:** time, target path, text before and after, and the live
  region holding it, if any.
- **The focus log during pass T:** any focus move with no key pressed,
  and where it went.
- **Dialogs** that opened during pass T (`t4e._DIALOGS_JS`): role,
  accessible name, text, and whether focus moved into them or they hold a
  focusable element.
- **A crop of the content** before and after its first change.

**Time budget:** none beyond pass T (reads only).

## 3. Mechanical checks

Each auto-updating region (2.C's instances) is an *instance*.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| N1 | The changes or the live-region reads are incomplete | NEEDS REVIEW | Spec rule |
| N2 | Every change of the region is in a live region | PASS | p. 17 ER 3; DHS FAQ (only whether it is within the live region) |
| N3 | A change is in no live region, and a dialog opened with it that takes focus or holds a focusable element | Go to J2 | p. 16 ER 1 ("keyboard-accessible dialog") |
| N4 | A change is in no live region, and focus moved into the changed content with it (no key pressed) | Go to J1 | p. 16 ER 2 |
| N5 | A change is in no live region, with no dialog and no focus move | FAIL | p. 16 ER (none of 1–3) |
| J1/J2 | J1 or J2 = sufficient for every such change | PASS | p. 16 ER 1–2 |
| J1/J2 | J1 or J2 = not sufficient | FAIL | p. 16 ER 1–2 |
| N6 | Anything else (unsure, unanswered) | NEEDS REVIEW | Spec rule |

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | Every instance is PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

**Notes (no outcome).**

- `role=marquee` or `role=timer` counted as a live region, as ANDI does.
  Their implicit `aria-live` is off in ARIA, so screen readers may not
  announce them.
- `aria-live="off"` while the content rotates, as W3C's carousel pattern
  does, is in no live region (N5). The note says that announcements come
  on when the rotation is paused, and that the TT asks for a notification
  of each change. Built: `Region.live_off` (inside or holding
  `aria-live="off"`), fixture `t-apg-carousel`.

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| N2 | "<content> changes by itself inside a live region, so screen readers announce the changes." |
| N5 | "<content> changes by itself, but screen reader users are not told: it is not in a live region, focus does not move to it, and no dialog appears. Put it in an aria-live region, or let users pause it and announce the change." |
| A2 | "Nothing on this page changed by itself while we watched, so this test does not apply." |

## 4. Judgment questions

Both questions are settled by looking (CLAUDE.md principle 8, to be added
at 1.0.0). The mechanical check is that the dialog or the focus move
happened with no key pressed. The agent judges only the words, and answers
unsure whenever the evidence does not settle it.

### J1. Does the content focus moved to describe the change?

**Question:** "While the page updated by itself, focus moved to input.focused (its text). Does the focused content itself say what changed (for example "New message from Ana" or "Prices updated at 2:15 PM"), so a screen reader user hearing it would know? Answer sufficient, not_sufficient or unsure."

**Output:** `{choice: sufficient|not_sufficient|unsure, reasons}`.

**Use:** N4.

### J2. Does the dialog tell the user what changed?

**Question:** "While the page updated by itself, a dialog opened (input.dialog: its role, name and text). Does it tell the user what changed on the page? Answer sufficient, not_sufficient or unsure."

**Output:** `{choice: sufficient|not_sufficient|unsure, reasons}`.

**Use:** N3.

## 5. Edge cases

| Case | Rule | Verify |
| --- | --- | --- |
| A live region added in the same moment as its text | Not present before: not counted (as 5.F) | V8 |
| A live region inside an iframe | Read in that frame | V7 |
| A live region with `aria-busy="true"` | Still a live region (the FAQ asks only whether the change is within it) | Spec rule |
| A countdown timer in `role=timer` | N2, with the note above | ANDI `sandi.js` |
| Only moving content (2.B) and no change of content | 2.C DOES NOT APPLY, so 2.D DOES NOT APPLY | p. 15 Note |

## 6. What a FAIL records

For each instance:

- the content and its changes (times, text before and after);
- the live regions on the page, and the nearest one to the content;
- any focus move or dialog;
- the J1 and J2 answers.
