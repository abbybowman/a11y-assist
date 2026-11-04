# Roadmap

What is left to build, newest priorities first. A living list, not a log:
delete an item once it is built, and put any decision it needed into the
spec, CLAUDE.md or `docs/solutions/` where it belongs.

## Now: Tests 4 and 5, the multi-page batch and 19.A are built

Built (spec 1.0.0+, check registered, fixtures green): 4.A, 4.B, 4.C, 4.D,
4.E, 4.F, 5.A (Label provided), 5.B (Label descriptive), 5.C
(Programmatic label, from ANDI's output), 5.D (On input), 5.F (Error
identification), 5.G (Error suggestion), 5.H (Error prevention; 5.E is
obsolete in TT 5.1.3), 9.A (Bypass), 9.B (Consistent navigation), 9.C
(Consistent identification) and 19.A (Multiple ways). Judge eval (fresh agents, no scripted
answers): 43/44 Test 4 fixtures and every 5.x, 9.x and 19.A packet, no
false PASS after fixes (5.A 1.1.0's rubric change gave two, fixed: runs 12
and 13; [evals/README.md](../evals/README.md)). Every implemented test fits
one 120 s call on the realistic pages in `tests/fixtures/budget/` (the
agency page has no margin left, so the next single-page test must find
time elsewhere); pages too large to walk, or with more than 40 form
fields, are refused at once with a `no_time_limit` option
([solutions/time-budget.md](solutions/time-budget.md)). 9.A–9.C compare
the page with 1–5 other pages of the same site the caller names (up to 50 with `no_time_limit`)
(`other_pages`, the run limit +20 s each); without them they are NEEDS
REVIEW at no cost ([solutions/multi-page.md](solutions/multi-page.md));
19.A uses the same pages, then runs the site's own search live once if it
must (the one approved exception to principle 5).

Agent eval ([plan](plans/2026-10-31-agent-eval.md), [runbook](../evals/agent/README.md)):
the round 1 harness is built and tested on fixtures with a scripted model
(freeze, both arms, lock, score), and the Claude Code CLI route was
smoke-run on a fixture site with Sonnet 5.5. It has not run on real pages.
Round 1 runs on the CLI route: Abby commits `pages.txt` and freezes the
pages on her laptop, then both arms run in a cloud session. Pages with cross-site iframes now replay in full Chromium
([solutions/full-chromium-iframes.md](solutions/full-chromium-iframes.md)).

In progress: 2.A, 2.B, 2.C and 2.D (auto-playing and auto-updating content)
are built as drafts (specs 0.2.0-0.3.0, registered in `tests/drafts.py`),
with pass T, the mechanism probe and the media store; what is left before
1.0.0 is in [2c-build-tasks.md](rules/2c-build-tasks.md) (Abby's review of
the four specs, the scrolled watch, animated images below the first screen,
audio in an iframe, Windows headed Chrome). Then the visual-versus-code
cluster. Choose with the coverage map and CLAUDE.md's research rule.

Per-test leftovers live in each `docs/rules/<id>-build-tasks.md` (mostly
browser checks on Windows headed Chrome, which this Linux container cannot
run).

## Soon

- **Fixes found in agent eval round 1:** [plans/2026-11-04-post-round1-fixes.md](plans/2026-11-04-post-round1-fixes.md) (a detached-frame crash, client tool timeouts, CI for Agent B's tests). Before the next round.
- **MCP client tool timeouts (found 2026-11-04).** The Claude Code CLI in a
  cloud session cut every MCP tool call off at 60 s by default
  (`MCP_TOOL_TIMEOUT`); one `a11y_run_tt_tests` call may take up to
  `RUN_LIMIT_S` (120 s) plus 20 s per other page, or longer with
  `no_time_limit`. Check the default on a laptop's Claude Code; then either
  say in the README's setup how to raise it, or keep each call under the
  common client limits (for example by returning a run id at once and
  letting the client poll). Not checked on a laptop.

- **`tt.json` steps for 7.C and 16.B.** Each repeats the previous
  test's "How to Test" (the same PDF heading trap that scrambled 9.B, fixed
  2026-11-02; `tests/test_tt_source.py`). Fix each from its printed pages
  before building those tests, and the tt:// resource with it.
- **9.x rows no fixture triggers (optional; do with the real-page eval).**
  A coverage run (2026-11-02) reached about 91% of the 9.x check code; never
  triggered: 9.A M6 (focus did not really move), M2, the 8-candidate cap,
  a frame in the block, J1 `not_documented`/`unsure` and a documented key
  that does not work; 9.B N1, N5 and visual order reversed the other way;
  9.C C2 (a name on one page only), C5 and the all-dropped DNA; A2 (a page
  or ANDI that cannot be read) end to end; `other_pages` through the MCP
  tool, an other page that redirects off the host or fails to load, and the
  "other pages not used" note. Real .gov templates matter more than these:
  wait for the agent-eval pages, then add fixtures for whatever they show.
- **Multi-page testing, one page per call (open; Abby, 2026-11-02).**
  Current: one call records the tested page plus up to 5 other pages (50 with
  `no_time_limit`; more pages make 9.A–9.C and 19.A more reliable); only
  the tested page gets the single-page tests, the others are comparison
  pages for 9.A–9.C and 19.A, and a page too slow for its 20 s share leaves those
  NEEDS REVIEW. Proposed: test each page of a batch in full, in its own
  call, then run the multi-page tests once at the end and add their results
  to every page's report. Open: where the recordings live between calls
  (runs are kept 24 h; the comparison needs several runs at once, or the
  user's saved reports). Plan it with the next work on 9.A–9.C and 19.A
  (Multiple ways), not on its own. Part of it: **add pages to an existing
  run** (Abby, 2026-11-02). Today a second call with the suggested site map
  or other pages is a new run; 19.A's summary tells the agent to run 19.A
  alone and replace its result in the saved report. Later: append 9.A-9.C
  and 19.A to the first run's report from its kept recordings.
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
- **Merge fixture pages (only if suite time matters again).** CI's test step
  is 8 min 48 s (was 10 min 28 s before PR #5). Next saving: a simplify
  review of `tests/` lists pages worth merging; a merged page keeps every
  FAIL tied to its own instance and row, never only the page outcome (Abby,
  2026-11-02).
- **Large pages.** Pages over roughly 300 stops cannot be walked in one
  120 s call (F34, 600 links, is refused after ~5 s). Options if this
  matters for real sites: resumable runs (walk in one call, checks in the
  next), or walking P1 and P2 in parallel (headed Chrome focus in a
  background window needs checking on Windows first).
- **Starter-template leftovers.** `pyproject.toml` still says "Starter MCP
  server for the GSA MCP hackathon". (The 0.0.0.0 HTTP branch is gone; HTTP
  is loopback-only with Host/Origin checks. Authentication is still needed
  before any hosted deployment.)
- **Tidy the checks** (from the PR #3 review and a 2026-11-02 cleanup
  draft that was never approved; recheck each item against the code first;
  its principle gaps were fixed in PR #6). Sharing: the "could not be
  performed" note is typed by hand in 19 places (use
  `models.TEST_NOT_PERFORMED_NOTE`; the harness guards it); 5.G imports 5.F's private
  helpers (`t5f._errors_of`, `_field_input`, `_label`), so error pass E
  could be its own module like `labels.py`; `forms.py` exports underscore
  names; `RunContext.cache` keys are bare strings (a typo silently redoes
  work); the checks repeat findings, plain-text, question and replay code,
  and base.py's "add a check" steps say to copy a check. Last: CLAUDE.md's
  Layout lacks `egress.py`, `redact.py` and `routes.py` and says
  `verify_fix` where this list says `compare_to`; `_KEY_WORDS` (4.C) and
  `NO_INSTANCE` (4.E) look unused. Keep `traverse.py` and `pipeline.py`
  frozen; aim at the current tests, not future ones (Abby, 2026-11-02).
- **"Test a page" prompt** for operators who are not Trusted Testers: run,
  answer questions (one subagent for all of them), summarize, read
  `report_uri` and offer to save it.
- **Agent-level eval: round 1 and after** (plan: [plans/2026-10-31-agent-eval.md](plans/2026-10-31-agent-eval.md);
  runbook: `evals/agent/README.md`). Next, in order (weights and forms wording
  approved 2026-11-04): Abby commits `pages.txt` and freezes on her laptop (no model needed), then
  commits `frozen/`; Agent A, then Agent B at the start of a fresh 5-hour
  window, on the CLI route; lock, reveal, score. Later: the Ask Sage route
  (set `AGENT_API_AUTH_HEADER`; install Tavily MCP for Agent B's search),
  reported apart from CLI-route rounds; matching a failing element
  Agent B names to the key's element, plain-language rounds, repeats, the
  wording judge, the GPT and Gemini routes, DHS training pages. Also still
  to cover: a check that fails when a judge-eval agent opens files outside
  its packet (agent-eval agents get no file tools).
- **Network-level egress rules** on any host that runs the server, as a
  second layer behind the egress proxy (GSA template). Deployment work.
- **Untimed browser waits.** Headed test runs stalled for 25 to 50 minutes,
  apparently when the screen locked, waiting on a browser call with no time
  limit (a CDP command or `page.evaluate`, e.g. the settle rule's animation
  frames). A real run on such a machine would break the 120 s promise
  (`RUN_LIMIT_S`). Hosted runs are headless, so this is low priority until
  someone runs the server headed
  ([solutions/windows-chrome-results.md](solutions/windows-chrome-results.md)).
- **Egress tests in installed Chrome.** In headed Chrome 156 on Windows,
  `test_iframe_and_subresources_pointing_inside_are_refused` and
  `test_rebinding_mid_run_is_refused` fail because Chrome never makes the
  frame, subresource or later `fetch` requests, so the guard is not
  exercised. Nothing leaked: the sentinel got no hits. The default headless
  run still exercises the guard and passes. Find why Chrome skips them, so
  both browsers test the guard
  ([solutions/windows-chrome-results.md](solutions/windows-chrome-results.md)).

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
- **SCRT report files** (read, write, compare, TT review, export; plan:
  [plans/2026-11-02-scrt-io.md](plans/2026-11-02-scrt-io.md)). Fix advice for
  a read report is a separate, optional tool, reusing `explain.py`. ACRs and
  OpenACR are out of scope (product level, not page level).
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
