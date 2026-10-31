# Build tasks: 4.F

Work [4f-focus-order-meaning.md](4f-focus-order-meaning.md) (spec 0.1.0) needs done during the build, once Abby approves the spec. Delete each row once it exists in the repo. Delete this file when every table is empty.

## Walk changes

Uses the walk extras hook that 4.D needs (see [4d-build-tasks.md](4d-build-tasks.md)). 4.F's extras: page scroll offset, tabindex attribute, DOM order index and form group per stop; aria-haspopup per trigger. Pass R is a new shared collector (it brings back, proportionately, the hidden-content step 4.C dropped in 1.5.0); keep it separate from the walk so 4.C can opt in later.

`engine.PAGE_ROWS` has no DOES NOT APPLY page row after G1; 4.F's table 3b adds one (G4). Let a check supply its own page rows, or add the DNA row to the shared table, before building 4.F.

## Fixtures to build

No ACT rule covers 2.4.3 and DHS published no 4.F results, so all pages are custom, in `tests/fixtures/4f/`. Expected outcomes and scripted J1 answers live in the test file, never in a page.

| ID | Page | Expected | Proves |
| --- | --- | --- | --- |
| F01 | Header, nav, main, footer in DOM and visual order | PASS | M4, no signal |
| F02 | Address form whose tab order interleaves the newsletter checkboxes (Understanding failure example), scripted J1: does_not_preserve | FAIL | S5, M6 |
| F03 | tabindex=1 on a footer link (F44), scripted J1: does_not_preserve | FAIL | S1, S2, M6 |
| F04 | Two independent columns, CSS places the second first; scripted J1 by the agent: preserves | NEEDS REVIEW; with a person's answer: PASS | S3, M7 both ways |
| F05 | Left navigation after main in the DOM, shown on the left (Understanding passing example) | NEEDS REVIEW (agent) / PASS (person) | S3 from layout, M7 |
| F06 | Row of social icons reordered visually; scripted J1: does_not_matter | NEEDS REVIEW (agent) / DNA (person) | M8, G4 |
| F07 | Page with one link | DNA | A3 |
| F08 | Menu button whose menu is appended at the end of the body (F85) | FAIL with scripted J1 does_not_preserve | S6 |
| F09 | Disclosure that inserts its content right after the trigger (SCR26) | PASS | R, M4 |
| F10 | aria-modal dialog that keeps focus inside, closes on Escape | PASS | D, M3 |
| F11 | aria-modal dialog whose Tab escapes to the page behind | FAIL | D, M2 |
| F12 | Native `<dialog>` opened with showModal | PASS | M3; browser UI is not outside the page |
| F13 | 8 accordions | NEEDS REVIEW | G3 over `REVEAL_MAX` |
| F14 | Backward order differs from forward (script reorders on Shift+Tab); scripted J1: does_not_preserve | FAIL | S4 |
| 4.C f32-two-traps-injection | Forward order past a trap | NEEDS REVIEW | G3 |

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | Reading `direction` for the page and per stop; S3 mirrored for rtl | S3 |
| V2 | Native `<dialog>` showModal: Tab from the last element goes to the browser UI, then back into the dialog (4.C F10 shows the wrap) | M3 |
| V3 | DOM order index across same- and cross-origin frames, and within shadow roots | S2 |
| V4 | Full-page screenshot with injected badges lines up with the walk's page coordinates (scroll offsets per step) | Order image |
