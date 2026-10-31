---
tt_test: 4.B
tt_name: 2.1.1-no-keystroke-timing
spec_version: 0.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 4.B (2.1.1-no-keystroke-timing)

The tool gives each page one 4.B outcome: PASS, DOES NOT APPLY or NEEDS REVIEW. It never gives FAIL on its own evidence: a timing requirement and the lack of an untimed alternative are both for a person to confirm (section 3). It never emits NOT TESTED (p. 6).

**Citations.** Printed page numbers of TT 5.1.3 (text also in `tt://5.1.3/tests/4.B`). 4.B is on p. 20: continue from Test 4.A (HtT 1); determine whether any keystroke timing is required to activate an element, e.g. the speed at which a password is typed is part of authentication (HtT 2); if so, determine whether another keyboard method without timing is available (HtT 3). PASS if a keyboard method is provided for functionality without specific timings (ER 1).

**W3C sources.** [Understanding 2.1.1](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html): "specific timings for individual keystrokes" include repeating or executing several keystrokes within a short period, or holding a key down for an extended period before it registers. These inform the rubric only; the PDF stays the authority.

**Terms.** Stops and passes as in [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | P1 and P2 reach zero stops and the DOM inventory has zero candidates | DOES NOT APPLY (no user activated keyboard functionality) | p. 20 Applicability |
| A2 | Zero stops, but the inventory has candidates | NEEDS REVIEW | Spec rule |
| A3 | Otherwise | Applies | p. 20 Applicability |

## 2. Evidence to collect

**From the shared walk:** stops and pass ends. **Page text:** the visible text of every readable frame (`traverse.page_text`), and every stop's accessible name and title. No extra passes: keystroke timing cannot be seen in the DOM, and a tester settles it from what the page says and from operating it in 4.A (HtT 1).

**Timing words** (case-insensitive, whole words; English only): hold, press and hold, long press, held down, double-press, press twice, quickly, within N seconds, rapidly, in quick succession, typing speed, keystroke rhythm. <!-- OPEN Q6 -->

**Time budget:** under 1 s.

## 3. Mechanical checks

One page-level instance, *P*.

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | No timing word in the page text, names or titles | PASS | p. 20 HtT 2 |
| M2 | A timing word appears | Ask J1 (M3–M5) | p. 20 HtT 2–3 |
| M3 | J1 = no timing required | PASS | p. 20 ER 1 |
| M4 | J1 = timing required | NEEDS REVIEW (a person checks for an untimed keyboard method, HtT 3) | p. 20 HtT 3 |
| M5 | J1 = unsure, or not answered yet | NEEDS REVIEW | Spec rule |

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G3 | P is NEEDS REVIEW, or P1 did not wrap | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | P is PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| A1 | "Nothing on this page can be used with the keyboard, so this test does not apply." |
| M1 / M3 | "Nothing on this page asks you to press keys at a certain speed, hold a key down, or press a key twice quickly." |
| M4 | "The page seems to need keys pressed with a certain timing (<J1 reasons>); please check there is also a way to do it without timing." |
| M5 | "The page mentions key timing and we could not tell whether it is required; please check." |

## 4. Judgment questions

### J1. Does the page require timed keystrokes?

**Question:** "input.matches lists sentences from the page that mention holding keys, pressing quickly or similar. Does any of them require a keyboard user to press keys at a certain speed, hold a key for a set time, or press a key repeatedly within a short time, to make something work? Answer no_timing, timing_required or unsure, with reasons in a few plain words."

**Rubric.** timing_required: "press and hold Space for 3 seconds to confirm", "double-press Enter to submit", typing rhythm used for sign-in. no_timing: the words are unrelated to the keyboard ("hold your card up to the camera", "apply quickly", "within 30 days"). unsure: whenever the sentences do not settle it.
