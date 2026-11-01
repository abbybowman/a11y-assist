# Build tasks: 5.F and 5.G

Specs [5f-error-identification.md](5f-error-identification.md) (0.4.0) and
[5g-error-suggestion.md](5g-error-suggestion.md) (0.3.0) are drafts, built as
`checks/t5f.py` and `checks/t5g.py` and registered in `tests/drafts.py`.
Fixtures green with scripted answers: the seven TC10.D cases (14 pairs) and
`tests/test_fixtures_5f.py` (11 pages, 22 pairs). Order of
work: [plans/2026-11-01-forms-5f-5g.md](../plans/2026-11-01-forms-5f-5g.md).

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
| f09 a field that turns green (valid) after a value, nothing else (its button is "Update": "Save" is a skip word) | J2 not_error, A3 |
| f10 "Invalid entry" with no format given | 5.G N5 |

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | A text change outside any live region, with focus left where it was, is told apart from one inside a live region (read at the time of the change) | Notice, M7 |
| V2 | Checked (Linux headless Chromium, 2026-11-01): Playwright records a JS `alert` message; after dismissing it focus is where the page sent it (TC10.D-all-pass-1: the field) | Notice, M6 |
| V3 | Checked (Linux headless Chromium, 2026-11-01): Enter on a submit button fires `invalid` on every invalid field, blocks the submission and focuses the first; `validationMessage` reads "Please fill out this field." and "Please include an '@' in the email address. 'abc' is missing an '@'." (f01). Left: Enter in a text field, headed Chrome's bubble | M2 |
| V4 | Windows headed Chrome: every fixture gives the same outcome (cannot run from Linux) | All rows |

## Left to do

- Time pass E on `budget/agency-home.html` and `budget/benefits-form.html`
  (`evals/time_budget.py --drafts`).
- Judge eval on the 5.F and 5.G packets (`evals/judge_eval.py prepare OUT 5.F,5.G`).
- Fields inside frames are not checked yet (a NEEDS REVIEW note).
- Scripted answers apply one answer to every J1 of a page, so f03's name
  field (given a valid "abc") is scripted "described" where an agent should
  say no_error; the outcome is the same. The judge eval checks the real
  answers.
