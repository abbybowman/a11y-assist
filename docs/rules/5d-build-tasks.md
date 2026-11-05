# Build tasks: 5.D

Spec [5d-on-input.md](5d-on-input.md) 1.1.0 is built (`checks/t5d.py`,
`tests/test_fixtures_5d.py`: 15 custom fixtures (F15: alike filter boxes,
one J1 for all, 1.1.0), unit tests on hand-built
evidence; the 5 Section 508 Baseline Alignment TC10.C cases in
`tests/test_baseline_cases.py`). Judge eval run 4: 14/14. Left to do:

- Calibrate `FIELD_MAX` (40) and `FIELD_SECONDS` (1.1 s) on real government
  forms; both come from fixture pages.
- After a retry, a submission that navigates away reads as navigation (the
  log is lost with the page); both are M4, so only the wording differs.

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V2 | Windows headed Chrome: ArrowDown on a closed select changes its value and fires `change` (yes in Linux headless Chromium; Mac opens the list) | Completing selects, M2 |
| V3 | `time` and `datetime-local` inputs: typing digits sets the value (checked for `date` in Linux headless Chromium, F14) | Completing dates, J3 |
| V4 | Fields in cross-origin iframes and shadow roots are completed and read back (a same-origin iframe is covered by F09) | Section 2 |
| V5 | Headed Chrome on Windows: every fixture gives the same outcome | All rows |
