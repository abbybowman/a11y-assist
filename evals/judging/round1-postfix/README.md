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

## Third run: grouped 5.C, follow_up_calls, the page cache, a debrief (`results/arm-a-3/`)

At commit e136924 plus the page cache, `--debrief`.

| Run | Weighted | Agree | False FAIL | Questions answered | Follow-up calls made |
| --- | --- | --- | --- | --- | --- |
| Third | 44 | 45 | 1 | 13 of 30 | 1 of 6 |
| Second | 53 | 54 | 1 | 8 of 81 | 0 |

- **Fewer questions:** 30 asked (81 before): 5.C's set grouping took
  Missions from 58 to 6.
- **A follow-up call made:** 19.A on Careers with the suggested pages (one
  of five pages); not 5.D's `no_time_limit` call on Missions.
- **The cache:** later calls reused 3-4 of their 4 other pages each.
- **The score fell from 53 to 44** with fewer tests finished on some pages;
  one run per setting, so part of this is noise.
- **Why (its debrief, `debrief.md`):** "two large outputs were cut off";
  it did not track what was still open across five pages; it started
  wrapping up for time and volume; it doubted answering would help. It
  asked for a compact list of open questions and follow-ups, one "what is
  outstanding" call, and a way to answer all pages' questions at once.
- **The cut-off outputs were ours:** results with pictures attached were
  150-545k characters (12 pictures each) and went over Claude Code's MCP
  result limit (about 25k tokens), so the agent lost part of their text,
  questions included. Fixed after the run: pictures now get only the token
  budget the text leaves (20k in all), at 768 px, at most 8.

## Fourth run: the outstanding-work list and the picture budget (`results/arm-a-4/`)

At commit 5adc37e, `--debrief`.

| Run | Weighted | Agree | False FAIL | Questions answered | Follow-up calls made |
| --- | --- | --- | --- | --- | --- |
| Fourth | 55 | 56 | 1 | 27 of 28 | 2 of 7 started, 0 collected |
| Third | 44 | 45 | 1 | 13 of 30 | 1 of 6 |
| Second | 53 | 54 | 1 | 8 of 81 | 0 |

- **Answering:** 27 of 28 questions, in 4 calls; only KSC's 4.F question
  was missed ("I lost track", its debrief).
- **Follow-up calls:** it started Missions' 19.A and 5.D (`no_time_limit`)
  calls but stopped before collecting them, and made none for three other
  pages. It never called `a11y_run_status` without a job_id. Its debrief:
  "I stopped waiting and wrote the report", and its final message wrongly
  said the calls "did not finish in the time available".
- **Pictures:** it says it answered visual questions from the text and
  mostly did not look at the pictures, though results now attach them
  (120-380k characters with pictures, within the token budget).
- **Results:** no false PASS; the same false FAIL (Artemis III's covered
  player button).
- Its own report overreached on NACA (it called 2.4.7 and 2.2.2 FAIL partly
  on its own guesses); it asked for confirmed and unconfirmed failures to be
  told apart more clearly.

## Fifth run: a finishing condition and confirmed failures apart (`results/arm-a-5/`)

At commit 1f8de03 (`next_step`: "finished only
when a11y_run_status with no job_id lists nothing left"; FAIL findings
carry `confirmed` and `unconfirmed`), `--debrief`. Scored with Abby's
adjudication of Artemis III's player button (a validated catch, +1), so
earlier runs are rescored the same way:

| Run | Weighted | Agree | Validated catch | False FAIL | Questions left open | Follow-up calls collected |
| --- | --- | --- | --- | --- | --- | --- |
| Fifth | 58 | 57 | 1 | 0 | 0 | 1 of about 6 |
| Fourth | 57 | 56 | 1 | 0 | 1 | 0 of 7 |
| Third | 46 | 45 | 1 | 0 | 6 | 1 of 6 |
| Second | 55 | 54 | 1 | 0 | 8 | 0 |

- 9 `a11y_run_tt_tests`, 19 `a11y_run_status`, 5 `a11y_answer_questions`
  calls; 1,106 s.
- **Answering:** every question answered, but the debrief says many only
  in form: it never opened a picture (4.D, 2.B and 4.F got "unsure",
  "not viewed"), and answered 9.C and 5.B/5.C from names alone.
- **Follow-up calls:** still mostly skipped (only NACA's 19.A collected),
  and it never made the no-job_id `a11y_run_status` check the new
  `next_step` asks for. Its debrief: "mostly effort and time ... each skip
  felt small. Nothing was unclear." It asked for one call that runs all
  follow-ups together, image review marked required, and a hard "not done"
  status until questions are answered.
