# Roadmap

What is left to build, newest priorities first. A living list, not a log:
delete an item once it is built, and put any decision it needed into the
spec, CLAUDE.md or `docs/solutions/` where it belongs.

## Now: Test 4 and 5.A, 5.C, 5.D, 5.F, 5.G are built

Built (spec 1.0.0+, check registered, fixtures green): 4.A, 4.B, 4.C, 4.D,
4.E, 4.F, 5.A (Label provided), 5.C (Programmatic label, from ANDI's
output), 5.D (On input), 5.F (Error identification) and 5.G (Error
suggestion). Judge eval (fresh agents, no scripted answers): 43/44 Test 4
fixtures and every 5.x packet, no false PASS
([evals/README.md](../evals/README.md)). Every implemented test fits one
120 s call on the realistic pages in `tests/fixtures/budget/` (about 110 s
and 97 s: the agency page has no margin left, so the next test must find
time elsewhere); pages too large to walk, or with more than 40 form
fields, are refused at once with a `no_time_limit` option
([solutions/time-budget.md](solutions/time-budget.md)).

Drafts (spec 0.1.0, in `tests/drafts.py`, fixtures green, judge eval 4/4):
9.A (Bypass), 9.B (Consistent navigation) and 9.C (Consistent
identification), on the new `other_pages` input (1–5 pages of the same
site, the run limit +20 s each) and the shared `site.py` read
([plans/2026-11-02-multi-page.md](plans/2026-11-02-multi-page.md),
[rules/9a-build-tasks.md](rules/9a-build-tasks.md)). Next: Abby's review
of the three specs for 1.0.0, then registration (0 s on a single-page run:
without other pages they are NEEDS REVIEW). After that: 5.B (label
descriptive) and 5.H (error prevention) would complete Test 5.

Per-test leftovers live in each `docs/rules/<id>-build-tasks.md` (mostly
browser checks on Windows headed Chrome, which this Linux container cannot
run).

## Soon

- **`tt.json` steps for 5.B, 7.C and 16.B.** Each repeats the previous
  test's "How to Test" (the same PDF heading trap that scrambled 9.B, fixed
  2026-11-02; `tests/test_tt_source.py`). Fix each from its printed pages
  before building those tests, and the tt:// resource with it.
- **Progress on long calls.** Multi-page runs take up to 120 s + 20 s per
  other page. The tool sends MCP progress per phase and page; a consumer
  agent that hands the run to a subagent sees none of it. Find a way for a
  subagent to relay progress to the main thread (Abby, 2026-11-02), or say
  in the tool description how long to expect.
- **More shared replays (deferred).** 4.A now reuses 4.D's pass W arrows
  and 4.F's pass R Enter presses when they cover what it needs
  (docs/solutions/time-budget.md). Left: 4.C's widget check (P4) and pass W
  at the same stops; 4.C reading pass R (traps inside revealed content);
  5.D and 5.F both filling fields. Build when a realistic page is over the
  limit again; the agency page is at 108 s of 110.
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
- **Agent-level eval** (plan: [plans/2026-10-31-agent-eval.md](plans/2026-10-31-agent-eval.md)).
  A model drives the tools end to end against a Playwright MCP baseline;
  outcomes scored in code with fixed weights, wording by a judge from
  another model family; 5 repeats. Next: build the harness on the
  development set with Sonnet 5.5 Gov through Ask Sage (route checked
  2026-11-01). Abby is choosing and blind-labeling real .gov pages, split
  by site; seeded faults cover keyboard traps. Open: DHS training pages
  (DHS's terms and the hackathon's "publicly available" rule), the GPT and
  Gemini routes, and how real pages are frozen for both arms. Also still
  to cover: a check that fails when a judge-eval agent opens files outside
  its packet (agent-eval agents get no file tools).
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
- **ANDI per-element data, beyond forms.** Names, descriptions and group
  labels are read for 5.C (`andi.andi_output`; ANDI does not report table
  headers). Next to try: contrast and image output for 7.x and 13.C. TT prescribes ANDI for
  about 20 tests, so matching its output matters there. Not needed for Test 4
  (4.F's note: use keyboard order, not ANDI's).
- **`read_report`**: read an agency's existing ACR or SCRT report (passed in
  by the client) and recommend fixes and re-tests, reusing `explain.py`.
- **`compare_to` on `a11y_run_tt_tests`** (verify a fix) taking a saved report, not
  a server-side run ID (runs expire after `RUN_TTL_HOURS`).
- **OpenACR export**, as a draft labelled agent-assisted; NEEDS_REVIEW maps
  to "not evaluated". TT tests map to WCAG criteria through `tt.json`
  (Appendix A); 4.A and 4.B share 2.1.1.
- **The visual-versus-code cluster** (10.x, 14.x, 15.A, 18.A; ANDI is the
  core evidence for most of it).
- **Firefox as an optional browser.** TT 5.1.3 validates Chrome and Firefox
  (Test Environment). Results are reported for the browser the report
  records and never claimed for others (e.g. Chrome 130+ tabs to scroll
  containers; ACT 0ssw9k). Not a setting change: focus reading
  (`traverse.FocusReader`) and listener lookup use Chrome's DevTools
  protocol, so Firefox needs its own reader (Playwright's Firefox has no
  CDP or isolated-world API) and every fixture rerun on it.
