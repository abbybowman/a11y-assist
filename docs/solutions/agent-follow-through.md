# Getting the calling agent to finish the work

Development runs 4-11 (`evals/judging/round1-postfix/README.md`, 2026-11-05
to 07), each with a debrief turn asking the agent what it skipped and why.
Plan: `docs/plans/2026-11-06-agent-follow-through.md`.

## Prose loses to the agent's own idea of "done"

The agent understood every instruction ("Nothing was unclear") and still
skipped what cost extra calls: follow-up calls, the final status check,
pictures. A sentence in `next_step` or the tool description competes with
the agent's own idea that the work is done, which is the moment it can
write its report, and loses.

What worked better, in order:
- **Fewer steps.** `finish=true` makes the follow-up calls in one call.
  The agent called it in 5 of 6 runs after it existed; before, it made
  almost none of the calls itself.
- **Status in the data.** `work`, `remaining`, `waiting_on` and the
  to-do list keep a careless relay from reading as complete.
- **The to-do list last.** Results ran 25-70k characters with the
  instructions at the top; the agent reads the end last.

Still not solved by any wording:
- reading every follow-up result;
- asking the user about `no_time_limit`, which is why it is now the
  default;
- calling `tobi_explain` before reporting.

## A required proof field gets filled, not followed

Answers to picture questions must say what the picture shows (`seen`), or
why they could not (`picture_error`). Each tightening moved the shortcut:
- Run 7 wrote `picture_error`: "images not examined" ×14.
- After `picture_error` was limited to pictures not attached, run 11
  wrote `seen` "as if I had looked, but I never opened those images".
- Run 9 called an inference a sighting, and a FAIL rests on it.

The server can check only what it serves. It can record a `run://` read,
but not whether the agent attended to a picture attached to a result. Do
not add more proof fields. Keep the honest record (`not_viewed`), check
answers with the judge eval, and move visual questions to the server's
own model (`ApiJudge`), which the judge eval can measure.

## One run is noise for behaviour

The same code and prompt gave `finish` used (run 6) and not used (run 7).
Scores moved only ±1-4 across runs 5-11, but behaviour moved a lot.
- **One run per small change**, read for behaviour (counts from the
  transcript: `finish`, `seen`, `picture_error`, `tobi_explain` calls).
- **Two runs on each side** only for a structural change, such as the
  result refactor (runs 8-9 before, 10-11 after).
- **The judge eval first** for any question or rubric change. At about
  90-175k tokens it costs a tenth of an answering run.

Count behaviour from `transcript.json` tool calls, not from the final
report: run 8's report did not mention 6 questions left open after their
answers were refused.

## Measure a result by field before cutting it

`evals/snapshot.py` prints result sizes, and a field-by-field breakdown
of a transcript's results takes a few lines (`json.dumps` length per key).

- **In answer results, findings were 70%.** Full summaries, rule rows and
  links were re-sent after every answer.
- **In a first result, the open questions were 66%,** mostly evidence the
  agent needs: one 4.F question carried a 13k list of stops.

The refactor (one line per finding, only changed findings after answers,
detail in `tobi_explain`) cut first results by about 20% and new context
per run by 35-40%. Rounding coordinates saved only 10% more. The rest is
evidence; cutting it means a new question format and its own judge eval.

Keep a short summary whole. A summary of 400 characters or less is often
the action needed ("run again with other_pages"), and a test that checked
for it caught the first version.

## Before a refactor that must not change outcomes, take a snapshot

`evals/snapshot.py record` runs six fixture pages through the pipeline
and saves outcomes, rows, summaries, questions and follow-up calls.
Record twice first: identical twice means any later difference is real.
After each step, `check` must say "identical". The suite passing is not
the same check: it tests the outcomes it was written for, not everything
a report holds.

## Pictures

A full page shrunk to 768 px on its longer side is about 160 px wide, and
4.F's order numbers could not be read. A picture taller than two widths
now keeps 768 px of width and is sent in parts of 1024 px, the first four
attached, each captioned with its part number (`inline._encode`).

## Rubric examples must not be the fixtures' own words

Judge eval run 26: "the rubric names this exact pair". 9.C's examples
("Search" / "Find") were the fixture pages' names, so the eval measured
matching, not judgment. Pick examples that appear on no fixture page
(grep `tests/fixtures/` first, titles included). Run 27, with neutral
examples, is the real result.

## Practicalities

- **Run answering runs from a worktree at a fixed commit.** The server
  starts from the files on disk, so editing while a run goes changes what
  it tests. Link the git-ignored `frozen/` folder into the worktree, then
  copy the run's small files back (`summary.json`, `final.md`,
  `debrief.md`, `steps.jsonl`); the rest stays ignored.
- **A container restart stops background work without a result.** A run
  that finished before it keeps its files in the worktree; check there
  before rerunning.
- **What the user sees of progress is the result each status call
  returns.** Third-party reports say Claude Code does not show MCP
  progress notifications (not confirmed in Anthropic's docs). Each
  still-running result now carries a progress line with elapsed time and
  asks the agent to relay it.
- **The repository moved** (`tobi508`), but this session's git access
  covers the old name, which redirects; push there.
