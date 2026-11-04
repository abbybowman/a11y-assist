# The agent eval harness: what cost time

`evals/agent/` runs Agent A (this server) and Agent B (Playwright MCP) on a
frozen round. Plan: `docs/plans/2026-10-31-agent-eval.md`. Runbook:
`evals/agent/README.md`.

- **Freezing reuses the server.** `FROZEN_PAGES_DIR` (`frozen.py`) is a
  server setting: "record_missing" records a URL and adds it; "replay"
  replays it, and a URL with no recording is a tool error, never a live
  fetch. `freeze.py` runs 19.A once on each page in "record_missing" mode,
  so the page, its other pages and 19.A's site search are recorded exactly
  as a live run records them. If Agent A later chooses other pages that
  make 19.A search when the freeze did not, the search is refused and
  19.A says so.
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
- **Its HAR replay needs two fixes.** With several HARs on one page, only
  the first registered may use `notFound: "abort"`: later routes run
  first, so an aborting later HAR would hide the others. Requests that
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
- **Agent B must never get WebFetch or `browser_run_code_unsafe`.** Either
  one reaches outside the frozen replay: the live site, or this machine's
  files. Both routes remove them (`Server.deny`, and the CLI's `--tools`
  and `--disallowedTools`).
