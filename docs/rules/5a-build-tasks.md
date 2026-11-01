# Build tasks: 5.A and 5.C

Specs [5a-label-provided.md](5a-label-provided.md) and
[5c-programmatic-label.md](5c-programmatic-label.md) are drafts (5.A 0.4.0, 5.C 0.3.0), built as `checks/t5a.py` and
`checks/t5c.py` on the shared `labels.py` (pass L), registered in `tests/drafts.py`.
Green with scripted answers: 26 TC10.A/TC10.E pairs and 12 custom pages
(`tests/test_fixtures_5a.py`, both tests in one call).
Order of work: [plans/2026-11-01-forms-5a-5c.md](../plans/2026-11-01-forms-5a-5c.md).

## Fixtures

Vendored first: the nine TC10.A and four TC10.E Baseline Alignment cases,
each with expected outcomes for both tests (TC10.A is Baseline 10.A, the
programmatic side; TC10.E is 10.E, the visual side). TC10.A-all-pass-1
(placeholder only) expects 5.C PASS and 5.A FAIL: the Baseline case judges
the name only; say so in its `differs` note. Custom pages in
`tests/fixtures/5a/` only for what they do not cover:

| Fixture | Covers |
| --- | --- |
| f01 visually hidden label only | 5.A J1 not_labeled (FAIL), 5.C PASS |
| f02 `aria-label` only, no visible text | 5.A FAIL, 5.C PASS |
| f03 date field with "(MM/DD/YYYY)" outside its label | 5.C J1 missing (FAIL) |
| f04 required marker "*" in a separate span, field not `required` | 5.C J1 missing |
| f05 Yes/No radio buttons under a question, no fieldset | 5.C J1 missing (Note 4) |
| f06 the same with fieldset and legend | 5.C M5 PASS |
| f07 phone number in three boxes, one label, two unnamed parts | 5.C M4 FAIL (F86); 5.A PASS (F82: a label for the set) |
| f08 fields in a table labelled by column headers | 5.C table association (ER 2); 5.A J1 |
| f09 icon-only search box with a magnifier image | 5.A J1 graphic |
| f10 floating label, focus-only instructions | 5.A read with focus |
| f11 icon button with no name next to a field, and a menu button with no name | 5.C M3 FAIL (every button) |
| f12 a disclosure revealing an "Other, please specify" field | Revealed fields read on 4.F's replay |

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | ANDI's `accName` for placeholder (checked in the spike), `title`, `aria-label`, `aria-labelledby` and label/for (TC10.A) | M3, M5 |
| V2 | Checked (Linux headless Chromium, 2026-11-01): ANDI reports a fieldset legend as `accGroup` (f06) | Programmatic text, M5 |
| V3 | Checked: ANDI does not report table headers for a field in a cell; the tool computes them from the table (f08) | M5, J1 |
| V4 | A page CSP that blocks inline scripts stops ANDI; how it shows | A2 |
| V6 | Checked for 4.F's pass R (f12): ANDI injected at the end of the replay analyses the revealed field. 5.D's fill pass: not covered by a fixture yet | Section 2 (revealed fields) |
| V5 | Windows headed Chrome: every fixture gives the same outcome (cannot run from Linux) | All rows |
