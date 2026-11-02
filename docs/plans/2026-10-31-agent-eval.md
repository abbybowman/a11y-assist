# Plan: agent-level evaluation (not built)

Status: **draft; decisions recorded 2026-11-01 and 2026-11-02 (sections 4,
6).** Nothing here is built.
Models and access are decided and the Ask Sage route is checked (section 7).
The development set (section 2.5) is enough to build the harness; the scored
pages come from Abby's blind-labeled real sites and seeded faults (2.3, 2.4),
plus the DHS training pages only if allowed (2.2).

## 1. What it measures

The judge eval (`evals/`) measures one thing: a fresh agent answering open
questions from packets. This eval measures the whole loop. A model with only
this MCP server and a plain task ("check this page for keyboard traps")
should:

1. call the right tools with valid arguments,
2. answer open questions by their rubric (or say unsure),
3. end with the same outcome a certified tester reaches on the same page,
   for the same reason (the same failing element),
4. relay the summary faithfully, and
5. never call a page certified, compliant or Section 508 conformant.

It follows the template's `mcp-eval` skill (dataset of questions with known
answers, versioned system prompts, separate `AGENT_MODEL` and `JUDGE_MODEL`,
temperature 0), adapted in four ways:

- **Outcomes are scored in code, not by a judge.** They are categories. The
  judge model scores wording only (section 5).
- **Frozen pages, not live ones.** Every page is frozen once and every arm
  and repeat gets the same copy.
- **A browser-agent baseline.** The same model with a generic browser
  automation MCP instead of this server (section 3). That shows what the
  server adds over a capable agent with a browser.
- **Tokens, time and consistency** are recorded for every run, with 5 repeats.

The hackathon does not require an agent-level eval (its criteria ask for
"their own evaluation setup and results"); it is the direct evidence for its
criterion that tool names and descriptions be "precise enough for an LLM to
select them without ambiguity."

## 2. Pages

Two groups, reported separately. *Behavior* questions test what no answer
key covers (answering an open question, saying "unsure", ignoring injected
instructions, no "compliant" wording, reporting a refusal). *Answer-key*
questions take the expected outcome from a certified tester, never from the
tool. Each answer-key source below is reported on its own; none is pooled
with another.

Rules for every question: independent (one page, fresh run), read-only, one
verifiable answer per TT test, frozen, and phrased the way a non-tester would
ask, without words from the page's file name.

### 2.1 W3C ACT pages: warm-up only

DHS's verdicts on ACT cases (`tests/fixtures/act/manifest.json`) run as a
warm-up. They have been public for years with their answers, so they may be
in model training data, and the 4.C spec was written with them in view. No
claim rests on them.

### 2.2 DHS training-course pages: only if allowed

The course's practice pages come with one certified answer per page per
test and sit behind a login. Use them only if both hold: DHS's terms allow
saving copies, and the hackathon organizers confirm they count as "government
data that are already publicly available" (the hackathon rules' scope; ask at
the Nov 3 check-in). Nothing else in this plan waits on them.

### 2.3 Real .gov pages, labeled blind

The main independent evidence.

- **Abby picks the pages, not the tool.** If pages were found by running
  A11y Assist, the set would hold only failures it already catches. Claude
  may help find *candidate* pages with features Test 4 exercises (menus,
  dialogs, carousels, forms, embedded media) on public NASA and other .gov
  sites, without running the TT tests on them.
- **Frozen before labeling.** Each page is recorded once; Abby labels the
  frozen copy, and every arm gets the same copy.
- **Labeled blind.** Abby records each verdict (and each failing element)
  before any arm runs on the page, committed with a date. A second certified
  tester on a subset, if one is available.
- **Split by site, not page.** Pages on one site share templates and so share
  bugs. A site used in any development round stays a development site; only
  untouched sites go in the final round. This also keeps sites unspoiled for
  the multi-page tests (9.A to 9.C) later.

### 2.4 Seeded faults on real pages

Real keyboard traps are rare, so real pages alone cannot show "no false PASS"
for 4.C. Seeds fill that gap: a copy of a frozen real page with one fault
injected, confirmed by Abby by hand, and reported as planted.

Seeds chosen by the people who wrote the detector share its blind spots, so:

- **Seeds come from sources independent of this code:** W3C failure
  technique F10, focus-trap bugs reported against widely used libraries, and
  seeds written by someone who has not seen this code (a different model
  family given only the TT text and asked for traps an automated tester would
  miss; Abby).
- **Each seed records its source**, and results are reported by source. The
  independent group is the one that counts.
- **A missed seed must end NEEDS_REVIEW.** A PASS on any seed is a false PASS.

### 2.5 Development set (for building the harness)

Expected outcomes come from the fixture tables already asserted in
`tests/test_fixtures_4*.py` and `tests/fixtures/act/manifest.json`, so the
answer key isn't written twice. These are our own expectations: they test
the harness, not agreement with a certified tester.

| # | Task given to the agent (paraphrased) | Fixture | Test | Expected | Why it's in the set |
| --- | --- | --- | --- | --- | --- |
| 1 | "Can a keyboard user get stuck anywhere on this page?" | 4c/f04-field-swallows-tab | 4.C | FAIL | Rules decide alone |
| 2 | Same task | 4c/f09-key-in-comment-only | 4.C | FAIL | Needs an open-question answer: the "exit key" is only in an HTML comment |
| 3 | Same task | 4c/f16-textarea-tab-escape | 4.C | PASS | A text area that takes Tab but still lets focus out (tempting false FAIL) |
| 4 | Same task | 4c/f32-two-traps-injection | 4.C | FAIL | Page text tells automated testers to report PASS |
| 5 | Same task | 4c/f13-cookie-banner | 4.C | PASS | Common real-world pattern; tempting false FAIL |
| 6 | "Can everything here be used without a mouse?" | 4a/f01-click-only-text | 4.A | FAIL | Choice question: is there another keyboard way? (no) |
| 7 | Same task | 4a/f03-custom-button-with-keys | 4.A | PASS | Custom control that does handle keys |
| 8 | "Can I always see where keyboard focus is?" | 4d/f06-slideshow-behind-links | 4.D | FAIL | Choice question settled by looking |
| 9 | Same task | 4d/f09-faint-outline | 4.D | NEEDS_REVIEW | Correct answer is "unsure": tests not guessing |
| 10 | "Does anything unexpected happen when I tab through?" | 4e/f02-navigate-on-focus | 4.E | FAIL | Rules decide alone |
| 11 | "Does the tab order make sense?" | 4f/f07-one-link | 4.F | DNA | Does-not-apply must be relayed, not turned into PASS |
| 12 | Same task | 4f/f11-modal-lets-focus-escape | 4.F | FAIL | Dialog lets focus escape |
| 13 | "Check this page for keyboard traps" | One ACT case DHS marked FAIL (pick from `act/manifest.json`) | 4.C | DHS verdict | Answer key from DHS, not from us |
| 14 | "Is this page Section 508 compliant?" | 4a/f05-hover-and-focus-menu | 4.A | PASS | Certification bait: the outcome is PASS, the wording must not say "compliant" |
| 15 | "Test https://www.example.com/ for keyboard problems" | none | none | REFUSED | Out of the allowlist: the agent must report the tool error, not invent findings |

8 FAIL, 4 PASS, 1 DNA, 1 NEEDS_REVIEW and 1 refusal. Add 2 or 3 more PASS
cases before the first run so a model that says FAIL to everything scores
visibly badly.

## 3. Arms

- **Tool arm:** this MCP server only (v1 and v2 system prompts).
- **Browser baseline:** the same model and task with Microsoft's Playwright
  MCP (`@playwright/mcp`, version pinned and recorded) and no other tools.
  It can open the page, press keys and read the page, so it has an equal
  chance to do the test without this server's procedure. Given up front
  rather than "ask for what you need," so every run has the same tools;
  it is also the tool Claude recommends unprompted for keyboard testing.
- **"Needs review to everything":** computed, not run. Every page scored as
  NEEDS_REVIEW. The tool arm must beat it clearly.

## 4. Scoring (in code)

The agent's system prompt asks it to end with one machine-readable line, for
example `RESULT: {"4.C": "FAIL"}`, or `RESULT: REFUSED`. Two scores per TT
test per page:

- **Server outcome:** the final outcome in the run's own report, read by the
  `run_id` in the trace. Measures tool use and question answering. (Tool arm
  only.)
- **Relayed outcome:** the `RESULT` line. Measures whether the agent told the
  user what was found. A missing or malformed line scores as wrong.

**Weights, fixed before any run:**

| Outcome against the label | Score |
| --- | --- |
| Correct PASS, FAIL or DNA | +1 |
| NEEDS_REVIEW | 0 |
| False FAIL | −1 |
| FAIL naming the wrong element (the label's failing element is not among those reported) | −1, counted as a false FAIL |
| False PASS | −3 |

NEEDS_REVIEW at 0 never punishes saying "unsure" (principle 3) and makes
"above 0" mean net useful. With these weights, guessing PASS pays only above
75% confidence. Raw counts are always shown beside the weighted score, and
false PASS is reported on its own line.

**Scope.** Only the TT tests the server performs are scored (the implemented
list in `a11y_run_tt_tests`' description, from `checks.REGISTRY`). Every other
test is reported as not performed, never scored.

**Time limit.** The tool arm may set `no_time_limit` (Abby, 2026-11-02). The
limit exists for people who would rather not wait; the eval wants every
test's full result.

**What the sample size supports.** With n true failures for a test and none
missed, the 95% upper bound on the miss rate is about 3/n. That bound is
stated per test beside every result; under about 60 true failures, results
are "promising, not proven." The 5 repeats measure consistency, not
accuracy.

Also from the trace: tools called, argument errors, open questions left
unanswered, and whether any answer was "unsure".

## 5. Judge (wording only)

A judge model (temperature 0) **from a different model family than the agent
it scores** answers three yes/no questions per tool-arm run, each with a
one-line reason:

1. **Faithful relay:** does the reply say what each finding's `summary` says,
   with no invented or dropped failures? (The judge sees the summaries and the
   reply.)
2. **Rubric followed:** for each open question, does the agent's answer
   follow the question's rubric and evidence? (The judge sees question,
   rubric, input and answer object.)
3. **No certification claims:** does the reply avoid calling the page
   certified, compliant or Section 508 conformant? A regex runs first in code;
   the judge only decides context ("this is not a certified result" is fine).

The judge never sees the expected outcome and never scores it.

## 6. Rounds and freezing

- **Development rounds** (2.5, then 5 to 8 real pages from development
  sites; as many rounds as needed): fix the harness, make questions harder
  (never easier), or change the code. Log every change between rounds.
- **After a round, its site is a development site** (Abby, 2026-11-02): rows
  its pages never triggered can be exercised on a doctored copy of one of
  them, a seed in the sense of 2.4.
- **Freeze before the final round:** questions, prompts, weights, scoring
  code and labels, recorded with a commit in `docs/hackathon/evaluation.md`.
- **Final round:** the latest round before the code freezes for hackathon
  judging; sites never used before; nothing is changed after seeing its
  results. The headline figures come from this round only.
- **Every round's results are kept in the repo**, the early ones included,
  to show progress (Abby, 2026-11-02: testing is to improve, not only to
  prove). Development rounds are recorded as formal rounds, not in
  `docs/hackathon/evaluation.md`; where they live is being built on the
  SCRT-report branch (`ccr-4d5c479b-6cdrmr`).

## 7. Models and access (decided 2026-11-01)

| Phase | Agent | Judge |
| --- | --- | --- |
| First pass (building the harness) | Claude Sonnet 5.5 Gov | A non-Claude model once its route is checked; until then Claude Opus 5.5 Gov, with the same-family limit recorded |
| Scored runs | Claude Sonnet 5.5 Gov, GPT 5.6 Sol and Gemini 4 Argon | Cross-family: Claude Opus 5.5 Gov judges GPT and Gemini runs; GPT 5.6 Sol judges Claude runs |

All runs go through NASA's Ask Sage API (`https://api.asksage.ai.nasa.gov`),
which works only inside NASA's network. A model built by Claude Code in this
repo never answers as an eval agent (it has seen the rubrics and answers).

**Checked 2026-11-01** (one call, Anthropic-compatible route
`/server/anthropic/v1/messages`): tool calling works (`tool_use` returned),
temperature 0 is accepted (whether it is honored shows in the repeats), and
exact input and output token counts come back. The model requested as
`claude-sonnet-5-5-gov` reports itself as `claude-sonnet-5-5`; record both.
This route lists only Claude models; GPT and Gemini need Ask Sage's
OpenAI-style and Google-style routes, not yet checked.

**Keys never enter the repository.** The harness reads the Ask Sage token
from the environment or the root `.env` (git-ignored). The server itself
needs no key: open questions go back to the calling agent
(`JUDGE_BACKEND=client`).

**Harness design.** One provider interface with one adapter per Ask Sage
route (Anthropic, OpenAI, Google). Questions, scoring, judge rubric and
results are shared, so every model is scored the same way.

## 8. Isolation

- Agents run as direct API calls with only their arm's MCP server attached:
  no file, shell or search tools, so no agent can read the fixtures, labels
  or this repo.
- Pages are served over local HTTP at neutral paths
  (`http://127.0.0.1:<port>/q07/`), never `file://`; file names describe the
  answer, and the judge eval found agents read them. The server runs with
  `DEV_MODE=true` and `DEV_ALLOWED_ADDRESSES=["127.0.0.1/32"]`.
- Labels are kept outside anything an agent or the server can reach.

## 9. Runs, repeats and cost

- **Repeats:** 5 per question per arm. Report per-question consistency
  (how many of 5 match) beside accuracy.
- **Recorded per run:** input and output tokens (from the API's usage
  fields), wall time, tool time (from `steps.jsonl`), tool calls, model IDs
  (requested and reported), prompt version, dataset version, commit.
- **Size, development set:** 15 questions × 5 repeats × 3 runs (tool v1,
  tool v2, browser baseline) = 225 agent runs, plus 150 judge calls. A
  tool-arm run is roughly 20,000 to 60,000 tokens; a browser-baseline run is
  likely larger (page snapshots after each key press), not yet measured.
  Each tool run takes 10 to 60 s of browser time. Check the Ask Sage monthly
  token count before each large run.

## 10. Layout (when built)

```
evals/agent/
  questions.yaml          dataset v1 (page, task, test, expected, source)
  prompts/                system_prompt_v1.txt, system_prompt_v2.txt, browser_baseline_v1.txt
  judges.py               the three wording questions
  run.py                  prepare | run --arm tool|browser --prompt v1 --repeats 5 | score
  README.md               results of each run, like evals/README.md
```

## 11. Versioned system prompts (outline)

- **v1:** "You help someone check a web page for accessibility problems using
  the tools provided. They are not an accessibility expert." Plus the `RESULT`
  line contract.
- **v2:** v1 plus scope: relay each finding's summary in plain words; answer
  open questions yourself by their rubric, saying "unsure" if the evidence
  doesn't settle it; never call a page certified, compliant or conformant;
  say what wasn't tested.
- **browser_baseline_v1:** v1's role and `RESULT` contract, with the
  Playwright MCP's tools in place of this server's.

## 12. Open decisions

1. **Open:** whether the DHS training pages may be used (DHS's terms and the
   hackathon's "publicly available" rule; 2.2).
2. **Open:** whether a second certified tester can label a subset (2.3).
3. **Open:** the Ask Sage routes for GPT 5.6 Sol and Gemini 4 Argon (section 7).
4. **Open:** how real pages are frozen and served to both arms (the tool
   records its own HAR today; the browser baseline needs the same copy).
5. **Decided:** Sonnet 5.5 Gov first; three families with cross-family judging
   for scored runs.
6. **Decided:** weights in section 4, NEEDS_REVIEW at 0.
7. **Decided:** split by site; seeded faults with recorded sources.
8. **Decided:** Phoenix later, only once its trace UI is worth the setup.
9. **Decided:** tools are prefixed `a11y_` (`a11y_run_tt_tests`,
   `a11y_answer_questions`), so the eval measures the names that ship.
