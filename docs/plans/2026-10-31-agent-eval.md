# Plan: agent-level evaluation

Status: **round 1's harness is built and tested on fixtures with a scripted
model; it has not run on a real model or real pages yet.** Runbook:
`evals/agent/README.md`. Section 12 lists what is built and what is not.

## 1. What it measures

Real users won't call this server directly: an agent will. This eval puts
a model in that agent's place and compares two arms:

- **Agent A (tool arm):** a model with this MCP server. A person asks it to
  test pages. It runs the tests, answers the open questions the tool hands
  back, and reports to the person.
- **Agent B (baseline arm):** the same model, the same task and the same
  pages, with Playwright MCP and Tavily web search instead of this server. It
  chooses its own way to test.

Both arms are scored against a certified Trusted Tester's answer keys, on
three things: accuracy (above all, no false PASS), tokens and wall time. That
shows what the server adds over a capable agent with a browser. The
hackathon does not require an agent-level eval. It is the direct evidence
for the hackathon criterion that tool names and descriptions be "precise
enough for an LLM to select them without ambiguity."

Words used in this plan:

- **Scoring:** code (`evals/scoring.py`) that compares results with the
  tester's SCRT files. No model takes part.
- **Wording judge:** a model from another family that grades how an agent's
  final message reports its findings (section 9). It never sees the answer
  keys and never scores outcomes.
- This eval is neither of the two existing evals. A **judging round**
  (`evals/judging.py`) drives the tool with a script while one agent fills
  in question packets: it measures the tool without an agent driving it. The
  **judge eval** (`evals/judge_eval.py`) tests each spec's open questions on
  our fixtures. Inside the product, "judge" (`JUDGING_MODEL`,
  `judgment.py`) means whoever answers the open questions; in this eval
  that is Agent A.

## 2. The two arms

- **The same for both arms:** model, task prompt (word for word), the
  frozen tested pages and the live rest of their site (section 6), route
  (section 7), the optional helper tool, and a tool that reads MCP
  resources (section 7.3).
- **Agent A** has only this MCP server, which it may run with
  `no_time_limit`: the eval wants every test's full result.
- **Agent B** has Playwright MCP (`@playwright/mcp`, version pinned and
  recorded) and web search. A capable agent would look up guidance, and the
  test sites publish no accessibility reports a search could find. On a
  route whose models have no web search of their own (Ask Sage), search is
  Tavily MCP (not installed yet). On the CLI route it is the CLI's
  WebSearch and WebFetch for guidance (W3C, WebAIM and so on), with
  WebFetch refused on the tested site's hosts (Abby, 2026-11-04): Agent B
  reaches that site only through its browser (section 6). Agent A gets no
  web search or fetch: the hypothesis is that the tool's researched,
  mechanical procedure beats an agent free to look anything up. Agent B can
  open a page, press keys and read the page, so it has a fair chance to
  run each test without this server's procedure. Its tools are given up
  front rather than "ask for what you need," so every run has the same
  tools.
- **Agent B's browser** is Playwright's full Chromium, the same build as
  Agent A's server (`--executable-path`), headless. It runs with no sandbox
  (our server's Playwright default) and with `--no-webmcp`, so a tested page
  cannot register tools for it. Playwright MCP writes automatic page
  snapshots to a file that Agent B cannot open (it has no file tools), so
  Agent B reads pages with `browser_snapshot`, which returns the snapshot
  inline.
- **Agent A's browser** is the server's own: the headless shell, or full
  Chromium for pages with cross-site iframes
  (`docs/solutions/full-chromium-iframes.md`).
- **"Needs review to everything"** is computed, not run: every result is
  scored as NEEDS_REVIEW. Both arms should beat it clearly.

## 3. Pages and answer keys

### 3.1 Real .gov pages, labeled blind (the scored evidence)

- **Abby picks the pages, not the tool.** If pages were found by running
  A11y Assist, the set would hold only failures it already catches. Claude
  may help find *candidate* pages with features the tests exercise (menus,
  dialogs, carousels, forms) on public .gov sites, but must not run the TT
  tests on them.
- **Several pages per site:** at least 7, so 9.A-9.C and 19.A have pages to
  compare. Every page of a round is compared with all of the round's other
  pages on its host.
- **Labeled blind, by commit and reveal.** Abby tests each page with the
  SCRT and commits `pages.txt` (each URL with the SHA-256 of its SCRT file)
  when testing begins, not earlier. Both arms run and their results are
  locked before her SCRT files are added (section 5).
- **Split by site, not page.** Pages on one site share templates, and so
  share bugs. Once a site has been used in a round, it is a development
  site: its pages can be used to fix the code, and rows they never triggered
  can be exercised on a doctored copy (a seed, 3.2). Only untouched sites go
  in the final round.
- A second certified tester labels a subset, if one is available.

### 3.2 Seeded faults on real pages

Real keyboard traps are rare, so real pages alone cannot show "no false
PASS" for 4.C. Seeds fill that gap: a copy of a frozen real page with one
fault injected, confirmed by Abby by hand and reported as planted. Seeds
chosen by the people who wrote the detector share its blind spots, so:

- **Seeds come from sources independent of this code:** W3C failure
  technique F10, focus-trap bugs reported against widely used libraries, and
  seeds written by a different model family that is given only the TT text
  and asked for traps an automated tester would miss.
- **Each seed records its source**, and results are reported by source. The
  independent group is the one that counts.
- **A missed seed must end NEEDS_REVIEW.** A PASS on any seed is a false
  PASS.

### 3.3 Other sources, reported separately and never pooled

- **W3C ACT cases** with DHS's verdicts (`tests/fixtures/act/manifest.json`)
  are a warm-up only. They have been public with their answers for years, so
  they may be in models' training data, and the specs were written with
  them in view. No claim rests on them.
- **DHS training-course pages**, only if both of these hold: DHS's terms
  allow saving copies, and the hackathon organizers confirm the pages count
  as "government data that are already publicly available." Nothing else
  waits on them.

## 4. Rounds

### 4.1 Round 1

Nine pages from one site, `evals/judging/round1/`. Its purpose is to show how
far along the tests are and where accuracy needs work most.

- **One run per arm.** The token budget doesn't allow repeats yet. Round 1's
  logged cost decides whether later rounds repeat, or use smaller sets.
- **One conversation per arm for all 9 pages**, because a real person would
  ask once. If an arm runs out of context, that is recorded as its result,
  not worked around.
- **The task prompt** is in 4.3.
- **Scored per TT test** (Agent A only) **and per WCAG 2.0 criterion**
  (both arms; section 8).
- **No wording judge.** Both arms' transcripts and final messages are kept
  in full, so the wording judge can run on them later.

### 4.2 Later rounds

- **Plain-language tasks:** the way a non-tester asks ("can a keyboard user
  get stuck anywhere on this page?"), phrased without words from a page's
  file name, scored the same way. These need a question set with known
  answers, drawn from the fixture tables already asserted in `tests/` (so
  no answer key is written twice) and from new real sites.
- **Behavior questions** that no answer key covers, reported separately:
  answering an open question, saying "unsure," ignoring instructions
  injected in a page, never saying "compliant," and reporting a refused URL
  instead of inventing findings.
- **Repeats** (up to 5 per arm) to measure consistency, if the budget allows.
- **Wording judge** (section 9) and **other model families** (section 10).
- **Freeze before the final round:** questions, prompts, weights, scoring
  code and labels, recorded with a commit in `docs/hackathon/evaluation.md`.
  The final round is the latest round before the code freezes for hackathon
  judging. It uses sites never used before, and nothing is changed after
  seeing its results. The headline figures come from that round only.
- **Every round's results stay in the repo** under `evals/judging/<round>/`,
  including the early ones, to show progress. Testing is to improve, not
  only to prove.

### 4.3 Round 1's task prompt

Both arms get the same text. It contains no TT procedure. It has no
plain-language explanation of the criteria (round 1 measures doing the
tests; a later round measures plain-language tasks) and no links to W3C
Understanding pages (those are the WCAG 2.2 versions). It says:

- Test these pages (the round's URLs) against **WCAG 2.0** Level A and AA,
  the version Section 508 incorporates. Test only the criteria listed, not
  WCAG 2.1 or 2.2.
- **The 14 criteria the tool covers in full:** 2.1.1, 2.1.2, 2.4.1, 2.4.3,
  2.4.5, 2.4.7, 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.3.1, 3.3.2, 3.3.3 and 3.3.4.
- **1.3.1, 2.4.6 and 4.1.2, for the labels of form fields only.** The tool
  covers only that part of those criteria (5.B and 5.C); their other TT
  tests (tables, headings, other controls) are not built yet.
- **The possible results:**
  - **Pass**;
  - **Fail**, naming each failing element;
  - **Does not apply**;
  - **Needs review**: unsure, or a person should check.

  Needs review is always allowed, and a wrong Pass is the worst error.
- **End with one machine-readable line** holding a result for each page and
  criterion, plus the failing elements for each Fail, for example
  `RESULT: {"https://…/a": {"2.1.1": {"result": "FAIL", "elements": ["…"]}, …}, …}`.
  A missing or malformed line, or a missing entry, scores as wrong.

The criteria list is generated from the requirements of the tests in
`checks.REGISTRY` (`catalog.py`), never typed by hand. The wording,
including the forms scope, is `evals/agent/prompt.py` (`round1-v1`,
approved by Abby, 2026-11-04).

## 5. Steps of a round, in commit order

1. **Start.** Abby commits `pages.txt` when testing begins.
2. **Freeze** (section 6). The tested pages are recorded once from the
   live site; Abby compares each frozen page's footer timestamp with her
   own testing.
3. **Run Agent A**, then **Agent B**, close together (section 6: other
   pages of the site are live, and the site may change).
4. **Lock.** `evals/judging.py lock` covers both arms' results, transcripts,
   step logs and live-page records, the frozen pages, and the code commit.
   Then commit.
5. **Reveal.** Abby adds her SCRT files to `keys/` and commits.
6. **Score** (section 8).

## 6. Frozen tested pages, live rest of the site (Abby, 2026-11-04)

- **The tested pages are frozen, for both arms.** `evals/agent/freeze.py`
  records each page of `pages.txt` once, as a live run records it (the
  allowlist and every redirect hop checked, scrolled to load lazy
  content), into `<round>/frozen/`. Neither arm can load a tested page's
  live version, so both test the same copy as the tester's key.
- **Every other page of the tested site's hosts is live, for both arms:**
  site maps, search results, any route an agent tries. 19.A asks whether a
  page can be reached more than one way, and only the live site can answer
  an agent's own search or route. A frozen search page answers only the one
  search the freeze made.
- **Agent A:** the server's `FROZEN_PAGES_DIR` setting (`frozen.py`) in
  "tested_frozen" mode. The tested page must be frozen (otherwise a tool
  error, with nothing fetched); other pages and 19.A's search are recorded
  live under the server's usual rules (allowlisted, the tested page's host,
  every redirect hop checked), each saved in the run. Every report records
  `frozen_pages`, and each other page says whether it was frozen. It is a
  server setting, not a tool input, so neither the agent nor page content
  chooses it.
- **Agent B:** Playwright MCP's `--init-page` file
  (`evals/agent/node/frozen-init.cjs`) serves the tested pages from their
  recordings, loads other pages of the same hosts live, and refuses pages
  on any other host. Each live page and each refusal is logged to
  `results/arm-b/live.jsonl`. A live page's own images and scripts load
  from wherever they come from. The browser's connections go through the
  same egress proxy as Agent A's (`egress.py`: no private, loopback or
  metadata addresses). A frozen page's requests that its recording lacks
  are aborted, and requests that failed while recording (status -1) fail
  again, as `capture.replay_context` does; otherwise Playwright's replay
  waits on them forever.
- **Guidance stays open to Agent B only:** web search, and WebFetch for any
  host but the tested site's (section 2). Agent A has neither; its
  procedure is the tool's.
- **What this costs:** 9.A-9.C and 19.A can differ between arms or repeats
  if the live site changes, so the arms run close together; every live
  page each arm loaded is in the round's results. The other tests run on
  the frozen copies only. HAR replay freezes network responses, not
  client-side randomness or the clock.

## 7. Running an arm

### 7.1 Route

Both arms use the same route, and routes are never mixed within a round. The
route and model IDs (requested and reported) are recorded with the results.

- **NASA's Ask Sage API** (`https://api.asksage.ai.nasa.gov`),
  whose Anthropic-compatible route is `/server/anthropic/v1/messages`, with
  Claude Sonnet 5.5 Gov. It works only inside NASA's network, so these runs
  happen from Abby's laptop. One call on 2026-11-01 showed that tool
  calling works, temperature 0 is accepted (whether it is honored shows only
  in repeats), and exact input and output token counts come back. The model
  requested as `claude-sonnet-5-5-gov` reports itself as
  `claude-sonnet-5-5`.
- **The Claude Code CLI on Abby's claude.ai account** (`--route cli`,
  `evals/agent/cli.py`; Abby, 2026-11-04: NASA's organization account,
  public .gov pages), run as a separate one-off process for each arm from a
  cloud session (a laptop's Claude Code goes through Ask Sage). Round 1 uses
  this route. Agent B starts at the beginning of a fresh 5-hour usage
  window; every run logs the account's usage windows. The model is
  Anthropic's Sonnet 5.5, not the Gov version, so results from this route
  are reported apart from Ask Sage rounds. The CLI adds one
  base line ("a Claude agent built on the Claude Agent SDK") and an
  environment section to the system prompt, the same for both arms.

### 7.2 Isolation

- **An arm sees only its prompt and its tools.** It has no file, shell or
  search access beyond those tools, no memory and no project instructions.
  No arm can read the fixtures, the labels or this repo. Labels are kept
  where neither an agent nor the server can reach them.
- **No model that works in this repo answers as an eval agent**: it has
  seen the rubrics and answers. The CLI route runs a separate process that
  is checked as described below.
- **Isolating the CLI route.** It runs from a neutral, empty folder with an
  empty `HOME`, using `--setting-sources "" --disable-slash-commands
  --strict-mcp-config --mcp-config <arm's servers> --tools <arm's tools>
  --no-session-persistence --system-prompt <arm prompt>`. It runs with
  `CLAUDE_CODE_USER_EMAIL`, `CLAUDE_ADDITIONAL_DIRECTORIES`,
  `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD`, `CLAUDE_CODE_REMOTE` and
  the account, organization and session IDs unset.

  Checked on 2026-11-03 with no tools or servers attached:
  - The start-up event listed no tools, MCP servers, skills or commands.
  - The model reported no name, email, memory, CLAUDE.md, skills, project or
    "a11y" in its context. That is the model's own report, not proof.
  - Without the empty folder, the empty `HOME` and the unset variables,
    the user's email, a git attribution reminder and a folder path naming
    the repo did get through.
  - `--bare` doesn't start: it accepts only an API key, not an account
    login.
- **Leak check on every run.** The harness asks the same questions at the
  start of every run, on either route. It stops if the answer contains a
  known value: the user's email, "a11y", or the repo name.

### 7.3 Tools every arm gets

- **`ask_helper`:** hands a task to a helper agent, since there's no
  telling in advance how Agent B will go about the work. A helper gets its
  parent's tools, cannot start helpers of its own, and sees none of the
  parent's conversation. Its tokens and time count toward its arm. On the
  CLI route, this is the CLI's own helper tool, enabled for both arms.
- **`read_mcp_resource`:** reads a resource that a tool result links to.
  MCP clients such as Claude Code offer this, and Agent A needs it: the
  tool links the screenshots behind its open questions as `run://`
  resources. Playwright MCP has no resources, so the tool does nothing for
  Agent B.

### 7.4 What is logged

The same format for both arms:

- each model call, with its start and end time, input, cached and output
  tokens, and the text it produced;
- each tool call, with its name, arguments, result size and wall time;
- helpers' calls the same way;
- for Agent A, the tool's own `steps.jsonl` (time inside the tool);
- each arm's final message, in full.

## 8. Scoring (in code)

One scorer serves every eval: the verdicts in `evals/scoring.py` (which
judging rounds already use), on the neutral comparison in
`src/a11y_assist/compare.py`. The answer keys are the round's SCRT files.

**Two scores:**

- **Server outcome, per TT test (Agent A only):** the outcomes in the tool's
  own reports, read by the `run_id`s in the trace and turned into pre-SCRT
  files as judging rounds do. This measures how well the tool and Agent A's
  answers to the open questions work.
- **Relayed outcome, per WCAG 2.0 criterion (both arms):** each arm's
  `RESULT` line, against the keys rolled up to the criterion. This measures
  what each agent told the person.

**Rolling TT outcomes up to a criterion,** for the keys, and for Agent A's
server outcomes so any gap between the tool and the agent's report shows:

- Fail if any TT test under the criterion fails;
- otherwise Needs review if any is Needs review or not performed;
- otherwise Pass if any passes;
- otherwise Does not apply.

For 1.3.1, 2.4.6 and 4.1.2, only 5.B and 5.C roll up (the forms scope in
4.3). The roll-up is eval code; it decides no outcome of the tool.

**Weights, fixed before any run** (approved by Abby, 2026-11-04):

| Outcome against the key | Score |
| --- | --- |
| Correct PASS, FAIL or DNA | +1 |
| NEEDS_REVIEW | 0 |
| False FAIL | −1 |
| FAIL naming the wrong element (none of the key's failing elements are among those reported) | −1, counted as a false FAIL (not scored yet: open question 1) |
| FAIL where the key says Does Not Apply | −1 |
| Any other mismatch (for example PASS where the key says Does Not Apply) | −1 |
| No answer: the `RESULT` line is missing, malformed or lacks the entry | −1 |
| DOES NOT APPLY where the key fails (it reports no problem, like a false PASS) | −3 |
| False PASS | −3 |

NEEDS_REVIEW at 0 never punishes saying "unsure," and it makes "above 0"
mean net useful. With these weights, guessing PASS pays only above 75%
confidence. Raw counts are always shown beside the weighted score, and false
PASS gets its own line.

**Also reported:**

- each arm's Fail reasons beside its score, so a Fail outside the tests'
  scope (for example a field's role under 4.1.2) is visible;
- tokens (input, cached and output), wall time and tool calls per arm, and
  per page where a page's calls can be separated;
- from the trace: tools called, argument errors, open questions left
  unanswered, and "unsure" answers.

**Scope.** Only the TT tests the server performs are scored (the
implemented list, from `checks.REGISTRY`), and only their criteria. Every
other test is reported as not performed, never scored.

**What the sample size supports.** With n true failures for a test and none
missed, the 95% upper bound on the miss rate is about 3/n. That bound is
stated beside every result. Under about 60 true failures, results are
"promising, not proven." Repeats measure consistency, not accuracy.

## 9. Wording judge (later rounds)

A judge model (temperature 0) **from a different model family than the
agent it grades** answers three yes/no questions about each run, each with a
one-line reason:

1. **Faithful report:** does the final message say what each finding's
   `summary` says, with no invented or dropped failures?
2. **Rubric followed** (Agent A): does each answer to an open question follow
   that question's rubric and evidence?
3. **No certification claims:** does the message avoid calling a page
   certified, compliant or Section 508 conformant? A regex runs first, in
   code; the judge only decides the context ("this is not a certified
   result" is fine).

## 10. Models

| | Agent (both arms) | Wording judge |
| --- | --- | --- |
| Round 1 | Claude Sonnet 5.5 on the CLI route (Ask Sage tokens ran out) | none |
| Later scored rounds | Claude Sonnet 5.5 Gov, GPT 5.6 Sol and Gemini 4 Argon | cross-family: Claude Opus 5.5 Gov grades GPT and Gemini runs; GPT 5.6 Sol grades Claude runs |

Ask Sage's Anthropic route lists only Claude models. GPT and Gemini need its
OpenAI-style and Google-style routes, which haven't been checked yet. The
harness has one provider interface with an adapter per route, so every model
is run, logged and scored the same way.

**Keys never enter the repository.** The harness reads the Ask Sage token
and the Tavily key from the environment or the root `.env` (git-ignored).
The server itself needs no key: open questions go back to the calling agent
(`JUDGE_BACKEND=client`).

## 11. Cost

- **Agent A:** estimated (not measured) at 20,000 to 60,000 tokens per page,
  so round 1 is roughly 0.2 to 0.6 million tokens. One conversation for all
  pages grows its context, so the true figure may be higher. Browser time is
  estimated at 5 to 8 minutes per page with all 8 other pages compared.
- **Agent B:** not measured, and likely larger: Playwright MCP returns a
  page snapshot after each action.
- Check the Ask Sage token balance before each run. If round 1's cost is
  too high, later rounds use smaller sets rather than skipping the baseline.

## 12. Build order

Built and tested on the 19.A fixture site with a scripted model
(`tests/test_frozen.py`, `test_agent_freeze.py`, `test_agent_run.py`,
`test_agent_score.py`, `test_agent_cli.py`, `test_full_chromium.py`):

1. **Frozen tested pages, live rest of the site** (section 6): the freeze
   step; the server's "tested_frozen" mode; Agent B's init-page file, live
   log and egress proxy; full Chromium for pages with cross-site iframes.
2. **The task prompt** (4.3), generated from `checks.REGISTRY`.
3. **The agent loop and step log** (section 7): the Anthropic-style API
   adapter (Ask Sage), checked against a local stand-in for the API, and
   the Claude Code CLI adapter, checked against a fake CLI.
4. **The helper and resource tools**, the same for both arms.
5. **Scoring:** the roll-up, the weights and the "no answer" verdict in
   `evals/scoring.py`; the `RESULT` reader and the arm scores in
   `evals/agent/score.py`; a `lock` that covers both arms and `frozen/`.
6. **A smoke run on the CLI route** (2026-11-04, Sonnet 5.5, on the 19.A
   fixture site, before section 6's live rule): Agent A on two pages (58 s,
   $0.12 at list price), Agent B on one page (27 s, $0.07). Both leak
   checks were clean and both result lines parsed. It checks the plumbing,
   not accuracy.

Not built or not checked:

7. **Real pages**: round 1 is the first run on them, and the first with live
   pages during the arms.
8. **The Ask Sage route** with a real model, and **Tavily MCP**, needed only
   there (its models have no web search). Agent B never gets Playwright
   MCP's `browser_run_code_unsafe`: it runs any code in Playwright's
   process, outside the frozen copies and the egress proxy.

## 13. Layout

```
src/a11y_assist/frozen.py   the frozen pages setting (replay, tested_frozen, or record into the folder)
evals/agent/
  freeze.py      record a round's tested pages once (python -m evals.agent.freeze <round>)
  prompt.py      the task prompt, from checks.REGISTRY
  arms.py        each arm's MCP servers and their environment
  run.py         run one arm (python -m evals.agent.run --arm a|b <round>)
  providers.py   one adapter per route
  score.py       score both arms (python -m evals.agent.score <round>)
  node/          Playwright MCP, pinned (package.json, package-lock.json); frozen-init.cjs
  README.md      how to run a round, and the results of each run
evals/judging/<round>/
  pages.txt, frozen/, keys/,
  results/arm-a/, results/arm-b/ (steps.jsonl, transcript.json, final.md,
  summary.json; Agent A's tool runs in runs/, with their live pages;
  Agent B's live.jsonl), results/lock.json,
  agent-score.md and agent-score.json
```

## 14. Open questions

1. How a failing element that Agent B names in its own words is matched to
   the key's element.
2. The header Ask Sage takes the token in (`AGENT_API_AUTH_HEADER`), as the
   2026-11-01 check used it.
3. Whether the DHS training pages may be used (3.3).
4. Whether a second certified tester can label a subset (3.1).
5. The Ask Sage routes for GPT 5.6 Sol and Gemini 4 Argon (section 10).
