# round1-answers: Agent A told to answer the open questions (unscored)

A development round, never locked or scored as a round: Agent A on round
1's frozen pages (recordings restored from Abby's archive and checked
against `round1/results/lock-1.json`), with the same tool code as round 1
and prompt `answers-v1` (`evals/agent/prompt_dev.py`): answer every open
question, and rerun cut-short calls with `no_time_limit`. Compared with
Abby's round 1 keys as development analysis; nasa.gov is a development
site. Agent-assisted results, not certified Trusted Tester results.

The first attempt overloaded the container and was stopped
(`attempts/README.md`). This run (`results/arm-a/`, 2026-11-04 20:02-20:24
UTC) used `--no-subagents`.

## What happened

- **Answering:** 59 open questions on 6 pages, every one answered (0 left
  open), in 8 `a11y_answer_questions` calls.
- **`no_time_limit`:** Missions (refused as too large), the search page and
  Careers were called again with it, and the remaining pages were first
  called with it.
- **3 pages never finished:** Missions, NACA and KSC. With `no_time_limit`
  their calls ran past the CLI's 120 s foreground hold and moved to the
  background. The agent ended its turn to wait for them ("Three runs are
  still going in the background… I'm waiting for their results"). On the
  CLI's `-p` route, ending the turn ends the session, so the background
  calls were killed and there is no RESULT line. Scoring below is the
  tool's own files on the 6 finished pages.
- **Cost:** 1320 s wall time, 25 model calls, $1.31 at list price (cache
  writes 218k, cache reads 3.3M, output 10k). Usage: 5-hour window 20% to
  25%; 7-day window 81% to 81%.

## The tool against the keys, the same 6 pages

| Run | Weighted | Agree (of decided) | False PASS | False FAIL | Other | Undecided |
| --- | --- | --- | --- | --- | --- | --- |
| Round 1 A-1 (5 of the 6) | 31 | 34/37 | 0 | 3 | 0 | 48 |
| Round 1 A-2 | 32 | 35/38 | 0 | 3 | 0 | 64 |
| Round 1 A-3 | 36 | 38/40 | 0 | 2 | 0 | 62 |
| **answers-v1** | **56** | **61/66** | **0** | 3 | 2 | 36 |

Each TT test comes from the latest run that included it (the merge the
post-round 1 plan's fix 13 proposes for the scorer).

- **5.A is now right on all 6 pages.** The key fails 5.A on every page,
  because the header search field's only label is its placeholder. The
  agent answered J1 `not_labeled` 6 times ("placeholder only"), so 5.A
  failed on every page. In round 1 no run decided 5.A on any page.
- **5.C, 5.D, 5.H and 9.C are now decided and agree:**
  - 5.C: 21 answers `complete`;
  - 5.D: 2 answers `value` (phone and amount formats);
  - 5.H: 4 answers `not_consequential`;
  - 9.C: 8 answers `different_function`.
- **No false PASS.**
- **False FAILs (3):** all 4.D row M8 at 0 px, on the search page, Careers
  and Artemis III, where the key passes 4.D (fix 11). They come from the
  rule, not from an answer.
- **Other (2): 5.B Pass where the key says Does Not Apply** (Careers and
  the news release). On those pages the only field is the header search,
  which has no visible label. The agent answered `all_descriptive` for the
  header's form, and its reasons name buttons ("Button names describe
  themselves", "menu buttons"). For Abby: should 5.B be Does Not Apply when
  the only field has no visible label, and does 5.B cover the header's
  buttons?
- **The agent's "unsure" answers left 4.A (2), 4.D (1) and 4.F (6) needs
  review.** Every 4.F answer was "cannot settle", with no reason given.
  That is allowed by the rubric and safe, but 4.F stays undecided on every
  page. The agent read only 2 `run://` resources in the whole run, so it
  may have answered the visual questions without looking at their images.
  Check this before fix 4 changes the wording.
- **Still undecided:** 19.A on all 6 pages, which asks the user to
  approve more pages and has no question to answer, and 5.F/5.G (a form
  sent to its server).

## For the next run

- **The CLI's `-p` route loses background calls.** A call longer than 120 s
  moves to the background, and if the agent then ends its turn to wait,
  the session ends. Either keep the session open until background tasks
  finish (harness), or tell the agent not to end its turn while calls are
  running.
- **One server ran up to 12 browser runs at once** (the first attempt).
  Cap concurrent runs and queue the rest (post-round 1 plan, fix 5).
