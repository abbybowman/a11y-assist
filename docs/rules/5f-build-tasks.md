# Build tasks: 5.F and 5.G

Specs [5f-error-identification.md](5f-error-identification.md) and
[5g-error-suggestion.md](5g-error-suggestion.md) are drafts (0.1.0). Order of
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
| f07 several submit buttons ("Save draft", "Continue") | Q2 |
| f08 errors on leaving fields only, none on submit | Q3 |
| f09 a field that turns green (valid) after a value, nothing else | J2 not_error, A3 |
| f10 "Invalid entry" with no format given | 5.G N5 |

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | A text change outside any live region, with focus left where it was, is told apart from one inside a live region (read at the time of the change) | Notice, M7 |
| V2 | Playwright records a JS `alert` message and dismissing it returns focus where the page sends it | Notice, M6 |
| V3 | Native validation: an `invalid` event fires and the submission is blocked on Enter and on a submit button press; `validationMessage` reads the browser's text; headless draws no bubble | M2 |
| V4 | Windows headed Chrome: every fixture gives the same outcome (cannot run from Linux) | All rows |
