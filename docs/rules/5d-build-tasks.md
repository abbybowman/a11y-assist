# Build tasks: 5.D

Spec [5d-on-input.md](5d-on-input.md) 0.3.0 is a draft with no OPEN items;
it goes to 1.0.0 when its check is built and its fixtures pass. Plan:
[plans/2026-11-01-5d-on-input.md](../plans/2026-11-01-5d-on-input.md).

## Code

Built: stops carry `control` (5.D's field kind), `readonly`, `disabled` and
the radio `group` (4.C's `field` keeps its three kinds, so 4.C's J2 is
unchanged); the DOM inventory counts `form_fields` (radio groups once) and
P1 records it; the init script logs form submissions
(`traverse.submissions`), and `observe(..., submits=True)` adds the effect
"submit" (off for 4.A and 4.B, whose specs do not read it).

- Pipeline: the early stop for more than `FIELD_MAX` fields when 5.D is
  selected, beside `WalkTooLong`, with a time estimate; `no_time_limit`
  also lifts `FIELD_MAX`.
- `checks/t5d.py`: pass F, rows as `engine.Row` tables, J1–J3, the plain
  sentences; register it. `TestId` 5.D already exists.

## Fixtures

Vendored first, then custom pages for gaps. Expected outcomes live in
`tests/test_fixtures_5d.py` or the manifest, never in a page.

| ID | Page | Expected | Rows |
| --- | --- | --- | --- |
| B1 | Baseline TC10.C-3-fail-1: form submitted after exiting a field | FAIL | M4, M9 |
| B2 | Baseline TC10.C-3-fail-2: new window after exiting a field | FAIL | M5, M9 |
| B3 | Baseline TC10.C-3-fail-3: focus moved after a select item | FAIL | M6, M9 |
| B4 | Baseline TC10.C-all-pass: no change of context | PASS | M14 |
| B5 | Baseline TC10.C-ic-dna-1: no form components | DOES NOT APPLY | A1 |
| F01 | Jump menu: a select that navigates on change (F36 Example 2) | FAIL | M4, M9 |
| F02 | F01 with "Choose a state to go to its page" before the select (G13) | PASS | M4, M8 |
| F03 | Form that submits when its last field is filled (F36 Example 1) | FAIL | M4, M9 |
| F04 | Radio button that opens a new window (F37) | FAIL | M5, M9 |
| F05 | Auto-advancing phone field, no notice | FAIL | M6, M9 |
| F06 | F05 with a notice at the start of the form | PASS | M6, M8 |
| F07 | Checkbox that reveals more address fields | PASS | M7, M11 |
| F08 | Text field with an autocomplete list | PASS | M14 |
| F09 | Field inside an iframe that submits on change | FAIL | M4, M9 |
| F10 | ZIP field that submits only on a valid 5-digit value, with a pattern the fixed value fails | FAIL after J3 | M3, M4, M9 |
| F12 | Custom slider (role slider) whose change reloads the page with new results | FAIL | M4, M9 |
| F13 | Custom spinbutton that only updates a total beside it | PASS | M14 or M7, M11 |
| F11 | Notice after the field, not before ("you will be taken to the page" below the select) | FAIL | M4, M9 |

B1–B5 are vendored (`tests/fixtures/baseline/`, manifest expected 5.D
outcomes; skipped until the check is registered). Read before vendoring:
B1 never submits; it replaces the form with "Form Submitted" when focus
leaves the last name (J2, then J1). B2 opens a window only when focus leaves
the last radio option, which is why every option of a group is chosen. B3
moves focus to the button when the select changes. They load Bootstrap and
Font Awesome CSS only (missing offline; no effect on the rows).

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V6 | A popup to a host outside the allowlist (B2 opens access-board.gov; tests allow 127.0.0.1 only) still counts as a new page | M5 |
| V1 | A form submission in the HAR replay: the `submit` event fires, the request fails without hanging (`docs/solutions/egress-proxy.md`), and the top URL may or may not change | M4 |
| V2 | ArrowDown on a closed select changes its value and fires `change`: Linux headless Chromium yes (checked 2026-11-01); Windows headed Chrome not yet checked; Mac opens the list | Completing selects, M2 |
| V3 | Typing digits into `date`, `time` and `datetime-local` inputs in Chrome sets the value | Completing dates, J3 |
| V4 | Fields in same-origin and cross-origin iframes and shadow roots are completed and read back | Section 2 |
| V5 | Headed Chrome on Windows: every fixture gives the same outcome | All rows |
