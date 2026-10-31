# Handoff: simplify the 4.C build before going further

You are picking up the a11y-assist repo (branch `claude/wizardly-hawking-19pgnu`)
from a session that built 4.C (2.1.2-no-keyboard-trap) end to end. The owner
(Abby) stopped forward work because **a full 4.C test run takes about 35
minutes and the build tests far beyond what Trusted Tester asks a human to
do**. Your job is to simplify: make 4.C fast and proportionate to the TT
process, then make the codebase lean enough to repeat for 4.A–4.F.

You will also receive a high-level architectural analysis from another thread.
It was written without full repo context. **Adjudicate it against the code, the
spec and the PDF; do not accept it or this file blindly.** Where they disagree,
check the source and say which you followed and why.

## Read first

1. `CLAUDE.md`: its principles are non-negotiable. In particular, outcome logic
   comes only from the spec; a false PASS is the worst error; you must report
   "verified (test/command)" separately from "assumed".
2. `docs/rules/4c-no-keyboard-trap.md` (spec 1.4.0) and `docs/rules/4c-build-tasks.md`.
3. TT 5.1.3, printed p. 21 (4.C), which takes about a page:
   `pdftotext -layout -f 24 -l 24 "docs/sources/Trusted Tester Test Process v5.1.3.pdf" -`
   Also p. 5 ("This test could not be performed") and p. 6 (NOT TESTED only
   where a test names it): PDF pages 8 and 9.
4. `src/a11y_assist/t4c.py`, `traverse.py`, `engine.py` and `pipeline.py`.

**Spec changes need Abby's approval.** Propose them as a 1.5.0 diff with the
reason and the expected time saved. Changes that don't affect outcomes (pure
optimization) can go ahead, but measure before and after.

## What TT 5.1.3 asks a human tester for 4.C (p. 21)

The PDF asks a human tester to:

1. Use standard navigation keys (Tab, Shift+Tab, arrows, Ctrl+Tab, etc.) to
   move through all focusable elements.
2. Decide whether focus gets trapped on an element, or in a loop in a small
   section of the page. Two notes:
   - Focus may stay inside a modal until it is closed, but check the modal
     for traps.
   - A section that requires input before focus can move on is not a failure.
3. If there is a trap, look at the help and documentation for alternate keys,
   and check that those keys work.

It passes if focus can be moved away from every element and every section
using standard keys, or using documented custom keys. The note on continuing
past a trap says to bypass it with the mouse, or reload and navigate backwards.

A human does this in a few minutes per page. They do **not** try Enter and
Space on every control, open every disclosure, arrow through every widget,
re-check each exit by tabbing to the end of the page, or wait 300 ms after
every key.

## Current state

- **Commits:** spec 1.4.0 and its code are in the final commit of this
  session (see `git log`). Earlier commits include `f9677a9` (fixes) and
  `6e8647b` (the 4.C build).
- **Size:** about 3,700 lines in `src/` and 2,700 lines of Python tests, plus
  35 custom fixture pages and 19 vendored W3C ACT cases.
- **What works:**
  - Traversal reads focus through CDP in an isolated world, so a page can't
    spoof it. It follows focus through in- and out-of-process iframes and open
    and closed shadow roots, and takes role and name from Chrome's
    accessibility tree.
  - Settle rule, inventory and the spec cap.
  - Passes P1–P6 and rows A1–A3, M1–M13 and G1–G5, with a row trace on every
    finding.
  - J1/J2 open questions as 3 samples each. `answer_questions` presses the
    documented keys or enters the values in the recorded page and re-evaluates.
  - A DHS/ACT agreement printout at the end of every pytest run.
- **Last full outcome run** (53 pages, before the 1.4.0 rule change; 35:39):
  - 33 passed and 20 failed.
  - 3 of the failures were code bugs, now fixed and re-run green.
  - The other 17 were the spec disagreements that 1.4.0 resolved (M13 deleted;
    M11 now needs the loop to hold the whole inventory). After 1.4.0, only 4
    pages were re-run: F06, F12, F30 and ACT 7dcc4ae0, all green. **The full
    suite has not been re-run since 1.4.0.**
- **Expected agreement after 1.4.0** (from the last run plus the M13 fix;
  verify): all 19 ACT cases at our expected outcome. With DHS, 16 of 17; the
  1 difference is 4b93a866, which we score DNA and DHS scores PASS (decision
  O4). With ACT, the 3 known differences are 4b93a866 on two rules, and
  b20beca9, which ACT rates inapplicable while we and DHS rate it PASS.

## Measured cost and where it goes

All measured headless on Linux, before any optimization:

| Page | Time |
| --- | --- |
| F04 (3 elements, one stuck field) | 71 s |
| F05 | 11 s |
| F11, F13 | 27–30 s |
| F16 | 59 s |
| F22 | 46 s |
| F32 | 80 s |
| 4 pages (F06, F12, F30, 7dcc4ae0) | 240 s |
| Full outcome suite, 53 pages | 35.6 min |
| F34 (600 links) | marked `slow`, never run under the new engine; estimated ≥ 10 min |

Causes, largest first (per code reading and the timings above; profile to
confirm):

1. **Every probe starts from a fresh replay.** `Collector.probe`, `p4`, `p5`,
   `p6` and `_fill_probe` each open a new context, load the recording through
   `route_from_har`, navigate, then replay the whole key prefix with the full
   settle on every press.
   - P3 alone can mean, per trap: the opposite direction, 4 arrows (stuck
     elements only), Escape, and Enter plus Space on each member (up to 25
     each). That's up to about 57 replays.
   - P5 replays the prefix for every button or trigger (up to 40), then Tabs
     to the end of the page.
   - P4 tries 4 arrows per widget, then 2 continuations to the end of the page
     for every inner stop.
2. **Settle floor.** Every press waits at least 300 ms (300 ms with no DOM
   change, and `focus_stable_ms` = 300) plus 2 animation frames. That includes
   the replayed prefix presses, whose outcome is already known.
3. **A screenshot on every step of every replay and probe**, not just P1/P2.
4. **Exit checks run to the end of the page.** Spec 1.3.0's "outside the trap"
   rule means each successful probe keeps pressing until a wrap (OUT).
5. **J1/J2 round trip.** `answer_questions` reopens the browser to press keys
   or enter values.

## Scope beyond what TT asks (candidates to cut; each needs a spec change)

| Spec item | What it costs | TT basis | Leaner option |
| --- | --- | --- | --- |
| P5 hidden content (≤ 40 triggers, every button counts) | Large on real pages | Not in p. 21 | Drop. Note "content behind disclosures not traversed" for a human, or treat it as a 4.A concern |
| P4 widget probes | Medium | "arrow keys" are standard keys, but the PDF doesn't ask for a full widget sweep | Arrow only at stops that P1/P2 already showed stuck or looping |
| P3 Enter/Space on every trapped control | Up to 50 replays per trap | HtT 2.b note 2 (input/interaction gates) | One Enter probe on the focused control, or NEEDS_REVIEW plus J2 for a human |
| J2 value entry automation | Complex code, browser reopen | Note 2 | J2 answer only, then NEEDS_REVIEW with the values for a human to try |
| "Outside the trap" = continue to a wrap | 1 traversal per probe | Not in the PDF | Exit = a stop outside the trap that isn't immediately trapped again (say 3 presses) |
| P6 mouse bypass and continuation | 1+ traversal per trap | Note under ER (continue testing) | P2 from the end already covers what follows; keep the bypass only if P2 found no stops past the trap |
| Settle focus rerun (1,000 ms) and V14 log | Code plus wait time | ACT, not TT | Keep the mutation quiet window; reconsider the focus window; the late refocus is xfail anyway |
| Recording scroll passes, infinite-scroll signs | Small | Not in TT | Keep as a note, or drop |
| Screenshot every step | Time and disk | p. 5 asks for location of failures | Screenshots only at trap steps and failures |

## Optimizations that don't change outcomes (measure first)

1. **Instrument.** Add per-phase timing (session open, prefix replay, probe
   keys, continuation, screenshots) to `steps.jsonl`. Profile F04, F16 and F32.
2. **Reuse contexts.** Use one replay context per run and a fresh page (or a
   reload) per probe instead of `new_context` plus `route_from_har` each time.
3. **Replay prefixes with a light settle.** The page is a frozen recording,
   so check that the final stop matches the recorded one instead of settling
   fully on every replayed key.
4. **Probe in place.** If a probe key changed nothing (no DOM mutation, same
   stop), continue in the same session instead of reloading for the next one.
5. **Fewer screenshots.** Skip them during replays and probes.
6. **Parallelize tests** with pytest-xdist (dev dependency only); pages are
   independent.

## Unfinished items from this session

- **Full suite after spec 1.4.0:** not re-run (only 4 pages verified).
- **F34:** not run under the new engine (marked `slow`).
- **Fixture retirements:** retire `f01`, `f02`, `f06`, `f07`, `f08` and the
  current `f35-aria-modal-escape-closes`; ACT cases cover them (see
  build-tasks). Then build the new F35, a button that refocuses 600 ms after
  blur. Its expected row is M13 (loop), or M12 if it reads as stuck.
- **V14:** the focus-log test covers the top frame only; frames and shadow
  roots are untested.
- **Windows:** headed Chrome on Windows is not run for V1–V15. Abby will do it.
- **Late refocus:** `tests/test_traverse.py::test_late_refocus_is_caught_by_the_rerun`
  is xfail by decision (spec F35 row).
- **J1 help pages:** linked help pages are not followed (README known limits).
- **Navigation during a pass:** resume is not implemented, so the outcome is
  NEEDS_REVIEW (`t4c.collect`).
- **Duplicate tests:** `tests/test_fixtures_4c.py` behavior tests overlap the
  outcome tests. Prune them once outcomes are fast.
- **Fixture helper scripts:** the copied JS helpers in fixtures were never
  moved to one shared `_lib.js`.
- **Other tests:** 4.A, 4.B and 4.D–4.F are not started. 4.D is deferred, and
  its ACT cases (oj04fd) are not vendored.
- **Code smells:**
  - `t4c.py` is about 1,100 lines.
  - `pipeline.run_tt_tests` and `resume_4c` overlap.
  - The `Inst` and `State4C` models are ad hoc.
  - The 3-sample client-judge protocol is heavy for a calling agent.
  - `traverse.FocusReader.read` is long.

## Decisions already made (don't reopen without Abby)

- **Outcomes:** never NOT_TESTED (PDF p. 6). A test that can't be performed,
  or has no spec, is NEEDS_REVIEW with "This test could not be performed" and
  the reason.
- **Exits by the opposite direction pass:** Shift+Tab is a standard key
  (p. 21 HtT 1, ER 1.a). Spec 1.1.0's M12 was dropped: DHS's FAIL on ACT
  d2f5325f is a loop in both directions in Chrome (V15).
- **V9:** content inside tabindex=-1 iframes can't be reached by Tab. It is
  not a trap, is left out of the inventory, and gets a note for 4.A.
- **V10:** the recording scrolls 5 times. A request the recording can't
  answer is a sign of infinite scroll, which gives a note and never a PASS.
- **G4:** a pass may end at a trap whose instance passes and whose
  continuation wraps.
- **P6:** after a PASS instance, continue from the exit; bypass only FAIL and
  NEEDS_REVIEW traps.
- **Stop identity:** across loads, stops match by frame chain plus CSS path.
  The same URL ignores the fragment.
- **P5 links:** a link is a trigger only with a click listener on the link
  itself.
- **1.4.0:** M13 (small section) is deleted, because ER 2 sets no size limit.
  M11 needs the loop to hold at least as many stops as the inventory.
- **O4:** 4b93a866 (only a tabindex=-1 div) is DNA; a known mismatch with DHS.
- **Fixtures:** use ACT cases first. Expected outcomes live in manifests or
  test files, never in a page, because pages are evidence an agent may read.
  The row trace is asserted for custom fixtures only.
- **Test-only flag:** tests switch off Chromium's Local Network Access check
  (`Settings.browser_args`). Real runs launch Chrome unchanged.

## Verified vs assumed (as of this handoff)

**Verified (command):**
- ruff is clean.
- The fast tests pass (51).
- The 4 pages above pass under 1.4.0.
- The ACT and fixture results quoted come from the logged runs.
- The traversal tests pass headless and headed (Xvfb).
- The CDP spoof-resistance test passes.

**Assumed (not verified):**
- The full suite is green under 1.4.0.
- Windows Chrome behaves the same.
- F34's timing.
- The cost breakdown above, which is from code reading and needs profiling.

## How to run

```bash
uv sync --group dev
uv run pytest -k "not outcome"                 # fast-ish: everything but full 4.C runs
uv run pytest -k outcome                       # 4.C end to end on fixtures + ACT (~35 min today)
uv run pytest -m slow                          # F34
uv run ruff check . && uv run ruff format --check .
```

The DHS/ACT agreement summary prints at the end of any run that includes ACT
outcome tests.

## Suggested first steps

1. Read the above and the architectural analysis. Write down where they agree
   and disagree, and check each disagreement against the code or the PDF.
2. Instrument and profile 3 pages, and report the time per phase.
3. Propose to Abby:
   - (a) the outcome-neutral optimizations, with measured savings;
   - (b) a spec 1.5.0 scope cut that matches the TT human process, with the
     expected time per page and any fixture or ACT expectation it changes.
   
   Suggested targets: under 10 s for a small fixture, and under 5 minutes for
   the full suite.
4. After approval, simplify the code toward one small traversal engine reused
   by every TT test. Keep `engine.py`'s table runner, the CDP focus reader and
   the ACT manifest scoring; they are the parts most likely to carry over to
   4.A–4.F.
