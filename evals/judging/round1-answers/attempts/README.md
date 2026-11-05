# round1-answers: attempts stopped before they finished

A development round, never scored: Agent A with prompt `answers-v1`
(`evals/agent/prompt_dev.py`) on round 1's frozen pages.

## arm-a-1 (2026-11-04, 19:42-19:58 UTC): stopped, machine overloaded

- **What the agent did:** it sent three calls without `no_time_limit`
  (Spot the Station, search results, forms page), as round 1 did. Then,
  before answering any of their 8 open questions, it launched 9 subagents
  in parallel (the CLI's own Task/Agent tool, available in round 1 too but
  unused), one per page. Each ran `a11y_run_tt_tests` with
  `no_time_limit` and a sitemap among its other pages, and was told to
  answer the questions itself.
- **What happened:** up to 12 tool runs at once on a 4-CPU, 15 GB
  container. The load average reached 51, with 310 Chrome processes and 14
  GB of memory in use. Calls and checks failed with
  `Page.goto: Timeout 30000ms` (`check_error` in the runs' `steps.jsonl`),
  which turns tests into NEEDS_REVIEW for reasons that have nothing to do
  with the page.
- **Stopped by hand** after 16 minutes, so no data would come from an
  overloaded machine. No question was answered. Three runs have reports;
  the rest stopped mid-run. Usage: 7-day window 79% to 80%.
- **Files:** `steps.jsonl` (the harness log; no summary or transcript,
  since the run was killed) and `runs/`.

For the tool: one server accepted 12 browser runs at once, with no limit.
A hosted server would face the same (post-round 1 plan, fix 5).
