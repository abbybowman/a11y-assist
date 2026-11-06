# round1-postfix: Agent A after the post-round 1 fixes (development run)

Not a judging round: never locked or scored as one. Git keeps each arm's
`summary.json`, `final.md`, `debrief.md` and `steps.jsonl`; its tool runs
(reports, pre-SCRT files with screenshots inline) and transcript stay on
the machine that ran it (`.gitignore`), and the figures below come from
them. Five of round 1's
pages, from round 1's frozen recordings (Careers, Missions, Artemis III,
NACA, KSC history; `frozen/`, recordings git-ignored), Agent A on the CLI
route (Sonnet 5.5), the round 1 task prompt with **no special prompt**,
`--no-subagents`, 2026-11-05, at commit e90ce07 (fixes 1-20 built; fix 19
option 3 and fix 6b's smaller results included).

Compared with Abby's round 1 keys for the same five pages, by
`evals/agent/score._server` (the tool's own results, per TT test):

| Run | Weighted | Agree | False PASS | False FAIL | Left by the time limit |
| --- | --- | --- | --- | --- | --- |
| This run | 36 | 37 | 0 | 1 | 38 |
| Round 1 arm-a-1 | 20 | 24 | 0 | 4 | 35 |
| Round 1 arm-a-2 | 19 | 21 | 0 | 2 | 30 |
| Round 1 arm-a-3 | 18 | 20 | 0 | 2 | 33 |

What the agent did (fixes 2, 4, 5, 12, 18):
- **Long calls (fix 2/5, option C):** 5 `a11y_run_tt_tests` calls and 17
  `a11y_run_status` calls; no call was lost, and the run took 648 s.
- **Open questions (fix 4):** it answered 12 of the 13 questions asked, in
  3 `a11y_answer_questions` calls, with no prompt telling it to. Round 1's
  three runs answered none.
- **Time limit:** it never set `no_time_limit`, so NACA (all tests) and
  parts of Missions and Artemis III were cut short: the largest loss left
  (38 cells).
- **19.A (fix 18):** it named the suggestion ("I didn't rerun with the home
  page and sitemap added") but did not act on it.
- **The false FAIL:** Artemis III 4.D, the video player's "Hide player
  controls" button, which is covered at its centre when it has focus (fix
  11): Abby is checking the live page.

Cost: $0.60 at list price; tokens: cache writes 114,431, cache reads
441,884, output 9,936.

## Second run: the 600 s run limit (`results/arm-a-2/`)

Same pages, prompt and model, after the run limit went from 120 s to 600 s
and `next_step` began naming follow-up calls (commit 582426c).

| Run | Weighted | Agree | False PASS | False FAIL | Left by the time limit | Questions answered |
| --- | --- | --- | --- | --- | --- | --- |
| 600 s limit | 53 | 54 | 0 | 1 | 0 | 8 of 81 |
| 120 s limit | 36 | 37 | 0 | 1 | 38 | 12 of 13 |

- **The longer limit removed every time-limit loss** (38 to 0). The run
  took 760 s, with 22 `a11y_run_status` calls; no call was lost.
- **Answering fell off with volume:** more tests finished, so 81 questions
  were asked (Missions 58, 56 of them 5.C's label questions; NACA 10). The
  agent answered Careers' 8 in one call and reported the rest as "not
  checked". Those 73 questions are the next gain.
- **Follow-up calls were not made:** neither 19.A's (the suggested pages)
  nor 5.D's on Missions (`no_time_limit`), though `next_step` named both.
- The same false FAIL (Artemis III's covered player button). The agent's
  own report also turned NACA's 4.D FAIL into needs review ("the elements
  it listed were only ones it couldn't see"); the key fails NACA 4.D.

Cost: $0.61 at list price; wall time 760 s.
