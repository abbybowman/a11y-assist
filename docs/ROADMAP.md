# Roadmap

What is left to build, newest priorities first. A living list, not a log:
delete an item once it is built, and put any decision it needed into the
spec, CLAUDE.md or `docs/solutions/` where it belongs.

## Now: TT Test 4 is complete

Built (spec 1.0.0+, check registered, fixtures green): 4.A, 4.B, 4.C, 4.D,
4.E, 4.F. Next: measure the time budget across all of Test 4 (below), then
choose the next TT test group.

Per-test leftovers live in each `docs/rules/<id>-build-tasks.md` (mostly
browser checks on Windows headed Chrome, which this Linux container cannot
run).

## Soon

- **Time budget across Test 4.** One `run_tt_tests` call must finish in
  `RUN_LIMIT_S` (120 s). Measured so far: a 100-link page takes 53 s for the
  walk plus 4.D. Measure all of 4.A–4.F together on
  that page, and run the 600-link fixture (4.C F34, `pytest -m slow`), which
  has never run under the 120 s limit (expected: NEEDS REVIEW "ran out of
  time").
- **Share replays.** 4.C's widget check (P4) and 4.D's widget pass W replay
  to the same stops; 4.C could also read 4.F's pass R (traps inside revealed
  content).
- **Starter-template leftovers.** `pyproject.toml` still says "Starter MCP
  server for the GSA MCP hackathon". `app.main` binds HTTP to `0.0.0.0`
  whenever `PORT` or `DATABRICKS_APP_PORT` is set, with no auth: make HTTP an
  explicit opt-in with auth before any hosted deployment (CLAUDE.md: hosted is
  the target).
- **"Test a page" prompt** for operators who are not Trusted Testers: run,
  answer questions, summarize, offer to save the report.
- **Agent evals.** A small set on fixtures where a model drives the tools:
  right calls, outcomes relayed in the tool's words, no "certified" or
  "compliant", questions answered by rubric, tokens used. Each failure becomes
  a tool-description fix plus a regression case.

## Later

- **Section 508 Baseline Alignment cases for the next tests.** The
  framework (baselinealignment.section508.gov, 148 cases) has pages with
  expected results for images and CAPTCHAs (1.1.1), images of text, sensory
  characteristics, contrast (including on hover and focus), form names, on
  input (3.2.2: form submitted, new window, focus moved), error
  identification and prevention, labels, page titles, data tables,
  headings, lists, link purpose, language of page and parts, audio-only,
  media player controls, captions and audio description. Vendor each with
  `tests/fixtures/baseline/sync_baseline.py` when its TT test is built, and
  load it in Chrome first (TC01.A-2's behaviour is broken there).

- **Scanners** (axe-core, HTML_CodeSniffer) vendored with hashes and run on
  their own fresh load after the walk ([solutions/scanners-after-the-walk.md](solutions/scanners-after-the-walk.md)).
  Licenses: axe-core MPL 2.0 (unmodified files, keep notice), HTML_CodeSniffer
  BSD 3-Clause (keep notice); NASA release review before open sourcing.
  Scanner output is evidence for spec rows; a clean scan never means PASS.
- **ANDI per-element data.** A spike: can names, descriptions, table headers
  and contrast be read out of ANDI's state in the page? TT prescribes ANDI for
  about 20 tests, so matching its output matters there. Not needed for Test 4
  (4.F's note: use keyboard order, not ANDI's).
- **`read_report`**: read an agency's existing ACR or SCRT report (passed in
  by the client) and recommend fixes and re-tests, reusing `explain.py`.
- **`compare_to` on `run_tt_tests`** (verify a fix) taking a saved report, not
  a server-side run ID (runs expire after `RUN_TTL_HOURS`).
- **OpenACR export**, as a draft labelled agent-assisted; NEEDS_REVIEW maps
  to "not evaluated". TT tests map to WCAG criteria through `tt.json`
  (Appendix A); 4.A and 4.B share 2.1.1.
- **Multi-page tests** (9.B, 9.C), then the visual-versus-code cluster (10.x,
  14.x, 15.A, 18.A).
- **Firefox as an optional browser.** TT 5.1.3 validates Chrome and Firefox
  (Test Environment). Results are reported for the browser the report
  records and never claimed for others (e.g. Chrome 130+ tabs to scroll
  containers; ACT 0ssw9k). Not a setting change: focus reading
  (`traverse.FocusReader`) and listener lookup use Chrome's DevTools
  protocol, so Firefox needs its own reader (Playwright's Firefox has no
  CDP or isolated-world API) and every fixture rerun on it.
