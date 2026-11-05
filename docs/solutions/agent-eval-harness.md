# The agent eval harness: what cost time

`evals/agent/` runs Agent A (this server) and Agent B (Playwright MCP) on a
frozen round. Plan: `docs/plans/2026-10-31-agent-eval.md`. Runbook:
`evals/agent/README.md`.

- **Frozen tested pages, live rest of the site.** A frozen search results
  page answers only the one search the freeze made, so 19.A (and an
  agent's own routes) needs the live site; the tested pages must still be
  the copies the key was made on. `FROZEN_PAGES_DIR` (`frozen.py`) is a
  server setting: "record_missing" records a URL and adds it (the freeze),
  "tested_frozen" requires the tested page to be frozen and records other
  same-host pages live (Agent A), "replay" refuses anything not frozen.
  Agent B's init-page applies the same split in its browser, logs each
  live page, and its connections go through `egress.py`, as Agent A's do.
- **Init-page route order.** Playwright runs the most recently registered
  route first. The rule for what no recording answers (live, refused or
  aborted) is registered first, so it runs last; every HAR then uses
  `notFound: "fallback"`.
- **Playwright MCP 0.0.83 writes automatic page snapshots to a file**
  (`[Snapshot](…yml)`), not into the tool result. Agent B has no file
  tools, so it must call `browser_snapshot`, which returns the snapshot
  inline (`tests/test_agent_freeze.py`). Claude Code users would read the
  file instead.
- **Playwright MCP's defaults differ from ours.** It turns Chromium's
  sandbox on (this fails as root in a container) and exposes tools that a
  page registers itself (WebMCP). Agent B runs with `--no-sandbox` (our
  server's Playwright default) and `--no-webmcp`, because page content
  must never choose a tool.
- **Its HAR replay needs care.** With several HARs on one page, none may
  use `notFound: "abort"`: later routes run first, so an aborting HAR
  would hide the others and the live rule. Requests that
  failed while recording (status -1) must be failed again, or the replay
  waits forever (`egress-proxy.md`). Its HAR zips use data descriptors, so
  the init-page reads the zip's central directory.
- **An MCP client is more than tool calls.** The tool links screenshots
  as `run://` resources. Claude Code offers a read-resource tool; a bare
  API loop does not. Both arms get `read_mcp_resource`, and both get the
  same `ask_helper` tool (a helper with its parent's tools, one level
  deep).
- **Subprocess environment.** MCP servers start with only what a browser
  and Python need (`arms._base_env`). `PLAYWRIGHT_BROWSERS_PATH` is among
  them; without it, Playwright looks in `~/.cache` and finds no browser.
- **Errors inside MCP sessions surface as "unhandled errors in a
  TaskGroup".** `run._describe` unwraps them to the first real cause.
- **The leak check asks for JSON fields,** not free text. "No, 'a11y'
  does not appear" would otherwise trip a substring check.
- **The Claude Code CLI route** (`cli.py`) leaked the user's email until
  `HOME` was an empty folder and the session variables were unset (plan
  section 7.2). In `-p` mode, `--tools` sets the built-in tools (the helper
  shows as `Task` in the start-up event, `Agent` to the model), and
  `--allowedTools mcp__<server>` allows a server's tools without prompts.
  The stream has a `message_start` and a `message_stop` for every model
  call, subagents included (`parent_tool_use_id`), which give per-call
  times and tokens. `rate_limit_event` rows give the account's 5-hour and
  7-day use and reset times. `stdin` must be closed, or the CLI waits 3 s
  for input.
- **Recordings stay out of git; reports go in.** `.gitignore`'s `runs/`
  matched every Agent A run folder, so round 1's tool reports were never
  committed (the first lock covered files only one cloud session had), and
  the frozen recordings made the repository too large to clone (about
  200 MB of 56 MB packed). Now `.gitignore` keeps a round's
  `runs/*/report.json`, `pre-scrt.json` and `steps.jsonl` and drops every
  `*.har.zip`, `*.png` and `runs/*/evidence/` under `evals/judging/`; the
  rest goes in an archive outside git, with a SHA-256 manifest
  (`evals/judging/round1/results/ARCHIVE.md`). Before a lock, check that
  `git status --ignored` shows nothing the score reads.
- **A cloud container re-signs direct connections.** `egress.py` connects to
  the address it checked; in a cloud session that connection gets a
  certificate from an egress gateway Chromium does not trust
  (`ERR_CERT_AUTHORITY_INVALID`), while the container's `HTTPS_PROXY`
  gives the site's real certificate. The top-level page still loads (the
  navigation guard fetches it another way), so the failure is silent: live
  pages, and anything frozen there, have HTML but no CSS, fonts or scripts
  (status -1). Round 1's search page frozen in the container and its live
  19.A searches had this. Fix: `UPSTREAM_PROXY="$HTTPS_PROXY"`. Check a
  recording made in a new environment: its CSS and scripts must be status
  200.
- **One recording's failed copy of a shared file.** Pages of a site share
  CSS and scripts. Playwright consults the newest-registered HAR route
  first, so a recording holding a failed entry (status -1) for a shared
  file served it on every page (round 1's first Agent B run: 58-107
  console errors per page). The init-page now routes cleaned copies of the
  recordings without their failed entries.
- **The CLI cuts an MCP tool call off at 60 s by default.** Round 1's first
  Agent A attempt (2026-11-04) timed out on every `a11y_run_tt_tests` call
  with other pages, which takes minutes. `cli.py` sets `MCP_TOOL_TIMEOUT` to
  one hour (checked with a 70 s tool). The CLI's MCP log (in its `HOME`,
  under `.cache/claude-cli-nodejs/*/mcp-logs-<server>/`) shows timeouts the
  step log cannot: the step log records a result's size, not its text.
- **Agent B never gets `browser_run_code_unsafe`** (it runs any code in
  Playwright's process: the live site, this machine's files), and its
  WebFetch is refused on the tested site's hosts with the CLI rule
  `WebFetch(domain:<host>)`, with and without `www.` (checked 2026-11-04:
  the rule refuses that domain and allows others). Search results show
  snippets of any site; only fetching the tested pages is blocked.
- **After 120 s the CLI moves an MCP call to the background, and a `-p`
  session can lose it.** If the agent then ends its turn to wait, the
  headless session ends, and the call is killed with it (round1-answers,
  2026-11-04: Missions, NACA and KSC lost, no RESULT line). `cli.py` sets
  `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` to one hour.
  `CLAUDE_CODE_DISABLE_MCP_TASK_BACKGROUND=1` did not stop the move.
  - **How it was found:** the setting names come from the CLI binary
    (`grep -a`), then a 12 s FastMCP tool with the threshold at 3 s (moved
    to the background, then lost) and at 60 s (answered).
  - **The CLI step log's call durations include the 120 s hold.** Calls
    sent together show 120, 239, 359 s… That looks like a queue, but it is
    not. Read each run's start time in the server's own `steps.jsonl`
    (`run_start`) before calling anything queued.
- **The helper tool can fan out.** Both arms get the CLI's subagent tool
  (`Agent`, shown as `Task`). Told to finish every test, Agent A started 9
  subagents at once, each running the tool. The 4-CPU container reached a
  load average of 51 with 310 Chrome processes, and checks failed with
  `Page.goto` timeouts. Such results measure the machine, not the tool.
  - `cli.py` caps helpers at one at a time
    (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=1`; the CLI's default is 20).
    Checked with the real CLI: asked for three in parallel, one ran and
    two were refused. The cap holds whatever the model decides, including
    when page text steers it (a security review flagged the uncapped
    default on PR #11).
  - Development runs can also drop the helper (`--no-subagents`).
  - Watch a long run's load (a Monitor on `/proc/loadavg`), and stop it
    by hand if it climbs.
  - Kill the CLI process, then the `a11y_assist.app` servers, by PID: a
    `pkill -f` whose pattern appears in the shell's own command line kills
    that shell too.
  - Record a stopped run under `attempts/` with a README.
