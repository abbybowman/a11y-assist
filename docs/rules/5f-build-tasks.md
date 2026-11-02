# Build tasks: 5.F and 5.G

Specs [5f-error-identification.md](5f-error-identification.md) and
[5g-error-suggestion.md](5g-error-suggestion.md) 1.1.0 are built
(`checks/t5f.py`, `checks/t5g.py`, registered; shared pieces in `forms.py`):
the seven TC10.D Baseline cases (14 pairs, `tests/test_baseline_cases.py`) and
17 custom pages (`tests/test_fixtures_5f.py`, both tests in one call). Judge
eval: evals/README.md runs 5 and 6.

## Fixtures

Vendored first: the seven Baseline Alignment TC10.D cases (expected outcomes
in `tests/fixtures/baseline/sync_baseline.py` and `manifest.json`). Custom
pages in `tests/fixtures/5f/` only for what they do not cover:

| Fixture | Covers |
| --- | --- |
| f01 native validation (`required`, `type=email`) | M2; 5.G J1 on the browser's message |
| f02 server-side form (`action` to a URL, no script) | A4 |
| f03 error summary at the top, focus moved to it, links to the fields | M6 with a list naming several fields |
| f04 inline errors in `aria-describedby`, announced by a live region | M6, notice by live region |
| f05 field marked only by `aria-invalid` | M3 FAIL |
| f06 password field with "Incorrect password" | 5.G N2 |
| f07 "Save draft" before "Continue" | Submit control skips the draft button |
| f11 "Go" does nothing, "Send my question" checks the form | J0 picks the other control; both attempts rerun |
| f08 errors on leaving fields only, none on submit | Text after a Tab counts |
| f09 a field that turns green (valid) after a value, nothing else; its button is "Save" | J2 not_error, A3 |
| f12 "Save" is the only button and checks the form | A plain "Save" is a submit control |
| f13 native date with `max` and `required` | Out-of-range date, native validation (M2) |
| f14 birth date checked by script, no `max` | Far-future date, J1 |
| f10 "Invalid entry" with no format given | 5.G N5 |

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | A text change outside any live region, with focus left where it was, is told apart from one inside a live region (read at the time of the change) | Notice, M7 |
| V2 | Checked (Linux headless Chromium, 2026-11-01): Playwright records a JS `alert` message; after dismissing it focus is where the page sent it (TC10.D-all-pass-1: the field) | Notice, M6 |
| V3 | Checked (Linux headless Chromium, 2026-11-01): Enter on a submit button fires `invalid` on every invalid field, blocks the submission and focuses the first; `validationMessage` reads "Please fill out this field." and "Please include an '@' in the email address. 'abc' is missing an '@'." (f01). Left: Enter in a text field, headed Chrome's bubble | M2 |
| V4 | Windows headed Chrome: every fixture gives the same outcome (cannot run from Linux) | All rows |

## Left to do

- Fields inside frames are not checked (a NEEDS REVIEW note).
- Date and time kinds other than `date` (time, datetime-local, month, week)
  are left as loaded in attempt 2.
- Scripted answers apply one answer to every J1 of a page (f03's valid
  name field is scripted "described" where an agent says no_error; same
  outcome). The judge eval checks real answers.
- V1, V4 and Enter-in-a-text-field native validation (V3) on Windows
  headed Chrome; real government forms.
