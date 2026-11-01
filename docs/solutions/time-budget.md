# Where a run's time goes, and the tool's own screenshots

**Measure first.** `uv run python evals/time_budget.py [--no-time-limit] <pages>`
runs every implemented test and prints each phase's cost from steps.jsonl
(`walk` and `collected` entries carry `cost`: seconds, page loads, presses,
quick presses, slow redos). Pages: `tests/fixtures/budget/` (a realistic
agency home page and a benefits form) plus F10 and F34. For a finer split,
wrap module functions with a timer in a scratch script; don't add permanent
timers for one question.

**What it showed (2026-11-01).** About two thirds of a run is the settle
wait (~190 ms a press: two animation frames plus the 150 ms quiet window
after the press's own focus event), and about 70% of presses were replays
Tabbing back to a stop. Page loads, CDP reads and context creation are
small (as in [fresh-load-per-probe.md](fresh-load-per-probe.md)).

**The trap: our own screenshots are DOM mutations.** Playwright adds and
removes a style element for every `page.screenshot` (caret hiding), so the
mutation log saw a change at every walk step that had 4.D's images, on
pages with a text field (36 records a step on the agency page; none on F10).
Every step then looked "changed": no replay press could be quick, and 4.D
took its noise read (a second image after 150 ms) at every stop. Use
`traverse.screenshot()`, never `page.screenshot()`: it pauses the log
around the shot, counting records still pending when the pause starts and
dropping the shot's own. Test: `test_own_screenshots_are_not_page_mutations`.
Anything else the tool does to the page (marking elements, injecting
badges) needs the same care if it happens between presses.

**Replays: use `ctx.replay(keys)`.** It presses the walk's quiet presses
without the quiet window, fully settles the last press and any press the
walk saw change, and redoes the replay fully settled if focus does not end
where the walk had it (4.C spec section 2). A replay that must observe what
each press changes (4.E's reproduce replay) presses fully instead.

**The run limit.** Checks stop starting work 10 s before `RUN_LIMIT_S`; a
phase still running 2 s before it is cancelled (NEEDS REVIEW). Check
`ctx.deadline` before each replay in any new loop. P1's pace after 20
presses decides early whether the walk can finish; if not, the run is
refused and the caller may choose `no_time_limit`.

**Keys pressed outside `Traversal.press` cost a second each later.** 5.D
presses keys through `observe` (its observed actions), so the next
`Traversal.press` saw a focus change since its last read and waited the
settle rule's 1,000 ms re-read window: 0.7 s per field arrival. Call
`traversal.resync()` after pressing keys yourself. Arrivals between fields
also use quick presses where the walk saw them quiet (agency page: 5.D
16 s to 8.5 s), and an observe right after another can skip the noise
window (`noise_ms=0`, reusing the first one's noise).

**The time-limit note says what was cut, not when the run ended.** Checks
call `ctx.out_of_time()` (not `time.monotonic() > ctx.deadline`): it records
that work was cut, and only then does the result carry the "reached its time
limit" note. A run that finishes inside the 10 s reserve has no note.
