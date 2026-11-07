# Evals: real agents answer the open questions

`tests/` answer every open question with scripted answers (what a correct
judge would say). That tests the rules, not the questions. Here, fresh
agents answer them for real, seeing only what a consumer agent would get.

The agent eval (a model driving this server, against the same model with
Playwright MCP) is in `agent/`: see [agent/README.md](agent/README.md).

## Run

```bash
uv run python evals/judge_eval.py prepare /tmp/eval   # packets in /tmp/eval-packets
# ONE fresh agent answers every packet folder (questions.json -> answers.json);
# one agent per folder costs ~55k tokens each (docs/solutions/subagent-token-cost.md).
uv run python evals/judge_eval.py apply /tmp/eval     # follow-ups -> round2; score
```

**Isolation.** Each packet holds only the tool's own output: questions,
rubrics, inputs, page text, shared inputs, the evidence files they point to (copied from
`run://`), and the `tobi_answer_questions` description. Local URLs are mapped to
`https://example.gov/site/pageN.html` and folders are shuffled `qNN` IDs,
because fixture names describe the expected answer ("key-in-comment-only").
The answer key (`/tmp/eval/state.json`) is outside the packet tree. Agents
are told to open nothing else and to list every file they opened.

**Pictures (post-round 1 fix 19).** A fourth argument picks how the
packets give pictures: `all` (the default: copied in, as before), `none`
(left as `run://` links the agent cannot open, as for a real agent that
does not read them) or `retry` (as `none`, then each look-to-settle
question answered "unsure" comes back once with its pictures). The arm is
kept in `OUT/images.txt`. `TESTS` may be `all`:

```bash
uv run python evals/judge_eval.py prepare /tmp/eval-none all none
```

## Judging rounds: real pages against a tester's blind SCRT files

A certified tester running their own round: follow
[docs/how-to/run-a-judging-round.md](../docs/how-to/run-a-judging-round.md).

A round can be scored two ways, both against the same keys by commit and
reveal: the scan below (a script drives the tool; one agent fills in the
question packets), or the agent eval (`agent/README.md`: a model drives the
tool itself, beside a Playwright MCP baseline, on frozen copies of the
pages). Round 1 uses the agent eval.

`evals/judging.py` scores the tool on real .gov pages against a certified
Trusted Tester's SCRT files, by commit and reveal, so neither the tool nor
its developers see the pages or the answers first.

1. **Start a round.** The tester commits `evals/judging/<round>/pages.txt`
   when testing begins (not earlier: a page list in the repository lets
   development prepare for it). One page per line, its URL and the SHA-256
   of their SCRT file for it, in either order; `#` comments allowed. Hash
   the exact file to be uploaded (`shasum -a 256 *.json`, `sha256sum *.json`
   or `Get-FileHash *.json`) and do not re-save it in SCRT afterwards.
2. **Scan.** `uv run python evals/judging.py scan evals/judging/<round>`
   runs every implemented test on each page, with the round's other pages
   on the same host as `other_pages` (9.A-9.C, 19.A). In a container, set
   `BROWSER_CHANNEL=chromium HEADLESS=true`. The real allowlist applies.
3. **Answer.** ONE fresh agent answers every
   `<round>/packets/pNN/roundK/questions.json` into `answers.json` in the
   same folder, opening nothing else; then `apply`. Repeat until no page is
   open.
4. **Lock.** `uv run python evals/judging.py lock evals/judging/<round>`,
   then commit `results/` (reports, pre-SCRT files, HARs, `lock.json`).
5. **Reveal.** The tester adds their SCRT files to `<round>/keys/` (any
   names: they are matched to pages by hash) and commits.
6. **Score.** `uv run python evals/judging.py score evals/judging/<round>`
   writes `score.md` and `score.json` (scoring: `evals/scoring.py`, on the
   neutral comparison in `src/tobi508/compare.py`). It stops if a key
   matches no page, if a key's page (`P_Location`) names a different page
   than its line in `pages.txt`, or if `pages.txt`, a result or the scoring
   code changed after the lock (to score with older code, check out the lock
   commit). The rates open with how many pages were scored and why any were
   not. Add a line for
   the round below. Do not copy figures into `docs/hackathon/evaluation.md`
   until a final round is chosen.

Tests the tool does not perform yet, and tests the tester left blank, are
counted apart, never as agreement or disagreement.

**Freezing pages (later rounds).** Round 1 was tested live on the day of
the scan. Pages change, so later rounds record each page on the day the
tester tests it and scan that recording. Until a `freeze` command exists, in
Chrome: DevTools, Network tab, tick "Preserve log" and "Disable cache",
reload the page, then right-click a request and "Save all as HAR with
content". Whether a DevTools HAR replays like our own recordings is not yet
checked.

**Validated catches (Abby, 2026-11-06).** After the reveal, the tester may
confirm that the tool was right where it differed from their key (round 1:
Artemis III 4.D, a player button with no visible focus). They record it in
`<round>/adjudications.json` (page, TT test, the confirmed result, who,
when, why), never by editing a key, which is locked by its hash. The scorer
counts a tool result that matches as a **validated catch**, weighted +1 like
an agreement and shown apart (`evals/scoring.py`). The file sits outside
the lock, as the keys do.

## Run 28, 2026-11-07: reading questions without pictures (2.D 1.1.0, 5.F 1.3.0), their packets

2.D J1 and J2 and 5.F J1 are settled by reading, so their pictures moved from the question input to evidence only (Abby, 2026-11-07); the agent is no longer asked to say what a picture shows for them. 5.F J2 (the field's look) keeps its pictures. 19 cases (2 2.D, 17 5.F, one with a follow-up round), one fresh Sonnet agent: **19/19 match**, no false PASS, no answer refused. It opened pictures only for the 5.F J2 questions, which name them.
- **Limit:** both 2.D cases expect PASS, so no fixture checks a 2.D not_sufficient answer without the picture.
- **Rules:** it used one read-only Bash call and Grep inside the packets, against its instructions (Read, Write and Glob only); the follow-up round used only the allowed tools.
- **Unclear to it:** whether "Go" in 5.F f11 is a search or filter button (it picked "Send my question", which matches); "Enter your full name" as a reference to the Full name field (it answered described, which matches).

## Runs 26 and 27, 2026-11-07: 9.C 1.1.1 (when names show different things), its packets

The rubric now says names that name different things count as
different_function, and different words for the same action are
inconsistent. 2 cases, 4 questions, one fresh Sonnet agent each run.
- **Run 26:** 2/2, but the rubric's examples ("Contact" / "Get in touch",
  "Search" / "Find") were the fixture pairs themselves. The agent said "the
  rubric names this exact pair", so the run tested matching, not
  judgment.
- **Run 27:** the examples were changed to names on no fixture page.
  **2/2 match**, no false PASS, each answer reasoned from the evidence:
  same destination with different words is inconsistent; different
  destinations are different_function.

Still unclear to the agent: links named "Go to page N" whose number does
not match where they go. It followed the different-destination rule,
which matches.

## Run 25, 2026-11-07: compact question inputs (4.F, 5.B packets)

After the result refactor (agent follow-through change 2b), question
inputs as sent round coordinates to one decimal and leave out empty fields.
33 cases (11 4.F, 22 5.B), one fresh Sonnet agent: **33/33 match**, no
false PASS. It opened every picture and found each one readable.

What it found unclear:
- **Where 5.B puts numbers:** the question says "in elements", but the
  `element` field's description says "from input.stops".
- **4.F main content before a left sidebar:** the rubric does not say how
  to treat main content reached before a left-hand sidebar.
- **4.F menu skipped by the next Tab:** the rubric does not say whether a
  menu whose content the next Tab skips counts as reached far from its
  trigger. It answered does_not_preserve, which matches.

## Run 24, 2026-11-06: `seen` and `picture_error` (4.D, 4.F, 5.A, 5.C packets)

Answers to a question whose input names a picture now need `seen`
(something the picture shows), or `picture_error` with unsure; a bare
answer is refused (agent follow-through plan, change 3). 29 cases, one
fresh Sonnet agent: **29/29 match**, no false PASS, no answer refused. It
opened every picture, filled `seen` with what the numbered or outlined
elements showed, and never needed `picture_error`. It used Bash once
(read-only, a packet file) against its instructions. Points it raised:
- **Shared texts are easy to miss.** About half the cases point to
  `question_texts`.
- **The `answer_format` line is long.** Read shows it on every packet file.
- **`choice.quote`:** whether it is needed for "labeled" or "missing" is
  not said.
- **Close calls it flagged:** 5.A's "Find an office" heading over a field
  with only a Find button (it answered not_labeled), and a sidebar order
  in 4.F (preserves). Both match.

## Run 23, 2026-11-06: 5.C 1.3.0 (the heading over an option), its packets only

J1's input now gives an option's heading (`heading_over_it`,
`heading_over_them`) and its rubric names a heading that is the question
of a set (an example not on any fixture page, "Delivery speed"). 6 cases,
one fresh Sonnet agent: **6/6 match**, no false PASS. On F19 it answered the
set's one question `missing`, quoting the heading "Mission status", which
now reaches M7 (FAIL), as Abby judged NASA's Missions page. It read every
shared question through `question_texts` without trouble. It also used
Grep once on a packet file, within the packet.

## Run 22, 2026-11-06: 5.C 1.2.0 (options of one set asked once), its packets only

6 cases, one fresh Sonnet agent, Read/Write/Glob only. **6/6 match** after
one expectation was corrected: on the new F19 (three filter boxes under the
heading "Mission status") it answered the set's one question `missing`,
quoting the heading, where the test data had said `complete`. Its reading
is the careful one (the rubric counts a heading whose absence could
confuse), so F19 now expects that answer. Because pass L does not count a
heading as text beside a field, M7's quote check cannot pass and each box
is M9 (NEEDS REVIEW, safe). That is a spec gap for Abby: NASA's Missions
page, which the key fails on 5.C, would stay NEEDS REVIEW this way. It
found the grouped question clear.

## Run 21, 2026-11-05: the pointer wording (5.D), its packets only

After run 20, a shared question's `question` and `rubric` say where the
text is. 15 cases; one fresh Sonnet agent, Read/Write/Glob only: **14/14
scored match** (F10's follow-up left open), none unsure. It found the
shared text through the pointer ("clear once I did"). It also noticed that
5.D J1's rubric example "Choosing a state takes you to its page" is the
very sentence on fixture F02 (and F07's page): the eval gives that answer
away. Fixed after the run: F02 and F06 are reworded, so no fixture page repeats
a rubric example.

## Run 20, 2026-11-05: shared question texts (5.C, 5.D), their packets only

Packets now carry `question_texts`, as a client gets them (post-round 1
fix 6b): a question that shares its question and rubric with others in its
run names a key there instead. 20 cases; one fresh Sonnet agent: **19/19
scored match** (5.D F10's follow-up round left open), none unsure. It
answered the shared questions correctly but said their `question` and
`rubric` were empty and that it took the text from sibling packets: it
had not seen `question_texts` in the same file. So a shared question's
fields now say where its text is (`Shared with other questions: read
question_texts["5.D-J1"].question.`). It also wrote its answers with one
Bash call, against its instructions (it opened nothing outside the
packets).

## Run 19, 2026-11-05: fix 19's picture arms (4.A, 4.D, 4.F, 5.A-5.D)

The same 71 cases prepared three ways (`all`, `none`, `retry`), each
answered by one fresh Sonnet agent with the same prompt; `retry`'s first
round reused `none`'s answers (identical packets), then a fresh agent
answered its picture round (5 packets). 70 cases scored in each arm (5.D
F10's follow-up round left open in all three).

| Arm | Match | False PASS | False FAIL | Unsure | Agent tokens |
| --- | --- | --- | --- | --- | --- |
| `all` (pictures from the start) | 67 | 0 | 0 | 3 | about 296k |
| `none` (`run://` links only) | 64 | 0 | 1 | 6 | about 300k |
| `retry` (pictures for unsure answers) | 69 | 0 | 1 | 0 | about 300k + 96k |

- Without pictures the agent answered 5.A F09 (a magnifier icon is the
  search box's label) `not_labeled`, sure of itself: a false FAIL. The
  retry arm cannot catch it, since only unsure answers come back.
- The retry round settled all 5 of its unsure answers correctly (two 4.F
  orders, 4.A, two 5.B forms).
- Pictures cost little here: `all` used about as many tokens as `none`
  (each agent's fixed start-up and the questions dominate). The retry
  round's 96k is mostly a new agent's start-up; in real use the same
  agent would answer it.
- The `all` arm's three mismatches are unsure answers (NEEDS REVIEW), so
  the arms differ by agent as much as by pictures: one run per arm.

## Run 18, 2026-11-05: post-round 1 fixes (4.F, 5.A, 5.B, 5.D), their packets only

`prepare OUT 4.F,5.A,5.B,5.D` (images `all`): 61 cases ask questions,
including the new F15 (5.D: one J1 for four filter boxes) and F16 and F17
(4.F: a site overlay; a card grid). One fresh Sonnet agent, file tools
only, answered all 61 (about 223k tokens), then a second answered 5.D
F10's follow-up round. **60/61 match, no false PASS.**
- 5.D F15: `not_told` for the four boxes at once (FAIL, as expected).
- 4.F F17: `preserves` for a card grid read row by row (the rubric's new
  line), PASS.
- 4.F F16: `does_not_preserve` where the test data said `preserves`:
  after the menu opens, the next Tab lands in the overlay, which sits
  between the button and its menu. The agent is right, and F16 now
  expects FAIL through J1. The fix (no mechanical M2 for a dialog the
  menu did not open) is unchanged.
- It opened only packet files, and each 4.F order image and 5.A image a
  question named.

## Run 17, 2026-11-04: 2.A (draft spec 0.2.0), its packets only

`prepare OUT 2.A`: one case asks a question (2.A asks none of its own):
the page's first text, "Press Ctrl+Shift+M to mute the sound." (J2).
Preparing it showed that 2.A had borrowed 2.C's J2 wording ("pause, stop,
hide or slow"), which leaves out muting and the volume that 2.A's ER 1
counts: a careful agent could have answered no, a false FAIL. 2.A now has
its own J2 ("pause or stop that audio, or turn its volume down or mute
it"). Leak grep clean. One fresh Sonnet agent, told to use file tools
only: **1/1 match**: describes, key Ctrl+Shift+M; the tool pressed it once
and the audio was muted (K4, then E3, gated). It opened only packet
files.

## Run 16, 2026-11-04: 2.B (draft spec 0.2.0), its packets only

`prepare OUT 2.B`: 7 cases ask questions (`test_fixtures_2b.EVAL`): an
infinite spinning badge, a marquee, a two-colour blink, a four-colour
cycle, a sliding carousel, a badge with a "Pause animation" button (J2 in
round 2, after the probe found it works) and a badge below the first
screen. Leak grep clean. One fresh Sonnet agent, told to start no
sub-agents and write no scripts (about 100,000 tokens, 34 s, plus round
2): **7/7 match, no false PASS, no false DNA.** Every J1 was not essential
except the badge below the first screen, which it answered unsure: no
frame shows it (A5, NEEDS REVIEW, as intended; a crop of the content
itself would let J1 settle it, a follow-up). Its least sure calls: the two
spinning squares, which could be loading indicators; the usable page
around them decided it. It read one file through a shell one-liner and
wrote the answers with printf, against its instructions (no file saved
outside the packets).

## Run 15, 2026-11-04: 2.C and 2.D (draft specs 0.3.0 and 0.2.0), their packets only

`prepare OUT 2.C,2.D`: 10 cases ask questions: 5 ACT efbfc7 cases (four
J1 on a working Stop, Pause or Hide button; passed 5's J2 on "activate the
"Control changes" button"), and 6 custom pages in `tests/fixtures/2x/`
(`test_fixtures_2x.EVAL`): pause, "Update less often", "Options" (works,
not evident: the false-PASS check), a hotkey named in the first text (J2,
then J1 after the tool pressed it, round 2), focus moved to "New message
4 from Ana" (2.D J1) and a dialog "Prices were updated." (2.D J2). Before
the run, 2.C J1 had no image although its question named "image A": it
now carries pass T's first frame, the control's box and where it is in
words. Leak grep clean (the only hit is 2.D J1's own example, "New
message from Ana", which the fixture echoes, so that case is easy). One
fresh Sonnet agent, told to start no sub-agents and write no scripts
(about 99,000 tokens, 30 s, plus round 2): **10/10 match, no false PASS.**
"Options" was not evident. Its least sure call was passed 5's J2, which
it answered unsure: the text names a button but not what it does (NEEDS
REVIEW either way, K8 instead of K5). For the hotkey's J1 it noted the
mechanism is text naming a key, not a button, and judged it evident by
the rubric: J1's wording ("Pressing input.mechanism") fits controls
better than text; a follow-up for the 2.C spec. It opened only packet
files; it wrote the ten answers with one shell command.

## Run 14, 2026-11-02: 5.B 1.1.0 after the merge, its packets only

`prepare OUT 5.B` after 5.B 1.1.0 (an option in a set no longer takes the
legend as its label). 23 cases ask questions; leak grep clean. One fresh
Sonnet agent, told to start no sub-agents (about 154,000 tokens, 7 min):
23/23 match, no false PASS, no follow-up round. Its least sure calls:
duplicate "Name"/"Street" labels told apart by visible "Shipping"/"Billing"
headings (descriptive) against the same labels with no heading (not); a
field whose only visible label is "Go". **Coverage gap:** no packet has a
radio button or checkbox, so this run shows 5.B's cases still hold but does
not exercise the 1.1.0 change itself.

## Run 13, 2026-11-02: 5.A 1.1.0 after the rubric fix, its packets only

`prepare OUT 5.A`, fresh packets after run 12's two fixes. 13 of the cases
ask questions (16 questions); leak grep clean. One fresh Sonnet agent, told
to start no sub-agents (about 102,000 tokens, 2 min): 13/13 match, no false
PASS, no follow-up round. It called the "Find" and "Subscribe" fields
not_labeled ("names the action, not the field content"), the "Search"
button's box labeled, and quoted "Official Name:" (now matched on its
words). Least sure: the search box whose placeholder and button both say
"Search". It opened only packet files and used only Read and Write.

## Run 12, 2026-11-02: 5.A and 5.C 1.1.0 (PR #3 review fixes), their packets only

`prepare OUT 5.A,5.C` after 5.A J1's input gained `buttons_next_to_it` and
`question_of_the_set` (spec 1.1.0). 18 cases ask questions; leak grep clean.
One fresh Sonnet agent (it split the work across four sub-agents of its
own; about 49,000 tokens reported): **15/18, two false PASS.** With the
buttons beside a field shown and the rubric's only example "a Search button
beside a search box", it counted "Subscribe" (f01) and "Find" (f02) as
labels. Fix: the rubric now says a button counts only when its words say
what to type into the field, and names action words that do not. The third
miss (TC10.A-all-pass-6, NEEDS REVIEW for PASS) was the quote check: the
page shows "Official Name" and ":" as two pieces of text and the agent
quoted "Official Name:"; a quote now also matches on its words (M4). The
scripted tests could not see either problem: they answer as a correct judge
would.
## Run 11, 2026-11-02: 5.H after J2 named G155 and G168, its packets only

G155 (a required confirm checkbox) and G168 (an "Are you sure?"
confirmation) had been listed in the plan but not read; J2's rubric did not
name them, so a form confirming that way could have been judged "none" (a
false FAIL). The rubric and question now name both, with a fixture for
each (f06, f07). `prepare OUT 5.H`: 9 cases ask questions. One fresh
Sonnet agent, two rounds (about 100,000 tokens): 9/9 match, no false PASS;
it judged the dialog and the checkbox review_step. It read the packets with
one read-only Python snippet against its instructions; nothing outside the
packets was opened.

## Run 10, 2026-11-02: 5.B and 5.H (draft specs 0.1.0), their packets only

`prepare OUT 5.B,5.H`: 30 of the cases ask questions (5.B asks one question
per form on every labelled form; 5.H only when a form hints at
consequences): 16 ACT cc0f0a cases, the TC10.A/E and TC10.G Baseline
cases, and the custom 5.H pages. Leak grep clean. One fresh Sonnet agent
(about 127,000 tokens for round 1, 140 s; it also answered the four 5.H J2
follow-ups in round 2): 30/30 match, no false PASS. 5.B used the field
images (it saw the "Shipping"/"Billing" headings that make repeated
"Name" labels descriptive, and their absence when they are off screen).
Its least certain calls: a "step 1 of 3" form with a Next button that
leaves the recorded page (judged multi_step, then unsure about J2, which is
NEEDS REVIEW as intended). It opened only packet files, listed the folders
with one shell command, and wrote no scripts.

## Run 9, 2026-11-02: 19.A (draft spec 0.1.0), its packets only

`prepare OUT 19.A`: 2 of the 9 cases ask J1 (is the page a step in a
process?): a review step ("Step 2 of 3") and a contact form whose intro
says "Thank you for your interest" (hinted, not a process). One fresh
Sonnet agent (about 72,000 tokens, 13 s), told to use no scripts: 2/2
match, no false PASS. It opened only packet files and wrote none outside
them.

## Run 8, 2026-11-02: 9.A, 9.B and 9.C (draft specs 0.1.0), their packets only

`prepare OUT 9.A,9.B,9.C`. Cases now carry other pages (`pages`: the ACT
cases are compared with the rules' chapter2.html, the custom cases with
their sibling pages in `tests/fixtures/9x/`); `NOT_EVAL` in
`test_fixtures_9x.py` leaves out one rules-only case (the same page and
question as another, with the opposite scripted answer). 4 of the 47 cases
ask questions (9.A and 9.B decide almost everything mechanically; 9.B asks
nothing); leak grep clean. One fresh Sonnet agent (about 76,000 tokens,
32 s): 4/4 match, no false PASS, no follow-up round. 9.A J1 named Alt+S
with its quote; 9.A J2 judged a "Start / Benefits overview" trail as
repeated (the agent's least certain answer: no breadcrumb landmark, it went
by the links and separator); 9.C J1 judged "Go to page 3/4" and "5/6"
consistent, "Contact"/"Get in touch" and "Search"/"Find" inconsistent. It
opened only packet files; it read and wrote them with inline Python, which
its instructions said not to do (no file was saved).

## Run 7, 2026-11-01: 5.A and 5.C (draft specs 0.4.0 and 0.3.0), their packets only

`prepare /tmp/eval 5.A,5.C`; f12 runs with 4.F (its pass R reveals the
field), and packets hold only the case's own test's questions. 16 of the
50 cases ask questions (5.C decides most pages mechanically); leak grep
clean. One fresh Sonnet agent (about 89,000 tokens, 44 s): 16/16 match, no
false PASS, no follow-up round. It opened only packet files and wrote no
scratch file (it printed and wrote with inline Python). Borderline calls
it listed: a field named only by its table header judged complete; a red
"*" on a field without `required` judged missing; on the floating-label
page it read the small "ZIP code" label in the image as the label.

## Run 6, 2026-11-01: 5.F and 5.G at 1.0.0, their packets only

After Abby's review: a plain "Save" is a submit control again (f09 back to
"Save", f12 new), native date fields get a date outside their range in
attempt 2 (f13 `max`, f14 a birth date checked by script), and a date
field is read through its input (it had been dropped from its form: a
false DNA). 33 of 5.F's and 5.G's 42 cases ask questions; leak grep clean.
One fresh Sonnet agent (about 94,000 tokens, 171 s; then 9 s for f11's two
round-2 packets after J0's rerun): 33/33 match, no false PASS. It opened
only packet files; it wrote a scratch file (`/tmp/dump.txt`) and deleted
it, against its instructions, as agents did in runs 1 and 5. Borderline
calls it listed: instruction-style messages ("City: enter the city ...")
judged described; a valid "abc" name with only the ZIP code's error listed
judged no_error.

## 2026-11-01: shared replays and 4.A 1.2.0, no agent run needed

4.A now reuses 4.D's pass W arrows and 4.F's pass R Enter presses, and
treats native date-input parts as native (4.A 1.2.0). Packets for every
Test 4 fixture were built on main and on the branch and compared case by
case (`questions.json`, run IDs normalised): all 45 that ask questions
are identical, so no question or input changed.

## Run 5, 2026-11-01: 5.F and 5.G (draft specs), their packets only

`prepare /tmp/eval 5.F,5.G` (the new optional test list). 28 of 5.F's and
5.G's 36 cases ask questions (11 custom pages and the 7 TC10.D Baseline
cases, each for both tests). Leak grep (local hosts, fixture names, case
IDs): no match.

**First agent** (Sonnet, about 87,000 tokens, 74 s): 25/26 scored match,
no false PASS. The miss, 5.F f10 ("Date of birth: invalid entry."): the
agent answered not_described (FAIL), but the PDF's own example of a
description is "the Password you entered is incorrect" (p. 28 HtT 3.b).
J1's rubric now says that saying the value is incorrect or invalid is
enough (what to enter instead is 5.G); J0's rubric now excludes the
control already pressed (the agent asked). 5.F spec 0.5.0.

**Second agent** on the rebuilt packets (about 95,000 tokens, 77 s, then 8 s
for the two round-2 packets after J0's rerun): 28/28 match, no false PASS
(5.F: 4 FAIL, 9 PASS, 1 DNA; 5.G: 3 FAIL, 9 PASS, 1 DNA, plus the f11
pair after J0 picked "Send my question"). It opened only packet files; it
wrote one scratch file outside the packets (`/tmp/dump.txt`, removed),
as an agent did in run 1. Borderline calls it listed: instruction-style
messages ("Enter your full name", "City: enter the city ...") judged
described (G83: a text description identifying the field not completed);
"Error: not a number." on an empty number field judged described (5.F) and
guides (5.G).

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
