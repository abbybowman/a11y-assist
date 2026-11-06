# Plan: the agent finishes the work, whatever prompt started it

Status: **draft 2026-11-06, building on branch `agent-follow-through`**
(after PR #14, post-round 1 fixes).

**Why (Abby, 2026-11-06):** the tool should help agents give consistent
results without relying on a perfect starting prompt. Development runs 4
and 5 ([round1-postfix](../../evals/judging/round1-postfix/README.md))
used round 1's plain task prompt (nothing about this tool, no time
pressure). The agent answered every question once that was the obvious
next step. It skipped what cost extra calls:
- most follow-up calls (1 of about 6 collected);
- the final no-job_id `a11y_run_status` check;
- every picture ("unsure, not viewed").

Its debrief: "Nothing was unclear… mostly effort and time… each skip felt
small." So the instructions are understood and lose to the agent's own
sense of "done" (writing its final line). Prose in `next_step` cannot win
that; the tool has to make the complete path the cheap one.

## Research (2026-11-06)

- **Design around outcomes.** Exposing many small steps and trusting the
  agent to sequence them is a common anti-pattern; text in a tool
  description is guidance, never enforced (AWS, "MCP tool design:
  practical approaches and tradeoffs"; Phil Schmid, "MCP best practices";
  Workato, "MCP server design"; The New Stack, "15 best practices for
  building MCP servers").
- **Every result says what to do next, and errors say how to fix them**
  (Anthropic, "Writing effective tools for agents", Sept 2025). Already
  done (`next_step`).
- **Evaluate from transcripts.** Let agents read their own transcripts and
  suggest changes (same post). Done (`--debrief`).
- **Protocol features that take the model out of the loop**, each
  depending on client support (not checked yet for Claude Code and the
  other target clients):
  - **MCP Tasks** (spec 2025-11-25, experimental): call now, fetch later;
    the client polls, not the model.
  - **Sampling:** the server sends its own prompt, with the picture, to
    the client's model.
  - **Elicitation:** the server asks the user directly.
- **Client support (second search, 2026-11-06).** These come from
  third-party snapshots; check them against modelcontextprotocol.io/clients
  before building:
  - **Sampling:** deprecated in the 2026-07-28 spec (SEP-2577); about 2 of
    24 surveyed clients support it. Claude Code is listed without it; VS
    Code has it. Dropped.
  - **Elicitation:** the one active client feature; Claude Code is listed
    with it.
    - Form mode takes simple fields only (text, number, yes/no, a choice);
      nothing found about images.
    - URL mode (2025-11-25) sends the person to a web page after the
      client asks their consent.
  - **MCP Apps:** the server ships an HTML view that the client renders in
    the conversation. Hosts named: Claude, Claude Desktop, VS Code Copilot.
    A terminal cannot render it.
  - **MCP Tasks:** experimental. The core spec and an extension (SEP-2663)
    describe it differently, and no Claude Code support was found.

## Changes, in order

### 1. One call finishes the outstanding work

- `a11y_run_status` with `finish=true` (no job_id) starts every
  outstanding follow-up call the server may make by itself, as one job,
  and waits like any run. Its result is the outstanding list again, with
  each run's new findings.
- The calls are listed in `follow_up_calls`; the server still makes only
  the calls it would make for the agent:
  - **A test left by the time limit,** re-run alone. It runs within the
    usual limit; `no_time_limit` stays the user's choice (CLAUDE.md).
  - **19.A with pages the caller already gave.**
- **What stays with the agent:**
  - **Pages suggested from page content.** The server never visits them by
    itself (CLAUDE.md); the agent passes them back as `other_pages`.
  - **`no_time_limit`.** The user's choice.

  The result lists both once, as decisions for the agent or the user,
  never as work silently dropped.
- **Check:** a tool test with two runs that have follow-ups; the
  dev-round run shows follow-ups collected.
- **Status:** built (2026-11-06). `a11y_run_status` with `finish=true`
  (`pipeline.take_follow_ups`, `record_follow_up`; the report records each
  call made in `follow_ups_made`, so it is made once). Abby, 2026-11-06:
  the server may visit 19.A's suggested pages, so 19.A's call is made by
  the server; `no_time_limit` calls are listed in `for_the_user`. Test:
  `tests/test_fixtures_19a.py::test_finish_makes_the_suggested_pages_call_once`.
  Not yet checked: a development answering run.

### 2. Status in the data, not in prose

- Results carry `work`: `"incomplete"` while the run has open questions or
  follow-up calls, with `remaining` (questions, calls, the tests that can
  still change). It is `"complete"` only when nothing is left. `status`
  stays the job's state ("done" means the run ended), so pollers do not
  change.
- Every FindingView whose outcome depends on remaining work says so in a
  field (`waiting_on`), so a careless relay still reads as incomplete.
- `a11y_answer_questions`' result carries the same status.
- **Check:** model and tool tests; no outcome logic changes (outcomes still
  come only from the specs).
- **Status:** built (`models.Remaining`, `FindingView.waiting_on`;
  `tests/test_models.py`).

### 3. Answers that show the picture was seen

- A question whose rubric needs a picture asks the answer to name
  something only the picture shows in a `seen` field. Examples: the
  indicator's colour, or which item is outlined.
- An answer without `seen` is recorded as "not viewed": the question stays
  open and goes to a person. It is never taken as "unsure", which reads
  as a judgment.
- The server does not check `seen` against the picture: it only shows the
  agent looked. The judge eval checks whether such answers are right.
- Questions to change: 4.D, 4.F, 2.B and the others with `image_*` inputs.
  The rubrics change, so run the judge eval (CLAUDE.md principle 6).
- **Status:** built (2026-11-06; `Answer.seen`, `Answer.not_viewed`,
  `judgment.record_answers`). The rule covers questions whose input names
  a picture (the pictures attached to the result); a picture only in
  `evidence_paths` does not count. An answer without `seen` is refused with
  a message saying how to open the picture; an unsure without it is
  accepted and marked `not_viewed`. Checked: `tests/test_models.py`,
  README example 3, and the scripted test answers. **Not yet checked:**
  the judge eval (the answer format changed), and a development answering
  run. Run 6's agent answered "unsure, not viewed" on every picture
  question, so if unsure stays the easy way out, consider refusing an
  unsure without `seen` too (Abby to decide).

### 4. Reconsider which choices stay with the agent or the user (Abby, 2026-11-06)

- **`no_time_limit` by default.** Abby leans toward it, provided the user
  running the agent sees frequent progress, so a long run never looks
  stuck.
  - **Needed first:** progress the user sees, not only the agent.
    Progress notifications per phase and page exist; check what Claude
    Code and other clients show of them.
  - **Each `a11y_run_status` return carries a one-line human status**
    (phase, page, stops walked of the estimate, elapsed, a rough ETA) for
    the agent to relay.
  - **Shorter waits per call** so updates come more often.
  - **Decision:** if users can see the run moving, make `no_time_limit`
    the default. Keep `RUN_LIMIT_S` as a safety cap far above any page
    seen so far (NACA took 309-428 s), and update CLAUDE.md's time rule.
- **19.A's suggested pages: decided (Abby, 2026-11-06).** The server may
  visit them itself; built with change 1. CLAUDE.md principle 5 names the
  exception.
- **Elicitation form mode for what remains a user choice** (simple fields,
  where the client declares elicitation); otherwise list it as in 1.

### 5. Show NEEDS_REVIEW items to a person, with the screenshot

- **Chat clients: an MCP Apps review view.** One card per question,
  showing:
  - the screenshot;
  - the plain-language question (no spec codes);
  - the answer buttons.

  The person's answer goes back to the server and overrides the agent's
  (principle 8).
- **Terminals and other clients:** a plain question plus `run://` image
  links, and elicitation form mode for the answer where supported.
- **Maybe later: elicitation URL mode.** It would open a review page the
  server serves. That needs authentication and a security review first;
  hosted deployment only.

### 6. Visual questions answered by the server's own model (`ApiJudge`)

- Build the planned `ApiJudge` (`judgment.py` stub; the hosted model
  named in `config.py`) for questions that need a picture. This works
  whatever the client and whatever the prompt.
  - **Costs:** the server needs a key and pays for the model calls.
  - **Recording:** every report records the judging model, as now.
  - **Checking:** the judge eval measures it before it is turned on.
  - **Fallback:** the client agent answers the rest.

### 7. Watch: MCP Tasks

- Replace our polling with MCP Tasks once the spec settles and target
  clients support it. Until then, change 1's single finish call keeps
  polling cheap.

## Evaluating prompt independence

- **Three task prompts per development round:**
  - Round 1's plain prompt.
  - A one-liner a real user would type ("check these pages for Section
    508 issues").
  - One with time pressure ("you have limited time; be quick").
- **Each prompt run 2 or 3 times,** scored as now.
- **Two things measured:**
  - **Spread between runs and prompts:** outcomes per TT test that change
    from run to run.
  - **Follow-through:** questions answered, follow-ups collected, pictures
    opened.
- **Target:** every prompt within a few points of the others, and no
  false PASS on any. Prompt variants go in `evals/agent/prompt_dev.py`.
- Round 2's scored run still uses one fixed prompt, chosen before its lock.
