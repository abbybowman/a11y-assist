# Plan: fixes after agent eval round 1

Status: **open; round 1 scored 2026-11-04; answering runs done
2026-11-04** (round 1: [evals/agent/README.md](../../evals/agent/README.md#results);
Agent A told to answer: [round1-answers](../../evals/judging/round1-answers/README.md)).
Fix 9 is done; 14, 17 and 18 are decided (Abby); the rest are not
started. Fix 19's inline images need Abby's approval (a CLAUDE.md rule).

**When (Abby, 2026-11-05):** after the 2.x and 3.A tests on their branch
reach review. These fixes are made while Abby labels the next judging
round blind. The harness fixes made during the round are listed at the
end. Each fix below is made after
round 1 is locked and before the next round. They are not made during
round 1: the round measures the code as it was at its start. Results and
scores: `evals/judging/round1/`. Eval plan:
[2026-10-31-agent-eval.md](2026-10-31-agent-eval.md).

## Order, from round 1 and the answering runs

Ranked by how many cells each would change on round 1's 9 pages, errors
before undecided cells of the same size. No run made a false PASS.
Evidence:
- **Round 1:** the tool scored weighted 44-47. About two thirds of its
  cells were needs review, from the time limit (35-48 per run) and the
  unanswered questions (21-26).
- **The answering runs:** with every question answered and
  `no_time_limit`, the tool scored 82, with 90/98 decided cells agreeing.
  Its 8 errors were 4.D row M8 (4), 5.B (3) and one 4.F answer. 55 cells
  were still undecided: 5.F and 5.G (18), 19.A (9), 4.F (8) and 20
  others.

1. **Fixes 4, 19, 15 and 6b: answers without a special prompt.** The
   largest gain (weighted 44-47 to 82), but only when the agent is told to
   answer.
   - Fix 4: the tool's own wording must get a real user's agent to answer.
   - Fix 19: questions that need looking must put the screenshot in front
     of the agent. It opened 2 of them in two runs, and answered every 4.F
     question "unsure".
   - Fix 15: Missions' 96 identical questions went unanswered and cost a
     correct Fail.
   - Fix 6b: a large result is saved to a file the agent reads only in part.
2. **Fix 5 (with fix 2): time.**
   - Without `no_time_limit`, 35-48 cells per run are lost. With it, NACA
     took 20 min and Missions 15.
   - It also covers the concurrency cap (one server ran 12 browser runs
     at once) and the CLI's 120 s background move (fix 2).
3. **Fix 11: 4.D row M8 at 0 px.** The largest error source left: 4 of the
   answering runs' 8 errors and 7 of round 1's 9. Results are unstable from
   run to run.
4. **Fix 17: 5.F and 5.G on a search form.** 18 undecided cells, 2 on every
   page. Decided: Does Not Apply when no input can be wrong.
5. **Fixes 10 and 14: 5.A row M3 and 5.B, the header buttons.**
   - 3 errors (5.B).
   - Today 5.A is right only because the agent answered J1; M3 would fail
     it mechanically.
   - Abby decided 5.B.
6. **Fix 18: 19.A is never decided.** 9 cells. Decided: the agent may add
   pages itself.
7. **Fix 16: 4.F.** 2 false FAILs, both the tool's: a card grid the rubric
   does not name, checkbox boxes, and a dropdown taken for a dialog. 8 cells
   undecided, mostly "unsure" answers.
8. **Fix 12: refused pages.** With `no_time_limit` Missions ran, but only
   after a refusal and a second call.
9. **Fix 1: a detached frame.** Cost a call once; a retry recovered it.
10. **Fix 13: the scorer (harness).** It changes no outcome, but it must be
    right before round 2's lock, which also locks the scorer.
11. **Fixes 3, 7 and 8: harness and setup.** No effect on accuracy.

## Fixes

### 1. A detached frame crashes a run

- **Found:** round 1, Agent A, Spot the Station (`www.nasa.gov`, 4
  cross-site iframes). `a11y_run_tt_tests` failed after 44 s with
  `Frame.frame_element: Frame has been detached.`, a tool error with no
  findings. The same page with fewer other pages, called again, finished.
  It is intermittent: it depends on whether an embed reloads at that
  moment.
- **Where:** `traverse.dom_inventory`. It walks every frame's parents to
  see whether a container hidden from the keyboard holds the frame.
  `f.frame_element()` is not guarded, unlike the frame's own `evaluate`
  just above it.
- **Fix:** treat a frame that detaches during the inventory like one whose
  script cannot run: count it in `unreachable_frames` and go on. Then look
  for other unguarded frame calls on the walk and the checks' paths
  (`frame_element`, `parent_frame`, `evaluate` on a frame), since any embed
  can reload.
- **Test:** a fixture whose iframe removes itself, or reloads, while the
  inventory runs. It must give a run with findings, not a tool error.
- **Also:** the crash left a run folder with no report
  (`results/arm-a-1/runs/20261104T125122Z-6e3198/`), though CLAUDE.md says a
  call that ends in a tool error leaves none. The pipeline should remove it,
  or keep it as a failed run the report links to.
- **Status:** not started.

### 2. MCP clients' tool timeouts

- **Found:** round 1's first Agent A attempt
  (`evals/judging/round1/attempts/`). The Claude Code CLI in a cloud
  session cut each MCP tool call off at 60 s by default, and one call took
  minutes. The harness now sets `MCP_TOOL_TIMEOUT` to an hour, but a real
  user's client may have the same limit.
- **Also found (round1-answers, 2026-11-04):** after 120 s the CLI moves a
  running MCP call to the background (`CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`).
  If the agent then ends its turn to wait, a `-p` (headless) session ends,
  and the call ends with it: Missions, NACA and KSC were lost this way. An
  interactive user's session survives, and the result arrives later as a
  notification. The harness now keeps calls in the foreground for up to an
  hour. `CLAUDE_CODE_DISABLE_MCP_TASK_BACKGROUND=1` did not stop the move.
- **Fix:** check the defaults on a laptop's Claude Code and other MCP
  clients. Then either document both settings in the README's setup, or
  keep each call under common client limits (for example, return a run id
  at once and let the client poll). Decide with fix 5.
- **Status:** not started; also in `docs/ROADMAP.md`.

### 3. CI skips Agent B's browser tests

- `tests/test_agent_freeze.py::test_agent_b_browser_rules` and
  `tests/test_agent_run.py::test_arm_b_on_a_frozen_round` skip in CI,
  because the workflow does not install Playwright MCP.
- **Fix:** add `npm ci --prefix evals/agent/node` to the workflow (Node is
  on GitHub's runners).
- **Status:** not started.

### 4. Agent A chose not to answer the open questions

- **Found:** round 1, `arm-a-1`. Its final message: "I did not answer the
  tool's open judgment questions." Every finding that needed an answer
  stayed NEEDS_REVIEW. The process depends on the calling agent answering
  them (principle 8).
- **Fix:** make answering harder to skip, in the tool, not in the eval's
  prompt (a real user's agent gets no special prompt): for example, the
  result says plainly that the findings are incomplete until the questions
  are answered, how many there are, and that answering takes one call;
  check the `a11y_run_tt_tests` and `a11y_answer_questions` descriptions.
  Then the judge eval on the new wording.
- **Measured (round1-answers):** told plainly to answer (prompt
  `answers-v1`), the agent answered 59 of 59 questions on 6 pages, and 57
  of 152 on Missions. The tool's 9-page weighted score went from 44-47 to
  82, with no false PASS. Two things to keep in mind for the new wording:
  - its visual answers were thin. Every 4.F answer on the first 6 pages
    was "unsure", with no reason given, and it opened only 2 screenshots in
    that run;
  - one answer was wrong (fix 16).
- **Status:** not started. `arm-a-2` and `arm-a-3`, unchanged repeats,
  made no `a11y_answer_questions` call either: 3 of 3 runs.

### 5. Pages that need more than the time limit

- **Found:** round 1. Of the tool's NEEDS_REVIEW findings, 40, 35 and 48
  per run were "the run reached its time limit". NACA (all 15 tests) and
  Artemis III (6 to 11 tests) were cut short in every run; Careers, the
  search page and Missions in some (5.A-5.C and others).
- **Corrected after scoring:** this was first read as calls queued in the
  server (the CLI's call durations climb by about 120 s each). The server's
  step logs say otherwise. The CLI kept each call in the foreground for
  120 s and then moved it to the background, so the next call arrived 2
  minutes later. The server started each run as it arrived (browser
  launched within 1 s of `run_start`). At most two runs overlapped, and each
  run's limit (120 s plus 20 s per other page, so 180 s with 3) counted
  from its own start. The cut-short runs used the whole limit, so these
  pages need more time than the budget allows. The overlap may have slowed
  the runs, but how much is unknown.
- **Fix:**
  - Measure one cut-short page alone first: NACA, with the archive
    restored, as a development run. If it finishes alone, the overlap
    matters.
  - Then find where the time goes (`evals/time_budget.py` on its
    `steps.jsonl`) and decide:
    - make the slow phases faster, or
    - spend the budget on the tests most likely to decide (round 1: 5.A
      and 9.A, which the key fails on every page), or
    - raise the limit for big pages, or split the run into calls the
      client can chain.
  - Also say in the tool's description that calls run side by side and
    each has its own limit.
- **Concurrency (round1-answers' first attempt):** the agent started 9
  subagents, and one server ran up to 12 browser runs at once. The
  container (4 CPUs, 15 GB) reached a load average of 51, and checks
  failed with `Page.goto` timeouts, so their tests were left NEEDS REVIEW
  for reasons unrelated to the page.
  - Cap the browser runs one server does at once.
  - A call waiting for a free slot must not use its own time limit while
    it waits.
  - The hosted runner in the results-service plan
    (`2026-11-04-results-service.md`, story T7) needs the same cap.
- **With `no_time_limit`:** NACA took 1190 s and Missions 896 s, on a
  quiet machine. These are the budget's real targets.
- **Status:** not started.

### 6. Agent A asked for a shell

- `arm-a-2` called `Bash` once, which the eval does not give (refused:
  "No such tool available"). Probably to wait for a slow call. Harmless;
  noted for the agent's behaviour, nothing to fix.

### 6b. A tool result too large for the client

- **Found:** round 1. The search page's result was over the Claude Code
  CLI's limit for an MCP result, so the CLI saved it to a file and gave the
  agent the path. The eval's agent had no file tools: `arm-a-2` went on
  without that page's results, and `arm-a-3` stopped mid-task with no
  result line. A Claude Code user's agent can read the file, but every
  client has some limit, and CLAUDE.md asks for small tool output.
- **Fix (the tool):** keep `a11y_run_tt_tests`' result under common client
  limits on a busy page (large evidence in `shared_inputs` and `run://`
  resources, not inline); measure the round 1 search page's result. The
  harness now gives both arms `Read`, allowed only in the CLI's folder of
  saved results (`cli.py`; checked: a saved result read, a repo file
  refused).
- **Status:** the harness part done; the tool part not started.

### 7. The freeze should check its own recordings (the harness)

- **Found:** round 1 twice. A typo in `pages.txt` froze NASA's "Page Not
  Found" page (status 404), and a page frozen in the cloud container had
  its HTML but none of its CSS or scripts (status -1). Both reached the
  agents before anyone noticed.
- **Fix:** `freeze.py` reports, for each page, the main document's status
  and how many of its CSS, font and script requests failed, and refuses to
  call a page frozen when the document is not a 2xx or when most of them
  failed (with a flag to accept it anyway). Show the page's title and
  heading in `freeze.json`, so a typo shows at a glance.
- **Status:** not started.

### 8. Efficiency in the score (the harness)

- Total tokens mislead: Agent B used about 930k tokens and cost less at
  list price ($0.41) than Agent A's 510k ($0.66), because most of B's were
  cache reads (re-reading its history after each small browser call) and
  most of A's costly ones were cache writes (each large tool result). On a
  subscription the limit is the usage meter, not dollars.
- **Fix:** `agent-score.md` shows each token type, the cost at list price
  and the usage-window change for each run, beside wall time. A tool call's
  duration includes its wait in the server's queue (fix 5), so the per-run
  wall time is the efficiency figure, not the sum of call durations.
- **Status:** not started.

### 9. After the lock: what Agent A would have answered (not scored)

- No Agent A run answered its open questions, so round 1 shows nothing of
  the answering half of the process. The three runs' reports keep all 119
  open questions with their evidence (`results/arm-a-*/runs/*/report.json`).
- **Plan:** a development run, never scored: an agent answers those saved
  questions with `a11y_answer_questions` on copies of the run folders, and
  the answers are compared with the revealed keys, so we learn which
  questions the agent gets right before fix 4 changes how they are asked.
  The run folders' frozen recordings are pointer files; copy each named
  recording back (its SHA-256 is in the pointer) before a step replays the
  page. nasa.gov is a development site from now on (eval plan section 3.1).
  The recordings are not in git (history rewritten 2026-11-04): restore
  Abby's archive first (`results/ARCHIVE.md`: three zips and a SHA-256
  manifest, unzipped into the repo root, git-ignored), then copy each
  pointer's recording into the copied run folder and check its hash.
- **Watch:** 4.D's J1 rubric counts "an added icon or marker, on the
  element or touching it" as yes. The key fails KSC and NACA for a focus
  square of about 4x4 px in the image's corner that does not cover the
  link. In round 1 that question was never asked (the time limit on NACA;
  on KSC the images could not be compared). If an agent answers yes, that
  is a false PASS, so check the rubric against the key's case before
  round 2.
- **Done another way (2026-11-04):** instead of answering saved
  questions, Agent A ran the pages again with prompt `answers-v1`
  (`evals/judging/round1-answers/`, `round1-answers-rest/`). The frozen
  recordings came from Abby's archive and were checked against
  `lock-1.json`'s hashes. The 4.D watch above still holds:
  - NACA's 4.D was decided Fail, which is right;
  - KSC's 4.D stayed undecided (40 image links not compared), so the
    rubric case is still untested.
- **Status:** done.

### 10. 5.A row M3 counts any button beside the field

- **Found:** round 1 scores. The key fails 5.A on all 9 pages: the site
  search field's only text is its placeholder ("Search"). The tool reads
  it as placeholder-only, but row M3 ("no button's text is beside it")
  does not fire, because the header's "Explore" button is in the field's
  picture (`buttons_next_to_it: ["Explore"]`). It goes to J1, whose rubric
  says a button counts only when its words say what to type. So J1 would
  answer `not_labeled` (FAIL), but nobody answered.
- **Fix (spec, MINOR):** M3 ignores buttons whose text could not label the
  field, by the same test the J1 rubric uses: the search words of G167,
  not "Explore", "Go" or "Submit". Research it first (CLAUDE.md), then
  `docs/rules/5a-label-provided.md`, a fixture with an unrelated button
  near a placeholder-only field, and the judge eval.
- **Status:** not started.

### 11. 4.D row M8: false FAILs at 0 px

- **Found:** round 1 scores. All of the tool's 4.D false FAILs are M8 with
  0 px changed between the on and off pictures:
  - Artemis III: "NASA", "Hide player controls", "About Orion", "Go To
    Gallery";
  - Careers: "Read More";
  - Missions: 7 links in the A-Z list.

  The key passes 4.D on all three pages. On the same frozen page the
  failing elements change from run to run, so the measurement is unstable,
  and the page's styles are not the cause. Causes to check:
  - the element is off screen or covered when captured;
  - a carousel or video moves between the shots;
  - focus moved before the "on" shot.
- **Fix:** restore the archive and look at the on, off and diff images of
  those instances in `arm-a-3`. A 0 px change on an element the key says
  shows focus means the capture went wrong, so M8 should then lead to
  NEEDS REVIEW, not FAIL. The spec already does this for M4, where there is
  no clear view. Add a check that the element is in view and unobscured
  in the "on" shot.
- **Status:** not started.

### 12. A refused page is never tested fully

- **Found:** round 1 transcripts. Missions (98 form fields) was refused in
  every run with advice to set `no_time_limit`. No run did:
  - `arm-a-1` called again without 5.D;
  - `arm-a-2` called again with six tests, then 9.A alone;
  - `arm-a-3` never called again.

  The key fails Missions on 5.C and 5.D. 5.D was never run, and 5.C was cut
  short.
- **Fix:** the refusal should test what fits instead of nothing. Run every
  test but 5.D at once, and say in the result that 5.D needs one more call
  with `no_time_limit`. Then the agent's choice costs one test, not the
  page.
- **Also:** `arm-a-3` reported 3.2.2 Fail on Spot the Station where its
  tool said NEEDS_REVIEW (the key passes it). Fix 4's wording should also
  say that a NEEDS_REVIEW is reported as needs review, not decided by the
  agent.
- **Status:** not started.

### 13. The scorer (harness), before round 2's lock

- The lock covers the scoring code, and `score` refuses to run on changed
  code. Round 1 was therefore scored as locked, and these are for round 2:
  - **Split calls:** take each TT test from the latest run whose `tests`
    included it, not only the page's latest run. Round 1's `arm-a-2`
    Missions lost 3 agreements and 1 false FAIL this way (tool weighted 41
    as scored, 43 merged). A one-function change in `tool_files`, checked
    by hand on round 1.
  - **Needs review versus not performed:** every NEEDS_REVIEW carries the
    note "This test could not be performed", so `agent-score.md` lists
    open questions and time limits as "not performed". Show each reason
    (open question, time limit, could not be performed) from the finding's
    summary, or have the checks keep the note for tests that truly could
    not be performed (principle 2).
  - **Page keys drop the query:** `?search=artemis` scores as the home
    page (`nasa.gov`). A round that has both would collide.
  - Fix 8's efficiency columns.
- **Status:** not started.

### 14. 5.B: Does Not Apply without a visible label; header menu buttons are not form controls

- **Found:** round1-answers (`evals/judging/round1-answers/README.md`). On
  Careers and the news release, the only field is the header search,
  whose only label is its placeholder. The key says 5.B Does Not Apply,
  but the tool passed it: the agent answered J1 `all_descriptive` for a
  form that included the header's menu buttons ("Explore", "News &
  Events").
- **Decided (Abby, 2026-11-04):**
  - 5.B is Does Not Apply when no field has a visible label, since there
    is no visible label to check.
  - Header menu buttons are not form elements. Count only buttons that
    act on the form's data (submit, clear).
- **Fix (spec, MINOR):** `docs/rules/5b-label-descriptive.md` and pass L
  (`labels.py`):
  - a field with no visible label (5.A M3, placeholder only) gives 5.B
    nothing to judge, so a form whose fields all lack one is Does Not Apply;
  - buttons count only when they submit or clear that form.

  Research first (CLAUDE.md), then a fixture (a placeholder-only search
  beside a menu button) and the judge eval. 5.A's row M3 (fix 10) reads
  the same buttons, so do both together.
- **Status:** decided; not started.

### 15. Many identical open questions

- **Found:** round1-answers-rest, Missions. 5.D asked 96 questions, one
  per filter checkbox, all the same ("does the text before it say that
  checking it changes the page?"). The agent answered none of them: the
  result was too large to read whole. The key fails 5.D there for exactly
  that reason, so the unanswered questions lost a correct FAIL. The page's
  152 questions also led the agent to rerun the page six times.
- **Fix:** ask once for a set of fields whose change and text before them
  are the same, with the set as instances, and apply the answer to each;
  keep `a11y_run_tt_tests`' result small (fix 6b). Then the judge eval.
- **Status:** not started.

### 16. 4.F: a card grid, a filter list's boxes, and a dropdown taken for a dialog

Both 4.F false FAILs are in the tool, not a question for the key. Abby
asked for the details; checked on the frozen recordings, 2026-11-05.

- **Missions (round1-answers-rest): J1 answered `does_not_preserve`, and M6
  failed it.** The key passes 4.F. The order image and the signals show
  three things:
  - **The results grid.** Cards in rows of three, each an image link then
    a title link. Tab goes card by card along a row, so focus "jumps back
    up" from one card's title to the next card's image (":envihab" to "3D
    Tissue Chips Image"). A grid read row by row, each card's parts
    together, preserves meaning, but J1's rubric does not name it: it
    names "columns read one after another".
  - **The footer.** Link columns read row by row ("About NASA's Mission",
    then "Join Us", then "Home"). This is the same case as the grid.
  - **The filter list is one column, not several.** Its signals ("Flyby"
    to "Ground-based Telescope") come from the checkbox boxes: "Flyby"'s
    box is at y=983 and "Ground-based Telescope"'s at 949, though "Flyby"'s
    label is above. Focus follows the list. The signal measures the box,
    not what a user sees (the label beside it).
- **Careers (round 1, `arm-a-1`): row M2, "Tab leaves the Internships
  dialog".** "Internships" is a dropdown in the Careers sub-navigation
  (`aria-expanded`, `aria-controls="basic-nav-section-one"`), not a dialog.
  On the frozen page, Enter opens it, no `dialog`, `role="dialog"` or
  `aria-modal` element becomes visible, and Tab moves through its links
  ("Internships Home", "Pathways Internships", "Fellowships"). The page
  has a hidden Popup Maker overlay (`#pum-872473`, `role="dialog"`,
  `aria-modal="false"`), the one 4.D also met on Artemis III. Pass R
  probably took it for the dialog Enter opened. To confirm, read that
  run's `evidence/4f.json` in Abby's `round1-results.zip`.
- **Fix:**
  - **J1's rubric (spec, MINOR):** add "a grid of cards or footer link
    columns read row by row, each item's parts together" as `preserves`.
  - **The O signals:** read the position of a checkbox or radio button
    from its label when the label is beside it.
  - **Pass R:** count a modal dialog only when it is `aria-modal="true"`
    (or `showModal`) at the time of the check, and only when it is what the
    trigger opened: named by `aria-controls`, or focus moved into it after
    Enter. An overlay that opens on a timer or scroll is not the
    trigger's.
  - Fixtures for each, then the judge eval on the rubric.
- **Status:** not started. Abby's key passes both pages; nothing waits
  for her.

### 17. 5.F and 5.G on a form with nothing to get wrong (site search)

- **Found:** the answering runs. 5.F and 5.G are undecided on all 9 pages
  (18 cells). On each page the tool sent the header's search form and
  could not see the server's reply in the recording ("Please submit…").
  The key says Does Not Apply on 7 pages (only the search form) and Pass
  on the forms page.
- **Decided (Abby, 2026-11-05):** a form whose fields accept any input,
  with no errors or validation (a site search: no required field, no
  format), is Does Not Apply for 5.F and 5.G.
- **Fix (spec, MINOR):**
  - `5f-error-identification.md` and 5.G, which reads 5.F's pass: decide
    Does Not Apply before sending a form that has no required field, no
    pattern or type that limits input, and no validation script.
  - Research first: which free-input forms the Baseline cases cover.
  - Then fixtures (a site search, and a search with a required field) and
    the judge eval if a question changes.
- **Status:** decided; not started.

### 18. 19.A is never decided

- **Found:** round 1 and the answering runs. 19.A was NEEDS_REVIEW on every
  page in every run. The tool finds 0-1 ways in the pages it was given and
  asks the user whether to run again with the pages it suggests (the home
  page, the site map). No user was there. In the rerun, the agent noted the
  suggestion and did not act on it. The key decides 19.A on all 9 pages.
- **Decided (Abby, 2026-11-05):** the calling agent may add pages itself.
  Any same-site page it finds can count, as long as the pages show two
  different ways, as the 19.A spec already defines them.
- **Fix:**
  - The 19.A summary tells the agent it may call again with the
    suggested pages, or other same-site pages it finds, as `other_pages`,
    instead of asking the user.
  - Update CLAUDE.md's line "Other URLs found on pages are only *suggested*
    to the user" to say they are suggested to the calling agent, which may
    pass them back (Abby, 2026-11-05). The server still never visits them
    by itself.
  - Then an answering run checks that the agent does it.
- **Status:** decided; not started.

### 19. Visual questions need the screenshot in front of the agent

- **Found:** the answering runs (`docs/solutions/judge-eval.md`). Each
  question names its images as `run://` links, and only the MCP
  read-resource tool opens them.
  - The agent viewed 2 screenshots in two runs, tried its file reader on a
    `run://` link 3 times (refused), and never opened a 4.F order image.
  - Its 8 undecided 4.F cells were mostly "unsure, cannot settle", with no
    reason. 4.D's single question and 4.A's 2 went the same way.
  - The judge eval copies images into each packet as files, so it never saw
    this.
- **Idea (Abby, 2026-11-05):** pass the screenshots along with the text for
  visual analysis, as a third round for questions still undecided, or
  alongside the second round. Options, cheapest first:
  1. **Wording:** each visual question says "open `image_a` with your MCP
     client's read-resource tool (not a file reader)".
  2. **A round with the images:** when `a11y_answer_questions` gets
     "unsure" on a question a careful tester settles by looking (principle
     8's list), it returns that question again with its image inline (MCP
     image content, downscaled), once.
  3. **Images inline from the first round,** for those questions only.
- **Conflict:** CLAUDE.md says screenshots in a question are `run://`
  links ("Keep tool output small"). Options 2 and 3 need Abby's approval
  for inline images, and a size cap per result (fix 6b).
- **Test:**
  - the judge eval with `run://` links only (no copied files), to show the
    effect;
  - then an answering run on the same frozen pages;
  - compare the "unsure" counts for 4.A, 4.D and 4.F, and check that no
    false PASS appears (an image can also mislead).
- **Status:** not started; option 1 can go with fix 4.

## Observations to decide after scoring

These describe how Agent A used the tool. They are not bugs. Whether to act
on them depends on what round 1's scores show.

- **Other pages per call.** Agent A passed 5, then 3, then 2 other pages,
  not all 8, and did not set `no_time_limit` on its first calls. 9.A–9.C
  and 19.A get more reliable with more pages. The tool's description could
  say so more plainly.
- **Other pages are read again on every call** (Abby, 2026-11-04). A frozen
  other page reuses its recording, but each call loads and reads it again
  (page units, ANDI names for 9.C); a live other page is recorded afresh
  on each call, so two calls can see two versions of a shared parent page.
  Idea: a session cache of each page's recording and reading, so a batch
  records and reads each page once (and, for the eval, both arms use the
  same live copy). It fits the ROADMAP's "multi-page testing, one page per
  call" proposal. Agent A's transcript should show first whether it cut
  other pages to save time.
- **Refusals with advice.** Confirmed from the transcripts; now fix 12.
- **Agent B and 2.4.1.** Both Agent B runs passed bypass blocks on
  landmarks alone, which the federal baseline does not accept as a
  keyboard method. The key fails 2.4.1 on all 9 pages ("No way to skip
  the top nav"). B-1 passed 8 of them, and B-2 left them for review.
- **Degraded live searches in `arm-a-1` and `arm-a-2`.** Their 19.A live
  searches ran in the container before `UPSTREAM_PROXY`, so the results
  pages loaded without scripts. NASA renders its results on the server, so
  the links are probably there; read 19.A's scores for those runs with
  that in mind (`arm-a-3` has the fix). Scored: no run decided 19.A on
  any page (all NEEDS_REVIEW), so the degraded searches changed no score.

## Done during round 1 (the harness, not the tool)

- After scoring, for round1-answers (`evals/agent/`):
  - `--prompt` (development prompt versions, `prompt_dev.py`);
  - `--no-subagents` (attempt 1 launched 9 subagents and overloaded the
    container);
  - `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` set to an hour, because on the
    `-p` route a call moved to the background was lost when the agent
    ended its turn to wait for it. Checked with a 12 s test tool.

  Round 1's arms ran with the CLI's 120 s background move.

- Recordings and screenshots out of git: `.gitignore` had excluded every
  `runs/` folder, so Agent A's tool reports were not committed, and the
  frozen recordings made the repository too big to clone. Round 1 was
  archived (Abby keeps the zips; `results/ARCHIVE.md`), the binaries were
  removed from history, the reports committed and the round locked again,
  all before any answer key. Round 2's freeze and arms keep their
  recordings outside git from the start (runbook step 4).

- Agent B's browser served one recording's failed copy of a file the pages
  share (NASA's CSS and scripts) on every page; it now routes cleaned
  copies of the recordings (`frozen-init.cjs`), with a test.
- In the cloud container, live pages loaded without CSS or scripts (an
  untrusted gateway certificate on direct connections): `UPSTREAM_PROXY`
  in `egress.py`, off by default, with tests; checked on a live NASA page.
- A new frozen recording could reuse the file name of one still in use
  (`frozen.py` named it by counting the index): fixed, with a test.
- Runs of one arm are labeled (`--label`, `results/arm-a-1/`, `arm-a-2/`),
  and each run is scored on the pages it was given, less any recorded in
  its `not_scored.json` with the reason.
- One-hour MCP tool timeout on the CLI route (`evals/agent/cli.py`).
- The CLI route's step log keeps the first 500 characters of each tool
  result, so errors show their text.
