# Reading ANDI's output, and pass L's traps

Lessons from building 5.A and 5.C (2026-11-01).

**ANDI's per-element output is readable.** After `andi.inject_andi`, each
element ANDI analysed has `jQuery(el).data("andi508")` with `accName`,
`accDesc`, `accGroup` (display HTML) and alert lists. `andi.andi_output`
reads them in the main world, removes ANDI's display markup (an id badge
such as `#cn2` precedes described text) and takes each alert's message from
its link's `aria-label`. ANDI reports a fieldset legend as `accGroup`; it
does **not** use table headers for a field in a cell (it reports "no
accessible name"), so pass L computes them.

**ANDI wraps the page.** Its container changes every CSS path that does not
start at an element with an id, so components matched by path lost their
ANDI output (every id-less button read "not analysed"). Mark components
with a data attribute before injecting and match by mark.

**A viewport screenshot's clip is in viewport coordinates.** Adding the
scroll offset worked for fields at the top of a page and failed for every
field below the fold (5.A f13). Fixture pages are short: give one test a
long page.

**Nearby text needs a scope.** Around a field, the next fieldset's legend
and a step list above the form made every field of a realistic form go to
the agent. Text in other fieldsets, other fields and their labels,
headings (5.C p. 27 Note 5) and text outside the field's form are not its
cues. Measure on `tests/fixtures/budget/` before trusting a fixture-only
rule: the fixtures had none of this.

**Collect order is a tool.** 5.A and 5.C collect last (`shares = -1`), so
4.F's pass R and 5.D's fill pass, which run earlier, can read fields they
reveal at the end of their own replays (`labels.read_revealed`), only when
5.A or 5.C runs (`RunContext.selected`).
