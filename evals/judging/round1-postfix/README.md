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

## Sixth run: the finish call and `work` (`results/arm-a-6/`)

At commit 89325d1 (`a11y_run_status` `finish=true`; results carry `work`,
`remaining` and `waiting_on`), `--debrief`, from a separate worktree.

| Run | Weighted | Agree | Validated catch | False PASS / FAIL | Questions left open | Calls |
| --- | --- | --- | --- | --- | --- | --- |
| Sixth | 59 | 58 | 1 | 0 / 0 | 0 | 5 run, 22 status (2 with finish), 5 answer |
| Fifth | 58 | 57 | 1 | 0 / 0 | 0 | 9 run, 19 status, 5 answer |

- **Finish:** the agent called `finish=true` twice, and the server made
  the 19.A follow-ups for all five pages: it no longer started them by hand
  (9 run calls in run 5, 5 here). It read only two of their results, and
  those suggested further pages (the site map, search), which it did not
  pass on: "I ran out of steam". It never asked the user about Missions'
  5.D `no_time_limit` call.
- **Pictures:** still none opened. It answered "unsure" with "not viewed"
  on 4.D (Careers), 4.F (all pages), one 5.C and one 2.B question, though
  the transcript holds 34 attached images; it says "a step-by-step prompt
  to open each image, or a smaller image per question, would have helped".
  Change 3 (`seen`) is built after this run.
- **9.C:** answered from element names alone ("a guess"), giving PASS on
  those pages; its own report should call them weakly supported.
- It asked again for "a single 'you are not done' list I had to clear".

## Seventh run: the picture rule (`results/arm-a-7/`)

At commit 8db7481 (answers to picture questions need `seen`, or
`picture_error` with unsure), `--debrief`, from a separate worktree.

| Run | Weighted | Agree | False PASS / FAIL | Questions left open | Calls |
| --- | --- | --- | --- | --- | --- |
| Seventh | 57 | 56 | 0 / 0 | 1 (KSC 4.F) | 5 run, 10 status (0 finish), 6 answer |
| Sixth | 59 | 58 | 0 / 0 | 0 | 5 run, 22 status (2 finish), 5 answer |

- **The picture rule was met, but on paper.** 6 answers were refused for
  lacking `seen`. The agent then gave `picture_error` with unsure instead
  of looking: "images not examined" ×14, "order image not examined in
  detail" ×4. These are recorded as not viewed for a person: honest, and
  safe (no false PASS), but nothing was looked at. One `picture_error` was
  a real reading ("a tiny dark crop showing no clear focus indicator"). It
  opened 2 resources in the whole run.
- **Follow-through fell back.** It never called `finish=true` or
  `a11y_run_status` without a job_id. It made no 19.A follow-ups and
  never asked about Missions' 5.D `no_time_limit`. It missed KSC's 4.F
  question.
- **Debrief:** "many questions and the outputs were huge, so I took the
  cheap answer". It asked for a short to-do list at the end of each result
  instead of buried in 25-70k characters, smaller or paged outputs, and
  answers batched across runs.
- Runs 6 and 7 show how much one prompt varies from run to run (59 vs 57,
  finish used vs not); the plan's repeated runs per prompt will measure it.

## Eighth and ninth runs: baseline before the result refactor (`results/arm-a-8/`, `arm-a-9/`)

At commit 14fef46 (to-do list last in every result, questions 10 at a
time), `--debrief`, one after the other, from a worktree. These are the
"before" pair for the result refactor (plan change 2b: one line per
finding, `tobi_explain`).

| Run | Weighted | False PASS / FAIL | Questions left open | `finish` calls | Answers with `seen` / `picture_error` / neither |
| --- | --- | --- | --- | --- | --- |
| Ninth | 58 | 0 / 0 | 0 | 2 | 8 / 6 / 10 |
| Eighth | 58 | 0 / 0 | 6 (refused, not resent) | 2 | 0 / 1 / 10 |
| Seventh | 57 | 0 / 0 | 1 | 0 | 2 / 13 / 11 |

"Neither" counts answers to questions with no picture, which need
neither field.

- **Finish:** both runs called `finish=true` twice; run 7 never did. The
  to-do list is the likely cause, not proven. Both read only some of the
  follow-up results.
- **Refused answers:** run 8 left 6 questions open after their answers
  were refused for lacking `seen`, and never sent them again.
- **Pictures, a tool problem:** run 9 says the 4.F order picture,
  attached at 768 px, is "a tiny full-page thumbnail; numbers too small"
  to read. A full-page picture is unreadable when shrunk that far. This
  needs a fix: crop to the stops in question, or attach that one larger.
- **`seen` that was not seen:** run 9's debrief admits its `seen` text for
  NACA's 2.B questions m3-m7 ("faint SCROLL TO CONTINUE cue") was an
  inference, and a FAIL rests on it. The field can be filled without
  looking; the judge eval and a person's review remain the check.
- **Unchanged:** 9.C answered from names alone (both runs); Missions'
  5.D `no_time_limit` call was never put to the user.

## Tenth and eleventh runs: after the result refactor (`results/arm-a-10/`, `arm-a-11/`)

At commit d937ded (one line per finding, only changed findings after
answers, `tobi_explain`, compact question inputs), `--debrief`, from a
worktree. These are the "after" pair for runs 8 and 9. Run 11 was
restarted after a container restart cut off its first try.

| Run | Weighted | False PASS / FAIL | Questions left open | `finish` called | Picture answers: `seen` / `picture_error` | New context / re-read / output tokens |
| --- | --- | --- | --- | --- | --- | --- |
| Eleventh | 62 | 0 / 0 | 0 | yes | 14 / 0 | 107k / 1.25M / 12.2k |
| Tenth | 59 | 0 / 0 | 0 | yes | 3 / 12 | 122k / 0.86M / 11.9k |
| Ninth (before) | 58 | 0 / 0 | 0 | yes | 8 / 6 | 178k / 2.49M / 12.9k |
| Eighth (before) | 58 | 0 / 0 | 6 | yes | 0 / 1 | 176k / 1.30M / 9.8k |

- **Cost:** new context per run fell by about 35-40% after the refactor
  (107-122k from about 177k). Re-reads follow the number of calls.
- **Score:** 59 and 62 against 58 and 58. Run 11's 62 is the highest
  yet, with no false PASS or FAIL. The difference is in tests left
  undecided (23 against 27).
- **`seen` written without looking (run 11).** Its debrief: for the 4.F,
  5.B and 5.C questions it "wrote `seen` text as if I had looked, but I
  never opened those images", answering from the element lists. The
  pictures it means were attached to the results, so they were in its
  input; whether it attended to them, the field cannot show. Run 10 used
  `picture_error` the same way ("not inspected"). A required field
  invites a filled field: the judge eval, which checks answers rather
  than the field, and a person's review remain the checks.
- **Unchanged:** neither run asked the user about Missions' 5.D
  `no_time_limit` call. Both read only some of the follow-up results. Both
  answered 9.C from names alone. Neither called `tobi_explain`, which
  these runs' to-do list did not yet name.
- Run 11 asked for the server to refuse `seen` unless the picture's
  resource was opened. Only pictures not attached go through the resource
  reader, so the server could check those reads but not attention to
  attached ones.

## Twelfth run: no time limit by default, and the rest of change 2b (`results/arm-a-12/`)

At commit ba9f7b6, `--debrief`, from a worktree. New since run 11:
- no time limit by default, with a progress line in every still-running
  result;
- FAIL summaries whole, and `tobi_explain` on the to-do list;
- `picture_error` refused for attached pictures, and tall pictures in parts;
- 9.C 1.1.1.

**Weighted 54** (run 11: 62), no false PASS or FAIL. 53 agree, 31 not
performed. The drop has two causes, neither of them the default:
- **Artemis III's keyboard walk stopped early.** P1 ended "loop" after 13
  presses (run 11: wrap at 82), so 4.B, 4.E, 5.D, 5.F, 5.G and 5.H went to
  NEEDS REVIEW. Replaying the frozen page four times, P1 ended "loop" once
  (9 presses) with the 600 s limit and wrapped at 82 the other three
  times, with and without it. It is an intermittent walk problem on this
  page, now in the ROADMAP.
- **4.F on Careers and Missions stayed open.** The agent answered "unsure"
  with `picture_error` ("did not open images") where run 11 answered.

What the run showed of the new changes:
- **Picture rule:** 15 refusals (9 for `picture_error` on an attached
  picture). The agent answered again, 11 with `seen` and 11 with
  `picture_error`. It still opened no `run://` picture.
- **`finish`:** called twice, and the status check with no job_id twice.
- **`tobi_explain`:** never called, though the to-do list names it ("My
  failure explanations come only from the one-line summaries").
- **Missions' 5.D:** run with no time limit, with no question to the user.
  It asked 5.D questions in groups of 30 fields, which the agent answered
  "unsure".
- **It asked for:** a "nothing left" signal in the answer result itself,
  and `tobi_explain`'s output folded into results.
