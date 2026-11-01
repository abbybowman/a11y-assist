# Build tasks: 5.A and 5.C

Specs [5a-label-provided.md](5a-label-provided.md) and
[5c-programmatic-label.md](5c-programmatic-label.md) are drafts (0.1.0).
Order of work: [plans/2026-11-01-forms-5a-5c.md](../plans/2026-11-01-forms-5a-5c.md).

## Fixtures

Vendored first: the nine TC10.A and four TC10.E Baseline Alignment cases,
each with expected outcomes for both tests (TC10.A is Baseline 10.A, the
programmatic side; TC10.E is 10.E, the visual side). Custom pages in
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
| f11 icon button with no name next to a field | 5.C M3 FAIL (Q2) |
| f12 a disclosure revealing an "Other, please specify" field | Q5 |

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | ANDI's `accName` and Chrome's name agree for placeholder, `title`, `aria-label`, `aria-labelledby` and label/for (TC10.A) | Q3, M3 |
| V2 | ANDI reports a fieldset legend or radiogroup label (`accGroup`), and Chrome exposes it on the group | Programmatic text, M5 |
| V3 | Table header text for a field in a cell: from ANDI or computed from the table | M5, J1 |
| V4 | A page CSP that blocks inline scripts stops ANDI; how it shows | Q3 |
| V5 | Windows headed Chrome: every fixture gives the same outcome (cannot run from Linux) | All rows |
