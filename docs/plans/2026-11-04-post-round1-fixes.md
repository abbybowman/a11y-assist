# Plan: fixes after agent eval round 1

Status: **open; round 1 scored 2026-11-04** (results in
[evals/agent/README.md](../../evals/agent/README.md#results)). Fixes 1-13
are not started; the harness fixes made during the round are listed at
the end. Each fix below is made after
round 1 is locked and before the next round. They are not made during
round 1: the round measures the code as it was at its start. Results and
scores: `evals/judging/round1/`. Eval plan:
[2026-10-31-agent-eval.md](2026-10-31-agent-eval.md).

## Order, from round 1's scores

Ranked by how many scored cells each would have changed in round 1. Agent
A made no false PASS. Its only errors were false FAILs, and about two
thirds of its cells were needs review. The fixes that turn needs review
into correct answers come first; the one that removes false FAILs comes
next.

1. **Fix 5: pages that need more than the time limit.** 35-48 cells per
   run. Every test on NACA in all three runs; most on Artemis III. Key Fails
   lost this way include NACA's 4.A, 4.D and 9.A.
2. **Fixes 4 and 9: the unanswered open questions.** 21-26 cells per run.
   round1-answers measured it: told to answer, the agent raised the tool's
   9-page weighted score from 44-47 to 82, with no false PASS. Fix 15 (96
   identical questions) and fix 16 (4.F J1, one false FAIL from an answer)
   came out of it.
   Run fix 9 first: it shows which answers would be right before fix 4
   changes how the questions are asked.
3. **Fix 10: 5.A row M3 counts any button.** The key fails 5.A on all 9
   pages, and the tool decided none. With M3 fixed, every page whose search
   field is read fails mechanically, with no question.
4. **Fix 11: 4.D row M8's 0 px false FAILs.** 7 of Agent A's 9 errors.
   Results differ run to run on the same frozen page.
5. **Fix 14: 5.B and header buttons** (with fix 10, which reads the same
   buttons). 2 cells in round1-answers.
6. **Fix 12: refused pages are never tested fully.** Missions in 0 of 3
   runs; its key Fails (5.C, 5.D) were never tested.
7. **Fix 6b: result size; fix 1: a detached frame.** Each cost a page or a
   call once, and a retry recovered it.
8. **Fix 13: the scorer (harness).** No outcome changes, but it must be
   right before round 2's lock, which also locks the scorer.
9. **Fixes 2, 3, 7 and 8: harness and setup.** No effect on accuracy.

**For Abby (4.F, Careers):** `arm-a-1`'s tool failed 4.F (row M2: Tab left
the "Internships" dialog onto the page behind it), and the key passes it.
Is that dialog modal? If not, M2 should not apply to it. The spec row
needs the answer before any change.

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
- **Fix:** check the default on a laptop's Claude Code and other MCP
  clients. Then either document how to raise it in the README's setup, or
  keep each call under common client limits (for example, return a run id
  at once and let the client poll).
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
- **Status:** not started.

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

### 16. 4.F J1 and a list laid out in columns

- **Found:** round1-answers-rest, Missions. Tab goes along the rows of a
  filter list laid out in columns, so focus "jumps back up" between
  columns. The agent answered J1 `does_not_preserve`, and the tool failed
  4.F, where the key passes it. This is the only error in these runs that
  came from an answer.
- **For Abby:** does a grid or multi-column list read row by row preserve
  meaning? If so, add it to J1's rubric as a "preserves" example, then run
  the judge eval.
- **Status:** waiting for Abby.

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
