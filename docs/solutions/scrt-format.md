# SCRT's file format and its quirks

SCRT (DHS's Section 508 Compliance Reporting Tool, vendored in
`third_party/scrt/` at commit `63fe687`) is a static AngularJS page. It
saves a TT 5.1.3 test record as JSON. `scrt.py` reads its files leniently
and writes our own pre-SCRT format. Every quirk below was seen in the
vendored SCRT in Chromium; the ones that matter are pinned by tests.

## The file

- A **one-item array**: `[{Product, System, Tester, Standard, FPCMapping,
  SuccessCriteria, Criteria}]`. SCRT reads `jsonData[0]`, so a top-level
  object fails at `jsonData[0].Product`. That is how pre-SCRT stays out of
  SCRT (`tests/test_scrt_tool.py`).
- The template has **61 rows**, and their test IDs equal `catalog.active_ids()`
  once spaces are removed (`" 1.A"`, `"5.F "`, `"7. D"`) (`tests/test_scrt.py`).
- **Every value is a string.** Empty is `""` or `" "`; `IssueNo` is `"3"`.
- **Results:** `Pass`, `Fail`, `Does Not Apply`, `Not Tested`; a row never
  touched is saved with `TestResult: ""`. `OptMenu1` only chooses which
  results the dropdown offers (menu1 DNA/Not Tested, menu2 Pass/Fail/DNA,
  menu3 Pass/DNA, menu4 DNA, menu5 Pass/Fail, menu6 Not Tested; the user
  guide's table leaves out menu6).
- **`Risk` is blank on every template row.** Impact comes from
  `DisabilityImpact` (Section 508 functional performance groups), which the
  view page's "Risk Score Breakdown" counts over failed rows.
- **Child issues** are extra rows with the same `TestID`, saved after the
  parent. The reader groups rows by test ID; the first is the parent.
- **Screenshots are inside the file**, as base64 data URLs in `ImageSrc` (the
  issue) and `ImageSrc2` (the remediation).
- SCRT **builds the JSON by string concatenation** from the fields it knows
  about. Any other key is dropped when a person saves the file in SCRT, which
  is one reason provenance cannot live in an SCRT file.
- A newline in a comment is saved as a literal ` \n `.
- `T_Date` is the browser's date string (`Mon Nov 02 2026 21:08:28 GMT+0000
  (...)`), not ISO.

## What SCRT's Save keeps

Checked in the vendored SCRT, 2026-11-02, while looking into why a tester's
screenshots did not stay with their file:

- A screenshot on a row with a result is saved. A screenshot on a row with
  **no result chosen** is also saved (`TestResult: ""`).
- Screenshots survive reopening the file and saving it again.
- A row whose result is **set back to "No Selection" is left out of the
  saved file entirely**, screenshot and comments included (createReport.js
  skips it). This is the only way we found to lose a screenshot
  (`test_scrt_save_drops_a_row_set_back_to_no_selection`).
- The screenshot button appears only after the row's result list is
  clicked, and SCRT hides it again on a row with no result when another
  row's list is clicked.

## A bug to know about

**Adding a child issue moves the rows below it down one, but not their
Global issue choices.** A "No" set on 4.A before a child issue is added
above it ends up on 3.A. Results, comments and locations move correctly.
A Global issue in a tester's file may therefore sit one row off if child
issues were added after it was set. `tests/fixtures/scrt/make_sample.py`
sets Global issue last for that reason.

## Driving SCRT in Playwright

- The product and tester fields are in collapsed sections: set them with an
  `input` event, not `fill`.
- Each result list has a hidden, disabled first option showing the current
  value ("Fail" on a child row). Choose by an enabled option, not by label.
