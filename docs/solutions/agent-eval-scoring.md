# Scoring and reading an agent eval round: what cost time

Round 1 (2026-11-04) was the first round scored against real SCRT keys.
Results: `evals/agent/README.md` ("Results"). The answering runs:
`evals/judging/round1-answers/README.md`.

- **The lock covers the scorer and the prompt.** `lock.json`'s `code`
  includes `evals/agent/score.py`, `evals/scoring.py`, `compare.py`,
  `scrt.py` and `evals/agent/prompt.py`. `score` refuses to run if any of
  them changed ("score with the code at commit …"); it does not just
  record the change.
  - A scorer fix found after a lock is for the next round (post-round 1
    plan, fix 13).
  - Analysis beyond the scorer goes in a separate script that imports the
    scorer's own functions (`verdict`, `rollup`, `compare`), so there is no
    second copy of the verdict logic.
  - Development prompt versions live in `evals/agent/prompt_dev.py`
    (`--prompt`). Never edit `prompt.py` after a lock.
- **"Not performed" in `agent-score.md` is mostly "needs review".** The
  checks put the note "This test could not be performed" on every
  NEEDS_REVIEW, including ones that only wait for an answer. Sort them by
  the finding's summary instead:
  - "did not complete" / "time limit": cut short;
  - "question … open": waiting for an answer;
  - anything else: could not be performed.
- **An agent can split a page's tests across calls.** In round 1,
  `arm-a-2` ran Missions as six tests, then 9.A alone. Merge per TT test,
  taking each test from the latest finished run whose `tests` included it.
  The locked scorer takes only the latest run.
- **`page_key` drops the query.** `/?search=artemis` scores as the home
  page. A round with both would collide.
- **Rerunning a locked round's pages.** A locked round refuses new runs.
  Use a development folder (`evals/judging/<round>-<name>/`) with the
  round's `pages.txt` and frozen index; `.gitignore` already keeps its
  recordings out.
  - The rerun needs only the frozen `*.har.zip` files from the archive.
    Each is about 16-24 MB, under the 30 MB chat upload limit; the whole
    zip (176 MB) is not.
  - Check each recording against `lock-1.json`'s `files` hashes. The
    manifest is not needed.
- **Check usage before every run.** A one-line
  `claude -p --output-format stream-json --verbose` call prints a
  `rate_limit_event` with the 5-hour and 7-day windows. Round 1's Agent A
  runs cost 1-2% of the 7-day window each, the answering runs about 1% each.
  The cloud session's own work uses the same account.
- **Cost per run is in `summary.json`** (`cost_usd_list_price`,
  `usage_windows` first and last). Cache writes and output cost the most;
  cache reads are cheap. Agent A's 2-4 minute tool results are mostly
  cache writes.
- **Many identical open questions overwhelm the agent.** Missions asked
  152 questions, 96 of them the same 5.D question per checkbox. The CLI
  saved the result to a file the agent read only in part, and the agent
  reran the page six times in smaller pieces rather than answer (fix 15).
