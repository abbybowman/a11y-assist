# round1-postfix: Agent A after the post-round 1 fixes (development run)

Not a judging round: never locked or scored as one. Five of round 1's
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
