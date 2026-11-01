# Build tasks: 5.D

Spec [5d-on-input.md](5d-on-input.md) 0.5.0 is a draft with no OPEN items;
it goes to 1.0.0 when its check is built and its fixtures pass. Plan:
[plans/2026-11-01-5d-on-input.md](../plans/2026-11-01-5d-on-input.md).

## Code

Built: stops carry `control` (the form control kind, which 4.C's J2 reads
too), `readonly`, `disabled` and the radio `group`; the DOM inventory counts `form_fields` (radio groups once) and
P1 records it; the init script logs form submissions
(`traverse.submissions`), and `observe(..., submits=True)` adds the effect
"submit" (off for 4.A and 4.B, whose specs do not read it).

- Built: the early stop over `FIELD_MAX` (a check's `cap`, checked at the
  first load; `TooManyItems`), lifted by `no_time_limit`.
- `checks/t5d.py` is built (pass F, rows, J1–J3, sentences) as a draft,
  registered only by `tests/drafts.py`; move it into `checks/__init__.py` at
  1.0.0. All 14 custom fixtures and the 5 Baseline cases give their expected
  outcome with scripted answers.

## Fixtures

Vendored first, then custom pages for gaps. Expected outcomes and scripted
answers live in `tests/test_fixtures_5d.py` or the manifest, never in a
page. F01–F14 are written (`tests/fixtures/5d/`, helpers `f01-other` and
`f09-frame`); behavior tests in the same file check that each page does what
it is meant to in plain Chrome. Outcome tests skip until the check exists.

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
| F14 | Plain form with every kind of field, read-only and disabled fields, nothing happens | PASS | M14 |
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
| V6 | A popup to a host outside the allowlist still counts as a new page: yes (B2 opens access-board.gov, tests allow 127.0.0.1 only; FAIL by M5) | M5 |
| V1 | A form submission in the HAR replay: the submission is logged and the run does not hang (F03, F09, F10; the top URL may or may not change) | M4 |
| V2 | ArrowDown on a closed select changes its value and fires `change`: Linux headless Chromium yes (checked 2026-11-01); Windows headed Chrome not yet checked; Mac opens the list | Completing selects, M2 |
| V3 | Typing digits into `date` inputs in Chrome sets the value: yes in Linux headless Chromium (F14, 2026-11-01). Chrome focuses the input's parts one by one in its shadow root (one field, `stop.group`). `time` and `datetime-local` not yet checked | Completing dates, J3 |
| V4 | Fields in iframes and shadow roots are completed and read back: a same-origin iframe yes (F09); cross-origin iframes and shadow roots not yet checked | Section 2 |
| V5 | Headed Chrome on Windows: every fixture gives the same outcome | All rows |
