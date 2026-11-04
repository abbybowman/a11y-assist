# Round 1: attempts stopped before they finished

Not results and never scored (the scorer reads `results/` only). Kept so the
round's history is complete.

## arm-a-1 (2026-11-04, 12:45-12:49 UTC)

Agent A on the CLI route. Stopped after about 4 minutes, with no result,
because of a harness bug: the Claude Code CLI gives an MCP tool call 60 s by
default (`MCP_TOOL_TIMEOUT`), and a run of the tool with 5 other pages takes
minutes, so every call came back to the agent as a timeout (`mcp-log.jsonl`:
"timed out after 60s"). The agent only saw the round's prompt and the
timeouts; no tool result reached it. Fixed in `evals/agent/cli.py` (one hour
per call; checked with a 70 s tool) before the run was started again.
Files: `steps.jsonl` (the harness's step log), `mcp-log.jsonl` (the CLI's log
of the a11y server connection).

## The search page's typo (2026-11-04)

`pages.txt` first listed `https://www.nasa.gov/search?=artemis` (a typo);
NASA answers it with its "Page Not Found" page, which was frozen and which
`results/arm-a-1` tested. Abby corrected the line to
`https://www.nasa.gov/?search=artemis` (same hash: her key is for that
page). The typo's recording and index entry are in `frozen-typo/`; the
corrected page was frozen on 2026-11-04 at about 13:30 UTC. `arm-a-1` is
scored on the 8 pages it was given; `arm-a-2` and Agent B use all 9.

## arm-b-1 and the search page frozen in the container (2026-11-04)

Agent B's first run (13:59-14:02 UTC) is not valid, and neither is the
search page frozen in this container at about 13:30 UTC
(`frozen-container-search/`).

- The container re-signs direct connections with a certificate Chromium
  does not trust, so that copy of the search page has its HTML but none of
  its CSS or scripts (status -1).
- Agent B's browser served those failed entries for every page, because
  the pages share NASA's CSS and scripts and the newest recording was
  consulted first: Agent B saw unstyled pages (58-107 console errors each).

Both are fixed (`UPSTREAM_PROXY`; cleaned recordings in the init-page),
checked with tests and on a live NASA page. The search page was frozen
again at about 14:55 UTC with its CSS and scripts. Agent A's runs were not
affected on the 8 pages frozen on Abby's laptop; `arm-a-2`'s search page
result used the broken copy and is not scored. Agent A's live 19.A searches
in `arm-a-1` and `arm-a-2` loaded without their scripts.
