# Agent eval: running a round

Agent A (a model with this MCP server) and Agent B (the same model with
Playwright MCP) test the same frozen pages with the same prompt. Their
results are scored against a tester's SCRT files by commit and reveal.
Plan: [docs/plans/2026-10-31-agent-eval.md](../../docs/plans/2026-10-31-agent-eval.md).
Lessons: [docs/solutions/agent-eval-harness.md](../../docs/solutions/agent-eval-harness.md).

Results are agent-assisted, not certified Trusted Tester results.

**Status:** every step below is tested on the 19.A fixture site with a
scripted model (`tests/test_agent_*.py`). None has run on a real model, on
real pages, or on Windows. Steps 1 and 2 need no model, so a round can be
frozen while it waits for model tokens.

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

## A round, in commit order

Round folder `evals/judging/<round>/`, for example `evals/judging/round1/`.

1. **Start.** The tester commits `pages.txt` (each URL with the SHA-256 of
   their SCRT file for it) when testing begins.
2. **Freeze.** This is the only step that touches the live site:

   ```bash
   BROWSER_CHANNEL=chromium HEADLESS=true uv run python -m evals.agent.freeze evals/judging/<round>
   ```

   It writes `frozen/` (an index, the recordings and `freeze.json`). Check
   that every page says `frozen`.
3. **Agent A, then Agent B:**

   ```bash
   uv run python -m evals.agent.run --arm a evals/judging/<round>
   ```

   ```bash
   uv run python -m evals.agent.run --arm b evals/judging/<round>
   ```

   Each run writes `results/arm-<a|b>/`: `steps.jsonl`, `transcript.json`,
   `final.md`, `summary.json`, and for Agent A the tool's own runs in
   `runs/`. A run first checks that the model's context holds nothing of
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
