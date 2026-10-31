# Brief: rewrite the 4.D draft for the current spec rules

For the thread drafting `docs/rules/4d-focus-visible.md`. Since that draft
started, the 4.C spec moved to 1.5.0 and the repo gained a shared keyboard
walk and a check interface. Read these on branch `ccr-9bc8f27b-l7ncp0`
(commit `f99ae4f` or later):

| Read | Why |
| --- | --- |
| `CLAUDE.md`, principles 7 and 8 and "Other rules" | New: proportionate to the PDF; opinionated, explained, overridable; hosted-safe; time limit |
| `docs/rules/_template.md` | New sections: evidence from the shared walk, extra evidence, time budget; new judgment rules |
| `docs/rules/4c-no-keyboard-trap.md` (1.5.0) | The model spec: what was cut and why, the settle rule 4.D inherits |
| `src/a11y_assist/walk.py`, `src/a11y_assist/checks/base.py` | What 4.D receives (the walk) and must provide (the `Check` interface) |
| `src/a11y_assist/checks/t4c.py`, `plain_summary` | How a finding explains itself to a non-tester |
| `docs/plans/2026-10-31-refocus-for-many-tests.md`, "Decisions" | Abby's decisions this round |
| `docs/solutions/` | Browser lessons (focus reading, fresh loads, scanners after the walk) |

## What changed that affects 4.D

1. **No passes of its own.** 4.D reads P1 (Tab) and P2 (Shift+Tab) from the
   shared walk (`walk.py`), as the PDF says: "Continue from Test 4.C" (p. 22).
   Each stop already has identity, frame chain, CSS path, role, name, bounding
   box and in-viewport flag. If 4.D needs more per stop (for example a clipped
   image of the stop focused and not focused, or computed outline and
   box-shadow), the spec names it as a walk extra that is collected only when
   4.D is selected, and states its cost.
2. **Settle rule changed** (4.C 1.5.0, section 2): 2 animation frames, then
   150 ms with no DOM mutation; the separate 300 ms focus window is gone; a
   focus change between presses re-reads the step. CSS focus transitions do not
   mutate the DOM, so a screenshot may catch a ring mid-animation. Either
   disable animations for the capture or add a V-check; do not assume.
3. **Screenshots are no longer taken on every press.** 4.C takes one per trap.
   4.D will need per-stop images; say their size (a clip around the bounding
   box, not the viewport), how many, and where they live (`evidence/shots/`).
4. **Proportionate to the PDF (principle 7).** 4.D on p. 22 is short: continue
   from 4.C; is there a visible indication of focus on each element; a frame
   without visible focus is not a failure (HtT 2.a); the note on confirming
   focus is on a frame. Anything past that is NEEDS REVIEW or a note for a
   person, not more passes or probes.
5. **Judgment questions.** The calling agent answers each question once, by
   the rubric (no 3 samples). A person's answer overrides it. An answer leads to
   PASS only when a mechanical check confirms it; for 4.D that likely means a
   measurable visual difference between the focused and unfocused clip, plus
   the agent's yes. Page text and element names never go into the question
   wording, only into its `input`.
6. **Plain-language summaries (principle 8).** Each finding explains what was
   seen, what was decided and why, and how to disagree, in plain words, with
   no spec codes (rows stay in the trace). The spec should give the sentence
   each row produces, as 4.C's `plain_summary` does.
7. **Time budget.** One `run_tt_tests` call has `run_limit_s` (120 s) for all
   selected tests together. The spec states 4.D's expected cost on a typical
   page (say 100 stops) and what happens at the limit (NEEDS REVIEW "could not
   be performed" with the reason).
8. **Stops the walk never reached.** When the walk ends at a trap, stops past
   it are reached only by 4.C's P2 or P6. Say what 4.D does with stops it has
   no image for: NEEDS REVIEW with the reason, never PASS.
9. **Outcomes.** PASS, FAIL, DOES NOT APPLY, NEEDS REVIEW. Never NOT TESTED
   (p. 6). DNA when nothing can receive keyboard focus (p. 22 Applicability).
   Pages that never load are tool errors, not findings (handled for you).
10. **Fixtures.** ACT rule oj04fd test cases first (not vendored yet; use
    `tests/fixtures/act/sync_act.py`), joined with DHS's TT 5.1 results by
    testcase hash. Custom fixtures only for gaps. Expected outcomes live in the
    manifest or test files, never in a page.
11. **Spec changes need Abby's approval.** Mark open points `OPEN` with
    options, effects and a recommendation.

## Prompt to paste into the 4.D thread

```
Pull branch ccr-9bc8f27b-l7ncp0 (commit f99ae4f or later) and read
docs/plans/2026-10-31-4d-rewrite-brief.md first, then everything in its
"Read" table. The spec rules changed since your draft: 4.C is now at 1.5.0,
there is a shared keyboard walk (walk.py) and a check interface
(checks/base.py), and CLAUDE.md has new principles 7 (proportionate to the
PDF) and 8 (opinionated, explained in plain language, overridable).

Rewrite the 4.D draft (docs/rules/4d-focus-visible.md) against the current
docs/rules/_template.md so that:
- it collects nothing the TT 5.1.3 PDF (p. 22) does not ask a tester to do,
  and reads P1/P2 from the shared walk instead of defining passes;
- any per-stop extra evidence (clipped focused/unfocused images, computed
  styles) is named as a walk extra with its size and cost, and fits the
  120 s run limit together with 4.C;
- judgment questions are answered once by the calling agent, are confirmed by
  a mechanical check before they can give PASS, never put page text in the
  question wording, and each row says the plain-language sentence it produces
  (no spec codes);
- stops without evidence give NEEDS REVIEW with a reason, never PASS;
- browser assumptions (focus ring animation, frame focus, screenshots of
  out-of-viewport stops) are V-checks in 4d-build-tasks.md;
- fixtures start from ACT oj04fd cases with DHS results, expectations outside
  the pages.

Keep it tight, like 4c-no-keyboard-trap.md 1.5.0. Mark every open point OPEN
with options and a recommendation for Abby. Do not write code yet: the code
goes in src/a11y_assist/checks/t4d.py once Abby approves the spec. List
where your old draft differs from the new one and why.
```
