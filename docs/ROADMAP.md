# Roadmap

What is left to build, newest priorities first. A living list, not a log:
delete an item once it is built, and put any decision it needed into the
spec, CLAUDE.md or `docs/solutions/` where it belongs.

## Now: Tests 2, 4 and 5, the multi-page batch and 19.A are built

Built (spec 1.0.0+, check registered, fixtures green): 4.A, 4.B, 4.C, 4.D,
4.E, 4.F, 5.A (Label provided), 5.B (Label descriptive), 5.C
(Programmatic label, from ANDI's output), 5.D (On input), 5.F (Error
identification), 5.G (Error suggestion), 5.H (Error prevention; 5.E is
obsolete in TT 5.1.3), 9.A (Bypass), 9.B (Consistent navigation), 9.C
(Consistent identification) and 19.A (Multiple ways). Judge eval (fresh agents, no scripted
answers): 43/44 Test 4 fixtures and every 5.x, 9.x and 19.A packet, no
false PASS after fixes (5.A 1.1.0's rubric change gave two, fixed: runs 12
and 13; [evals/README.md](../evals/README.md)). Those agents had every
screenshot as a file. A real agent gets `run://` links and rarely opens
them, so these figures hold for answers with the evidence in hand (fix 19
in the post-round 1 plan). Every implemented test fits
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
round 1 ran on 9 nasa.gov pages (CLI route, Sonnet 5.5) and was scored
on 2026-11-04 against Abby's blind SCRT files
([results](../evals/agent/README.md#results)).
- **Agent A:** no false PASS. It left about two thirds of the cells for
  review, because of the time limit and its unanswered questions.
- **Agent B:** 16-20 false PASSes per run, and no Fail reported.
- **Answering runs (unscored):** Agent A was told to answer the
  questions and to use `no_time_limit`. The tool's weighted score rose
  from 44-47 to 82, still with no false PASS
  ([round1-answers](../evals/judging/round1-answers/README.md)).

nasa.gov is now a development site. Pages with cross-site iframes replay
in full Chromium
([solutions/full-chromium-iframes.md](solutions/full-chromium-iframes.md)).

Next (Abby, 2026-11-05):
1. **The 2.x tests** (2.A-2.D, specs 1.0.0) are merged (PR #12), with pass T, the
   mechanism probe and the media store
   ([solutions/watching-a-page-over-time.md](solutions/watching-a-page-over-time.md));
   their leftovers are under "Per-test leftovers" below.
   Not yet in a judging round. 3.A (flashing) has its spec at 0.1.0 and its
   research done; it can reuse pass T's frames.
2. **The post-round 1 fixes, in the plan's order**
   ([plans/2026-11-04-post-round1-fixes.md](plans/2026-11-04-post-round1-fixes.md)),
   while Abby labels the next judging round blind:
   - answers without a special prompt;
   - time and concurrency;
   - 4.D row M8;
   - the 5.F/5.G, 5.A/5.B, 19.A and 4.F fixes.
3. **The agent finishes the work, whatever prompt started it** (built
   2026-11-07, PR for `agent-follow-through`; outcome and next steps in
   the plan: the Artemis III walk bug, then ApiJudge research)
   ([plans/2026-11-06-agent-follow-through.md](plans/2026-11-06-agent-follow-through.md);
   Abby, 2026-11-06): one call finishes outstanding work, an "incomplete"
   status in the data, answers that show the picture was seen, and
   development rounds with several prompts to measure consistency.
4. **Then the visual-versus-code cluster.** Choose with the coverage map
   and CLAUDE.md's research rule.

Browser checks still to run for the built tests (mostly Windows headed
Chrome, which a Linux container cannot run) are in
[rules/_browser-checks.md](rules/_browser-checks.md); the rest of each
test's leftovers are under "Per-test leftovers" below.

## Soon

- **Artemis III's Tab walk sometimes stops early with "loop" (found
  2026-11-07).** P1 ended after 9-13 presses in 1 of 4 replays of the
  frozen page, and in development run 12, against 82 presses otherwise.
  This happened with and without the time limit. Every walk-based test
  then goes to NEEDS REVIEW (safe, but it cost run 12 six tests). Find
  which stop repeats (likely the video player) and why the loop check
  fires, then decide whether a second P1 should confirm a loop before the
  walk ends.

- **5.F row M1 is half built (found 2026-11-05).** The spec's M1 gives
  NEEDS REVIEW when "a read was unsettled or unresolved"; `t5f.py` ignores
  the result of `settle()` after the submit press, so an attempt read
  before the page settled is used as if complete. A failed read and an
  attempt that never reached the form are handled (as incomplete, page row
  G3). 5.G's N1 reads 5.F's pass, so it shares the gap. Fix in the code
  (the spec is right), with a fixture whose error text appears after the
  settle window; it can move outcomes toward NEEDS REVIEW only.
- **Fixes found in agent eval round 1:** 20 fixes, all built, in
  [plans/2026-11-04-post-round1-fixes.md](plans/2026-11-04-post-round1-fixes.md)
  (PR #14), including MCP clients' tool timeouts as long polling (fix 2: a
  call waits 45 s, then `tobi_run_status`; at most 2 runs at once) and
  pages over the time limit (fix 5). Left: shared job state for a hosted,
  multi-worker server; the agent's follow-through is the next plan.
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
- **Hosted sign-in on VAST** (`docs/plans/2026-11-06-hosted-auth.md`).
  Built and tested against a local stand-in provider (AUTH=oidc, group gate,
  runs private to their maker, audit lines); next, deploy to
  508-tobi.vast.ndc.nasa.gov and sign in from Claude Code.
- **Tidy the checks** (from the PR #3 review, a 2026-11-02 cleanup draft
  that was never approved, and the unbuilt half of the 2026-11-01
  spring-cleaning plan, removed 2026-11-05 and in git history; recheck each
  item against the code first; the principle gaps were fixed in PR #6).
  Large enough for its own plan. Rules from that plan: every outcome stays
  the same (wording may change; rerun the judge eval when question text
  does); share only what means the same thing, and keep each check's spec
  constants and the conditions that feed its page rows in the check; a
  `checks/common.py` for findings, plain text and questions, a
  `checks/js.py` for snippets, `RunContext.shot` and `replay_to` for
  screenshots and replays. Sharing: the "could not be
  performed" note is typed by hand in 19 places (use
  `models.TEST_NOT_PERFORMED_NOTE`; the harness guards it). The checks also
  put it on findings that only wait for an answer, so scoring cannot tell
  "not performed" from "needs review" (post-round 1 fix 13); 5.G imports 5.F's private
  helpers (`t5f._errors_of`, `_field_input`, `_label`), so error pass E
  could be its own module like `labels.py`; `forms.py` exports underscore
  names; `RunContext.cache` keys are bare strings (a typo silently redoes
  work); the checks repeat findings, plain-text, question and replay code,
  and base.py's "add a check" steps say to copy a check. Last: CLAUDE.md
  says `verify_fix` where this list says `compare_to`; `_KEY_WORDS` (4.C) and
  `NO_INSTANCE` (4.E) look unused. Keep `traverse.py` and `pipeline.py`
  frozen; aim at the current tests, not future ones (Abby, 2026-11-02).
- **"Test a page" prompt** for operators who are not Trusted Testers: run,
  answer questions (one subagent for all of them), summarize, read
  `report_uri` and offer to save it.
- **Agent-level eval: round 1 and after** (plan: [plans/2026-10-31-agent-eval.md](plans/2026-10-31-agent-eval.md);
  runbook: `evals/agent/README.md`). Next, in order (weights and forms wording
  approved 2026-11-04): round 1 is scored. Next is round 2, on a new site,
  after the post-round 1 fixes and fix 13's changes to the scorer. Keep its
  recordings outside git from the start (runbook step 4). Later: the Ask Sage route
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

## Per-test leftovers

From the build-tasks files, removed at 1.0.0 (2026-11-05; in git history).
None blocks an outcome: each is NEEDS REVIEW-safe today.

- **Real government pages** (with the agent-eval pages): calibrate 4.A's
  `HOVER_MAX`, `CLICK_MAX` and `EXECUTE_MAX` and 5.D's `FIELD_MAX` (40) and
  `FIELD_SECONDS` (1.1 s); how often nearby text sends a 5.A/5.C field to
  J1; 5.H's consequence words and the error words for "checked" (known
  over-match: "order" in "tab order" or "in order to" asks J1; narrowing
  is a MINOR change); 9.B's region match and 9.C's same-place pairing;
  19.A's site search on real .gov sites (W2-W4); timing of 2.x on agency
  pages with motion (one budget page measured: 153.6 s of 165 s).
- **4.A:** controls inside content that opens only on click or Enter are
  not scanned (ER Note 1 covers them); reading 4.F's pass R would add them.
- **4.B (known limits):** timing the page does not describe in words is not
  found (a tester finds it while operating; 4.A's Enter and Space presses
  cover custom controls); the timing words are English only.
- **4.C:** a late-refocus fixture (refocus 600 ms after blur, no DOM
  change) once the xfail in `tests/test_traverse.py` is settled.
- **4.D and 4.F:** run 4.C's f19 (cross-origin frame), f24 (open shadow
  root) and f32 (two traps) for 4.D, and f32 for 4.F (expected NEEDS
  REVIEW: the forward order past a trap is unknown). Shared replays
  (4.D's pass W with 4.C's P4; 4.C reading 4.F's pass R) are under "More
  shared replays".
- **5.A, 5.C:** fields in frames and shadow roots are not read (frames: a
  NEEDS REVIEW note); a field revealed by 5.D's fill pass is wired but has
  no fixture.
- **5.B:** icon-only buttons are left out (pass L has no picture of
  buttons); add one if real pages show icon buttons with misleading names.
- **5.D:** after a retry, a submission that navigates away reads as
  navigation (both M4; only the wording differs).
- **5.F, 5.G:** fields in frames are not checked (a NEEDS REVIEW note);
  `time`, `datetime-local`, `month` and `week` fields are left as loaded in
  attempt 2.
- **2.A-2.D:** ER 3's shortlist (6.A, 7.A, 7.E, 12.D, 13.A, 13.B, 13.C,
  18.A): until each is built, a working mechanism is NEEDS REVIEW (E3),
  never PASS. 2.C J1's wording when the mechanism is page text naming a
  key; 2.B J1 for content below the first screen needs a crop (judge eval
  runs 15, 16; rerun it after either). A large media file fetched in
  several byte ranges is not reproduced in a test; real YouTube and Vimeo
  embeds on a normal network are NEEDS REVIEW (2.A A2).

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
- **Hosted results service and dashboard** (proposed; plan:
  [plans/2026-11-04-results-service.md](plans/2026-11-04-results-service.md)):
  a second, hosted MCP server that keeps results inside NASA, with a
  dashboard for site owners, Trusted Testers and web governance. Its MVP
  was cut for the GSA hackathon demo (Nov 20).
- **`compare_to` on `tobi_run_tt_tests`** (verify a fix) taking a saved report, not
  a server-side run ID (runs expire after `RUN_TTL_HOURS`).
- **OpenACR export**, as a draft labelled agent-assisted; NEEDS_REVIEW maps
  to "not evaluated". TT tests map to WCAG criteria through `tt.json`
  (Appendix A); 4.A and 4.B share 2.1.1.
- **The visual-versus-code cluster** (10.x, 14.x, 15.A, 18.A; ANDI is the
  core evidence for most of it). Research on what the browser, ANDI,
  scanners and image libraries can settle, and on ApiJudge:
  [research/2026-11-07-visual-judgment-and-apijudge.md](research/2026-11-07-visual-judgment-and-apijudge.md).
- **Answer once per site (Abby, 2026-11-07).** A judgment about the same thing on several pages of a site is made once and reused until something differs, as 9.A-9.C already do with repeated content. It covers per-image questions (7.E, 7.A, 13.C text in images), and media: videos, GIFs and other moving content in 2.A-2.D and 3.A. Key it by content (the image or media bytes' hash, and the question's spec version), never by URL alone. A new scan reuses an answer only when the hash and spec version match, and says so in the finding. A person's answer beats a reused model answer. Hosted, this can outlive one server session (a store beside run state, with an expiry); stdio keeps it in memory (`pagecache.keep_read`). Plan first: what is stored, for how long, and who may see answers from another user's runs.
- **A review view for people: parked (Abby, 2026-11-07).** Before building one, decide what is most usable and accessible for people who review results, answer open questions and add what the tool missed. One idea: open the recorded page (the HAR replay) beside the pre-SCRT file, so the reviewer can mark it up and answer comments in place. Whether that works outside Claude's artifacts is unknown. Not near term: reliability of the tool itself comes first.
- **13.C: ANDI's rounding (found 2026-11-07).** ANDI's contrast ratios equal exact WCAG maths rounded to 2 decimals (444 pairs checked), but ANDI compares after rounding, so 4.495-4.499 counts as 4.5 and PASS. WCAG Understanding 1.4.3 and the ICT Baseline say ratios are not rounded; the TT says to use ANDI's number. Decide in the 13.C spec; principle 3 suggests NEEDS REVIEW for that band. axe-core 4.14 compares unrounded. Details: research/2026-11-07-visual-cluster-per-test.md (13.C).
- **18.A Resize text: decide before its spec (found 2026-11-06).** The TT
  says only "use built-in browser zoom functions to resize the text to at
  least 200%" (pp. 74-75, HtT 1) and names no window size; its environment is
  desktop only (Test Environment, pp. 3-5: Windows "desktop mode"; About,
  pp. 1-3: mobile platforms "must be evaluated using other testing
  procedures"). Zoom halves the layout
  width, so our 1280 px window at 200% lays out at 640 CSS px (often the
  site's tablet or mobile layout), and a page can pass in a 1920 px window
  and fail in ours. Open:
  - **Which windows.** Proposed: the default 1280 px (a 1920x1080 laptop at
    150% Windows scaling) and a smaller desktop window near 1024 px (512
    CSS px at 200%).
  - **A failure only in the smaller window:** FAIL, or NEEDS REVIEW with a
    note, since the TT names no size.
  - **How to zoom: real browser zoom, checked 2026-11-07.** A two-file Chrome extension of our own (no content script, `tabs` permission only), driven through its service worker with `chrome.tabs.setZoom`, gives real 200% zoom in headless Chromium (`channel="chromium"`) on Linux. The half-width, DPR 2 stand-in matches it on layout width, DPR, media queries and most boxes, but not native form controls (text inputs 180×22 vs 185×21 CSS px), which F80 is about. So use real zoom. Per-tab zoom resets on navigation: set it after each load. Still to check: HAR replay in a persistent context (extensions need one), and Windows Chrome. Do not use the `playwright-zoom` npm package: its content script lets any page script change the zoom. Details: [research/2026-11-07-visual-cluster-per-test.md](research/2026-11-07-visual-cluster-per-test.md) (18.A).
  - **Functionality and time.** ER 3 ("all functionality is available"):
    compare the keyboard stops at 100% and 200% (a control gone or
    unreachable, such as a menu behind a hamburger button). A second walk
    costs about 46 s on the agency page, which the 120 s budget does not
    have: an allowance like `OTHER_PAGE_S`, or a lighter walk.
  - **Not in scope:** a phone-width check (320 CSS px) is WCAG 2.1's 1.4.10
    Reflow, not Section 508; at most a separate, clearly labelled extra.
  The report records the window (`Versions.display`: viewport, inner size
  and device pixel ratio), so results at different sizes can be told apart.
  3.A's spec should name its window too: the flash threshold is an area
  (341 x 256 px at 1024 x 768).
- **Firefox as an optional browser.** TT 5.1.3 validates Chrome and Firefox
  (Test Environment). Results are reported for the browser the report
  records and never claimed for others (e.g. Chrome 130+ tabs to scroll
  containers; ACT 0ssw9k). Not a setting change: focus reading
  (`traverse.FocusReader`) and listener lookup use Chrome's DevTools
  protocol, so Firefox needs its own reader (Playwright's Firefox has no
  CDP or isolated-world API) and every fixture rerun on it.
