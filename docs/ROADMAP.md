# Roadmap

What is left to build, newest priorities first. A living list, not a log:
delete an item once it is built, and put any decision it needed into the
spec, CLAUDE.md or `docs/solutions/` where it belongs.

## Now: TT Test 4 is complete

Built (spec 1.0.0+, check registered, fixtures green): 4.A, 4.B, 4.C, 4.D,
4.E, 4.F. Judge eval (fresh agents, no scripted answers): 43/44 fixtures, no
false PASS ([evals/README.md](../evals/README.md)). The time budget is
done: all of 4.A–4.F fit one 120 s call on realistic multi-section pages
(97 s and 83 s), pages too large to walk are refused early with a
`no_time_limit` option ([plans/2026-11-01-time-budget.md](plans/2026-11-01-time-budget.md)).
Next: 5.D On input ([plans/2026-11-01-5d-on-input.md](plans/2026-11-01-5d-on-input.md),
spec [rules/5d-on-input.md](rules/5d-on-input.md) 0.2.0), chosen from the
coverage map ([research/2026-10-31-tt-coverage-map.md](research/2026-10-31-tt-coverage-map.md)).
Then the other form tests (5.F, 5.G, the 5.A/5.C leftovers) or the
multi-page batch.

Per-test leftovers live in each `docs/rules/<id>-build-tasks.md` (mostly
browser checks on Windows headed Chrome, which this Linux container cannot
run).

## Soon

- **Share replays (deferred).** 4.C's widget check (P4), 4.D's widget pass
  W and 4.A's arrow probes replay to the same widget stops; 4.A's execute
  check and 4.F's pass R both press Enter on custom triggers; 4.C could also
  read 4.F's pass R (traps inside revealed content). With quick replay
  prefixes this saves only a few seconds per widget (it was 17 s + 18 s on
  the agency page before them), and sharing 4.A's arrows with pass W is a
  MINOR change to 4.A (pass W visits fewer items). Build it only when a
  realistic page is over the limit again; measure with
  `evals/time_budget.py`.
- **Large pages.** Pages over roughly 300 stops cannot be walked in one
  120 s call (F34, 600 links, is refused after ~5 s). Options if this
  matters for real sites: resumable runs (walk in one call, checks in the
  next), or walking P1 and P2 in parallel (headed Chrome focus in a
  background window needs checking on Windows first).
- **Confirm 4.B alternatives by pressing them.** The last judge-eval mismatch
  (4.B f02): the agent could not tell whether the named alternative does what
  the timed press does. Press it normally on a fresh replay and compare its
  effect with the timed press's (a mechanical check on J2, like 4.C's
  documented keys).
- **Starter-template leftovers.** `pyproject.toml` still says "Starter MCP
  server for the GSA MCP hackathon". (The 0.0.0.0 HTTP branch is gone; HTTP
  is loopback-only with Host/Origin checks. Authentication is still needed
  before any hosted deployment.)
- **"Test a page" prompt** for operators who are not Trusted Testers: run,
  answer questions (one subagent for all of them), summarize, read
  `report_uri` and offer to save it.
- **Agent-level eval: on hold** (plan: [plans/2026-10-31-agent-eval.md](plans/2026-10-31-agent-eval.md)).
  A model drives the tools end to end; outcomes scored by exact match in
  code, wording by a judge model; no-tool baseline; 5 repeats. Decided:
  Sonnet 5.x agent and Opus 5.5 judge as Claude Code subagents for
  development; NASA Ask Sage models for the scored runs, from the author's
  NASA laptop (key in `.env`, never committed); Phoenix later. Waiting on
  (1) DHS Trusted Tester training-course pages for the question set, and
  whether DHS's terms allow saving copies, and (2) the Ask Sage model list.
  Also still to cover: a check that fails when an eval agent opens files
  outside its packet.
- **Network-level egress rules** on any host that runs the server, as a
  second layer behind the egress proxy (GSA template). Deployment work.

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

- **Scanners** (axe-core, HTML_CodeSniffer; which tests they cover:
  [research/2026-10-31-tt-coverage-map.md](research/2026-10-31-tt-coverage-map.md)) vendored with hashes and run on
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
- **`compare_to` on `a11y_run_tt_tests`** (verify a fix) taking a saved report, not
  a server-side run ID (runs expire after `RUN_TTL_HOURS`).
- **OpenACR export**, as a draft labelled agent-assisted; NEEDS_REVIEW maps
  to "not evaluated". TT tests map to WCAG criteria through `tt.json`
  (Appendix A); 4.A and 4.B share 2.1.1.
- **Multi-page tests** (9.A, 9.B, 9.C as one batch:
  [plans/2026-11-01-multi-page.md](plans/2026-11-01-multi-page.md); 9.A is
  researched, with three questions for Abby), then the visual-versus-code cluster (10.x, 14.x, 15.A,
  18.A; ANDI is the core evidence for most of it, so the ANDI spike first).
- **Firefox as an optional browser.** TT 5.1.3 validates Chrome and Firefox
  (Test Environment). Results are reported for the browser the report
  records and never claimed for others (e.g. Chrome 130+ tabs to scroll
  containers; ACT 0ssw9k). Not a setting change: focus reading
  (`traverse.FocusReader`) and listener lookup use Chrome's DevTools
  protocol, so Firefox needs its own reader (Playwright's Firefox has no
  CDP or isolated-world API) and every fixture rerun on it.
