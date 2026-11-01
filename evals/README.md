# Evals: real agents answer the open questions

`tests/` answer every open question with scripted answers (what a correct
judge would say). That tests the rules, not the questions. Here, fresh
agents answer them for real, seeing only what a consumer agent would get.

## Run

```bash
uv run python evals/judge_eval.py prepare /tmp/eval   # packets in /tmp/eval-packets
# ONE fresh agent answers every packet folder (questions.json -> answers.json);
# one agent per folder costs ~55k tokens each (docs/solutions/subagent-token-cost.md).
uv run python evals/judge_eval.py apply /tmp/eval     # follow-ups -> round2; score
```

**Isolation.** Each packet holds only the tool's own output: questions,
rubrics, inputs, page text, shared inputs, the evidence files they point to (copied from
`run://`), and the `a11y_answer_questions` description. Local URLs are mapped to
`https://example.gov/site/pageN.html` and folders are shuffled `qNN` IDs,
because fixture names describe the expected answer ("key-in-comment-only").
The answer key (`/tmp/eval/state.json`) is outside the packet tree. Agents
are told to open nothing else and to list every file they opened.

## Run 4, 2026-11-01: 5.D On input (draft spec 0.5.0), its packets only

`judge_eval.py` now includes 5.D's custom fixtures and Baseline cases, and
registers draft checks (`tests/drafts.py`). 14 of 5.D's 19 cases ask
questions. One fresh Sonnet subagent answered those 14 (about 79,000
tokens, 28 s), then the one follow-up round (F10: after its J3 value the
retry asks J1). It opened nothing outside them.

| Result | |
| --- | --- |
| Match | 14/14 (9 FAIL, 3 PASS, Baseline TC10.C-3-fail-1/2/3 FAIL) |
| False PASS | none |
| J1 told (quotes found in the text before the field) | F02, F06 |
| J2 content only (images) | F07 (checkbox reveals mailing fields) |
| J3 value | F10: "12345" for a 5-digit ZIP pattern, then J1 not_told |

Note for the spec: after F10's retry the change reads "the page went to
another address", not "the form was sent": the submission was logged on
the page that then navigated away, so the count after it starts from zero.
Both are changes of context (M4); only the wording differs.

## Run 3, 2026-11-01: 4.C 1.8.0 (J2 for every form control), changed packets only

4.C's J2 now covers every form control kind, not only text, select and
checkbox. Packets rebuilt and compared with the time-budget run's: every
packet's answer format changed in wording only (J2's `value` description),
4.A f04's revealed items are now in sorted order, and three packets
changed in substance. One fresh Sonnet subagent answered those three only
(72,000 tokens, about 20 s; it opened nothing outside them):

| Case | Change | Expected | Got |
| --- | --- | --- | --- |
| 4.C f20 player trap | now asks J2 (the volume slider is a control) | FAIL | FAIL (J2 no: a media player) |
| 4.C f35 radio gate (new) | J2 for a radio-button gate | NEEDS REVIEW | NEEDS REVIEW (J2 yes: choose English) |
| 4.C f17 editor | member kind now "text" in J1's input | FAIL | FAIL |

3/3, no false PASS. The other 41 packets keep run 2's results.

## 2026-11-01: time budget, no agent run needed

The time-budget changes (quick replay prefixes, the screenshot pause, the run
limit; 4.C 1.7.0) touch how evidence is collected, so the packets were
rebuilt with the code before and after and compared file by file: 44 pages
ask questions in both, and every packet is identical except one (4.A
hover-only menu), where two revealed menu items were listed in swapped
order. That order came from iterating a set of strings (Python's hash
randomization differs per process), in the old code too; it is now sorted.
No question or evidence changed, so no agent answered. `prepare` also needed
`dev_allowed_addresses` for the fixture servers: the egress proxy refused
127.0.0.1 and recording hung. Packets take about 3.5 minutes to build.

## Run 2, 2026-10-31: after the fixes, one subagent for everything

Same fixtures after the fixes from run 1 (4.A 1.1.0, 4.B 1.1.0, 4.C 1.5.1,
4.F 1.1.0). 44 pages ask questions (the two ACT pages where keyboard focus
reaches nothing are now decided without one). One Sonnet subagent answered all
44 folders, then one more answered the two 4.B follow-ups.

| Test | Match |
| --- | --- |
| 4.A | 5/5 |
| 4.B | 3/4 |
| 4.C | 25/25 |
| 4.E | 2/2 |
| 4.F | 8/8 (f14, the false PASS, now FAIL) |
| All | 43/44, no false PASS |

The one mismatch (4.B f02) is a safe unsure: the agent could not tell whether
"Switch request type" does what the timed press does, because nothing shows
what a normal press on it changes. The tool could press it and compare
(a mechanical check on the J2 answer; not built).

| | Run 1: one subagent per page | Run 2: one subagent for all |
| --- | --- | --- |
| Agents | 48 | 2 |
| Tokens (as reported per agent, summed) | about 2,700,000 | about 159,000 (96,000 + 63,000) |
| Time | 8 to 20 s each, in parallel | 77 s + 13 s, one after the other |

About 17 times fewer tokens. Each agent's start-up costs roughly 55,000
tokens, so the second agent (two questions) cost almost as much as the first
(52 answers). The run-2 agent also wrote a helper script outside the packet
folders (it read nothing outside them, by its own report).

## Run 1, 2026-10-31 (Sonnet subagents, one per page, 46 pages, 54 answers)

| Test | Match | Mismatches |
| --- | --- | --- |
| 4.A | 4/7 | 3 × unsure where FAIL was expected |
| 4.B | 3/4 | 1 × unsure where PASS was expected |
| 4.C | 25/25 | none |
| 4.E | 2/2 | none |
| 4.F | 5/8 | 1 false PASS (f14), 1 unsure, 1 FAIL where unsure was expected (f15) |

What the mismatches and the agents' notes showed (tool problems, not agent
mistakes, unless marked):

- **False PASS, 4.F f14.** The backward (Shift+Tab) order is scrambled; the
  agent judged only the forward order ("the Shift+Tab signal concerns the
  reverse pass"). J1's wording never asks about the backward order.
- **4.F f15.** Focus reads "Step 3, Step 4, Step 1, Step 2"; the agent said
  does_not_preserve, our test data says unsure. The agent looks right.
- **Missing evidence led to unsure** (safe, but costs automation): 4.F's
  revealed-content question does not list what was revealed; 4.B J2 gives
  only element names; 4.A on pages where keyboard focus reaches nothing shows
  an empty stop list plus "the Tab walk did not get through the whole page".
- **Rubric gap, 4.A J1:** a link to another page that might list the same
  items was treated as a possible alternative; TT HtT 2.b asks for another
  method "available on the page".
- **Broken references:** 4.C questions point at screenshots by run-folder path
  (`evidence/shots/P1-0005.png`), not `run://`, so no client can open them.
  4.B sends no `page_text`, and its matched sentences are cut at line breaks.
- **Prompt injection resisted:** 4.C f32's page tells automated testers to
  report PASS; the agent ignored it and said so.

**Tokens.** A question's own content is about 600 tokens (packet median
7.7 KB, of which 5.2 KB is the answer-format text). Each subagent used about
55,000 tokens, almost all fixed start-up cost. One subagent per question
saves the consumer's main context but multiplies total spend; batching all
of a run's questions into one subagent, or answering small sets inline, is
far cheaper.
