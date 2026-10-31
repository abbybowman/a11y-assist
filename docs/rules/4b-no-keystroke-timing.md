---
tt_test: 4.B
tt_name: 2.1.1-no-keystroke-timing
spec_version: 1.0.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 4.B (2.1.1-no-keystroke-timing)

The tool gives each page one 4.B outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED (p. 6).

**Citations.** Printed page numbers of TT 5.1.3 (text also in `tt://5.1.3/tests/4.B`). 4.B is on p. 20: continue from Test 4.A (HtT 1); determine whether any keystroke timing is required to activate an element, e.g. the speed at which a password is typed is part of authentication (HtT 2); if so, determine whether another keyboard method without timing is available (HtT 3). PASS if a keyboard method is provided for functionality without specific timings (ER 1).

**Other sources.** [Understanding 2.1.1](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html): "specific timings for individual keystrokes" include repeating or executing several keystrokes within a short period, or holding a key down for an extended period before it registers. The [ICT Testing Baseline](https://ictbaseline.access-board.gov/web-baselines/01Keyboard/) 1.A tests it the same way as the PDF, by hand. Its alignment test case [TC01.A-2-fail-1](https://baselinealignment.section508.gov/testcases/TC01.A-2-fail-1.html) expects FAIL for a page that says to press and hold Space for 3 seconds with no alternative. No automated rule (ACT, axe) covers it: everyone finds timing from the page's instructions or by using the page. These informed the design and fixtures; the PDF stays the authority.

**Terms.** Stops and passes as in [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md). The *effect* of a key press is defined in [4a-keyboard-access.md](4a-keyboard-access.md) (Terms).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | P1 and P2 reach zero stops and the DOM inventory has zero candidates | DOES NOT APPLY (no user activated keyboard functionality) | p. 20 Applicability |
| A2 | Zero stops, but the inventory has candidates | NEEDS REVIEW | Spec rule |
| A3 | Otherwise | Applies | p. 20 Applicability |

## 2. Evidence to collect

**From the shared walk:** stops, with accessible name and title (4.A's walk extra), and pass ends. **Page text:** the visible text of every readable frame (`traverse.page_text`, one fresh load). Keystroke timing cannot be seen in the DOM; a tester finds it from what the page says and from using it (HtT 1–2).

**Timing words** (case-insensitive, whole words, English only): hold, holding, held down, press and hold, long press, double-press, double press, press twice, twice quickly, quickly, rapidly, in quick succession, within N second(s), for N second(s), typing speed, keystroke rhythm. Each sentence of the page text, a stop's name or a stop's title that contains one is a *match*.

**Timing proof** (only after J1 = timing_required). For the stop J1 names, three fresh replays to it: (a) one normal press of the key; (b) the timed press J1 describes: the key held down for its duration plus `HOLD_EXTRA_MS` (300 ms), or pressed its number of times `REPEAT_GAP_MS` (50 ms) apart; (c) only when (b) has an effect and (a) has none, a second (b), to confirm. Each records the effect.

**Time budget:** page text under 1 s; a proof is three replays (about 10 s), at most one per page per J1 answer.

## 3. Mechanical checks

One page-level instance, *P*.

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | No match | PASS | p. 20 HtT 2 |
| M2 | Matches | Ask J1 (J1?–M9) | p. 20 HtT 2 |
| M3 | J1 = no_timing | PASS | p. 20 ER 1 |
| J1? | J1 not answered yet | NEEDS REVIEW | Open question |
| M4 | J1 = unsure, or timing_required without a stop number, a key, and a duration or press count | NEEDS REVIEW | Spec rule |
| P? | The proof has not run yet | NEEDS REVIEW | Spec rule |
| M5 | Proof: focus did not reach the stop, the normal press has an effect, the timed press or the second one has none, or a timed effect is unreliable | NEEDS REVIEW (timing not confirmed) | Spec rule |
| J2? | Proof confirms timing (ask J2, HtT 3); J2 not answered yet | NEEDS REVIEW | p. 20 HtT 3 |
| M7 | J2 = alternative, naming a stop other than the timed one | PASS | p. 20 HtT 3; ER 1 |
| M8 | J2 = no_alternative | FAIL | p. 20 ER 1 |
| M9 | J2 = unsure, or an alternative that names no other stop | NEEDS REVIEW | Spec rule |

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | P is FAIL | FAIL |
| G3 | P is NEEDS REVIEW, or P1 did not wrap, or the page text could not be read | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | P is PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| A1 | "Nothing on this page can be used with the keyboard, so this test does not apply." |
| M1 | "Nothing on this page asks you to press keys at a certain speed, hold a key down, or press a key several times quickly." |
| M3 | "The page mentions holding or timing (<J1 reasons>), but not for using the keyboard." |
| J1? / P? / J2? | "The page mentions holding or timing; a question about it is still open." / "The page mentions key timing; we have not tried it yet." / "<element> works only if you <timing>; a question about it is still open." |
| M4 | "The page mentions key timing and we could not tell whether it is required; please check." |
| M5 | "The page says <element> needs you to <timing>, but pressing the key that way did not behave differently from a normal press, so we could not confirm it. Please check: load the page, press <keys>, then try it." |
| M7 | "<element> needs you to <timing>, but <other> does the same thing with a normal key press (<J2 reasons>). If you disagree, tell your assistant." |
| M8 | "<element> works only if you <timing>, and nothing else on the page does the same thing with a normal key press. People who cannot press keys quickly or hold them steadily cannot use it. To see it, load the page, press <keys>, then <timing>." |
| M9 | "<element> needs you to <timing>; please check whether something else on the page does the same thing without timing." |

## 4. Judgment questions

J1 and J2 are look-and-decide questions (CLAUDE.md principle 8): the agent answers by the rubric and answers unsure whenever the evidence does not settle it; a person's answer overrides it. A J1 answer only leads to a FAIL after the key presses confirm it (M5–M6) (Abby, 2026-10-31).

### J1. Does the page require timed keystrokes?

**Question:** "input.matches lists sentences from the page that mention holding keys, pressing quickly or similar; input.stops lists, numbered, the elements keyboard focus reaches. Does any sentence say a keyboard user must hold a key for a time, or press a key several times quickly, to make something work? Answer timing_required (with element: the stop's number, key: the key, and duration_ms for holding or presses for repeating), no_timing, or unsure, with reasons in a few plain words."

**Rubric.** timing_required: "press and hold Space for 3 seconds to confirm", "double-press Enter to submit". no_timing: the words are not about keys ("hold your card up to the camera", "apply quickly", "within 30 days"). unsure: whenever the sentences do not settle it, including timing that is about typing speed or rhythm (the proof cannot reproduce it).

### J2. Is there a way without timing?

**Question:** "input.timed is an element that works only with the timed key press in input.timing (confirmed by pressing the keys). input.stops lists, numbered, every element keyboard focus reaches. Is there an element that does the same thing with a normal key press? Answer alternative (with element: its number), no_alternative or unsure, with reasons."

**Rubric.** As 4.A J1. The named number must be a stop other than the timed element (mechanical guard; otherwise unsure).

## 5. What a FAIL records

The matched sentences, J1's and J2's answers and reasons, the three proof presses with their effects, the keys to reach the element from a fresh load ("Tab 4 times"), and the tool versions the plan requires.
