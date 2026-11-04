# Plan: fixes after agent eval round 1

Status: **open; collecting during round 1.** Each fix below is made after
round 1 is locked and before the next round. They are not made during
round 1: the round measures the code as it was at its start. Results and
scores: `evals/judging/round1/`. Eval plan:
[2026-10-31-agent-eval.md](2026-10-31-agent-eval.md).

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
- **Status:** not started. `arm-a-2`, an unchanged repeat, declined them
  too ("I did not answer the open questions"): 2 of 2 runs.

### 5. Parallel calls to one server

- **Found:** round 1. Both Agent A runs issued several calls at once. The
  stdio server ran them one at a time: in `arm-a-2` the calls' durations
  climb by about 120 s each (120, 239, 359, 478, 601, 720, 840, 959 s), so
  each waited for the ones before it, and each then had about 120 s, the
  run limit, so several were cut short ("the tool hit its time limit on
  several pages"). Even a refusal that needs no browser work (Missions, 98
  form fields) took 482 s in the queue, against 5 s alone.
- **Fix:** decide what one server does with concurrent calls: run them
  side by side (each in its own browser) or say in the tool's description
  that calls run one at a time and a batch is slower than calls in turn;
  in either case a call's time limit must not include its wait.
- **Status:** not started.

### 6. Agent A asked for a shell

- `arm-a-2` called `Bash` once, which the eval does not give (refused:
  "No such tool available"). Probably to wait for a slow call. Harmless;
  noted for the agent's behaviour, nothing to fix.

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
- **Refusals with advice.** The Missions page (98 form fields) was refused
  with advice to call again with `no_time_limit`. Record whether Agent A
  followed it.

## Done during round 1 (the harness, not the tool)

- A new frozen recording could reuse the file name of one still in use
  (`frozen.py` named it by counting the index): fixed, with a test.
- Runs of one arm are labeled (`--label`, `results/arm-a-1/`, `arm-a-2/`),
  and each run is scored on the pages it was given.

- One-hour MCP tool timeout on the CLI route (`evals/agent/cli.py`).
- The CLI route's step log keeps the first 500 characters of each tool
  result, so errors show their text.
