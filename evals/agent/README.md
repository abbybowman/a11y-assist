# Agent eval: running a round

Agent A (a model with this MCP server) and Agent B (the same model with
Playwright MCP) test the same frozen pages with the same prompt. Their
results are scored against a tester's SCRT files by commit and reveal.
Plan: [docs/plans/2026-10-31-agent-eval.md](../../docs/plans/2026-10-31-agent-eval.md).
Lessons: [docs/solutions/agent-eval-harness.md](../../docs/solutions/agent-eval-harness.md).

Results are agent-assisted, not certified Trusted Tester results.

**Status:** every step below is tested on the 19.A fixture site with a
scripted model (`tests/test_agent_*.py`). The CLI route was also
smoke-run on that site with Sonnet 5.5 (2026-11-04, both arms; it checks
the plumbing, not accuracy). Nothing has run on real pages, on the Ask
Sage route, or on Windows. Steps 1 and 2 need no model.

## Once per machine

```bash
uv sync --group dev
```

```bash
npm ci --prefix evals/agent/node
```

The second command installs Playwright MCP, pinned in
`evals/agent/node/package.json` and `package-lock.json`.

Then set the model route in the root `.env` (git-ignored) or the
environment:

```
AGENT_API_BASE=https://api.asksage.ai.nasa.gov/server/anthropic
AGENT_API_KEY=...
AGENT_API_AUTH_HEADER=...   # the header Ask Sage takes the token in (default x-api-key)
AGENT_MODEL=claude-sonnet-5-5-gov
AGENT_LEAK_VALUES=...       # optional, comma-separated: values the leak check must not see
```

## Routes

- `--route api` (default): an Anthropic-style API, Ask Sage on NASA's
  network. Set the `AGENT_*` variables above.
- `--route cli`: the Claude Code CLI on the claude.ai account, from a
  cloud session (a laptop's Claude Code goes through Ask Sage). Each arm
  runs as an isolated `claude -p` (`cli.py`). Nothing to set; `--model`
  defaults to `claude-sonnet-5-5`. Every run logs the account's usage
  windows (`rate_limit` rows in `steps.jsonl`, `usage_windows` in the
  summary), so a large arm can start at the beginning of a fresh window.

Both arms of a round use the same route.

## A round, in commit order

Round folder `evals/judging/<round>/`, for example `evals/judging/round1/`.

1. **Start.** The tester commits `pages.txt` (each URL with the SHA-256 of
   their SCRT file for it) when testing begins.
2. **Freeze.** This is the only step that touches the live site:

   ```bash
   BROWSER_CHANNEL=chromium HEADLESS=true uv run python -m evals.agent.freeze evals/judging/<round>
   ```

   It records the tested pages only, into `frozen/` (an index, the
   recordings and `freeze.json`). Check that every page says `frozen`, and
   compare each frozen page's footer timestamp with your own testing.
   During the arms, the tested pages come only from these copies; other
   pages of the same site (site maps, search results) load live for both
   arms, so run the two arms close together.
3. **Agent A, then Agent B:**

   ```bash
   uv run python -m evals.agent.run --route cli --arm a evals/judging/<round>
   ```

   ```bash
   uv run python -m evals.agent.run --route cli --arm b evals/judging/<round>
   ```

   (`--route api` for Ask Sage.)

   Each run writes `results/arm-<a|b>/`: `steps.jsonl`, `transcript.json`,
   `final.md`, `summary.json`; for Agent A the tool's own runs in `runs/`
   (with each live page it loaded); for Agent B `live.jsonl` (each live page
   and each refusal). A run first checks that the model's context holds nothing of
   the user or this repo, and stops if it does.
4. **Lock**, then commit:

   ```bash
   uv run python evals/judging.py lock evals/judging/<round>
   ```

   The lock hashes `pages.txt`, `frozen/`, every result file and the
   scoring code.
5. **Reveal.** The tester adds their SCRT files to `keys/` and commits.
6. **Score:**

   ```bash
   uv run python -m evals.agent.score evals/judging/<round>
   ```

   It writes `agent-score.md` and `agent-score.json`: each arm per WCAG 2.0
   criterion, Agent A's tool per TT test, the weighted scores, each Fail's
   elements, and tokens, wall time and tool calls.

## Results

None yet.
