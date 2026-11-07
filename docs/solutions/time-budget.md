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

**Measured** (Linux, headless; all implemented tests; before → after the
cuts of 2026-11-01, every outcome unchanged):

| Page | Before | After (4.A–4.F) | With 5.D |
| --- | --- | --- | --- |
| 4.D F10, 100 links | 60 s | 63 s | 63 s (no fields) |
| budget/agency-home (≈80 stops, 8 fields) | 153 s | 97 s | 108 s |
| budget/benefits-form (≈60 stops, 21 fields) | 158 s | 83 s | 109 s |
| 4.C F34, 600 links | ran out at 120 s | refused after ~5 s | refused |

Sharing replays (4.A arrows with 4.D's pass W, 4.A execute with 4.F's pass
R) would now save a few seconds per widget; it stays on the roadmap until a
realistic page is over the limit again.

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
phase still running 2 s before it is cancelled (NEEDS REVIEW). Call
`ctx.out_of_time()` before each replay in any new loop. P1's pace after 20
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

**Checks reuse each other's replays (2026-11-01).** Adding the draft 5.F
and 5.G put both budget pages at 111–113 s, past the 110 s soft deadline.
Timing the replay functions with a scratch wrapper (no permanent timers)
showed where: 4.A's arrow probe (11 s for one 4-tab tablist) duplicated
4.D's pass W, and on the benefits form 4.A executed the ten parts of
Chrome's native date inputs as custom controls (29 s). Now 4.D and 4.F
collect first (`shares = 1`, `RunContext.cache`) and 4.A reuses their
presses only when they cover exactly what it needs (every candidate item
reached; Enter had an effect), else it replays as before: no outcome
changed on any fixture. Date-input parts are native in 4.A (1.2.0, Abby's
approval). Agency page 108 s, benefits form 92.5 s, all nine tests.
Sharing that changes what a check visits (4.A's 20 arrow presses vs pass
W's 5 items) stays a MINOR change; this kind does not.

**Tests that compare pages cost nothing without them (2026-11-02).** 9.A,
9.B and 9.C are registered but need `other_pages`; without them they are
not performed and skip even the walk (`pipeline.needs_walk`). All fourteen
tests: agency page 108.0 s, benefits form 94.6 s. With one other page the
limit grows by `OTHER_PAGE_S` (20 s) and the agency page took 110.1 s of
140 s; measure with `time_budget.py --other`.

**Do not infer a mode from a sentinel value (2026-11-07).** 5.D and 5.F
lifted their field caps when `ctx.deadline` was infinite, which was how
`no_time_limit` used to show. When no_time_limit runs got a finite safety
stop (`MAX_RUN_S`), the caps came back silently, and a time-budget test
caught it. The run context now carries `no_time_limit` itself; check that
flag, never the deadline's value.
