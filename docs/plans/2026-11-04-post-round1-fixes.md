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

## Observations to decide after scoring

These describe how Agent A used the tool. They are not bugs. Whether to act
on them depends on what round 1's scores show.

- **Other pages per call.** Agent A passed 5, then 3, then 2 other pages,
  not all 8, and did not set `no_time_limit` on its first calls. 9.A–9.C
  and 19.A get more reliable with more pages. The tool's description could
  say so more plainly.
- **Refusals with advice.** The Missions page (98 form fields) was refused
  with advice to call again with `no_time_limit`. Record whether Agent A
  followed it.

## Done during round 1 (the harness, not the tool)

- One-hour MCP tool timeout on the CLI route (`evals/agent/cli.py`).
- The CLI route's step log keeps the first 500 characters of each tool
  result, so errors show their text.
