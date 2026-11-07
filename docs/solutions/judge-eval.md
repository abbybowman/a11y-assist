# Scripted answers test the rules, not the questions

**Problem.** Every fixture test answers open questions with a scripted
answer (what a correct judge would say). That proves the rows turn answers
into outcomes. It cannot show whether an agent, reading only the tool's
output, would give that answer. The first judge eval (2026-10-31) found a
false PASS (4.F f14: the question never mentioned the backward order, so the
agent judged the forward order only), five safe "unsure"s caused by missing
evidence, screenshots sent as paths no client could open, and one fixture
whose scripted answer was wrong (4.F f15).

**What we do.** `evals/judge_eval.py` builds a packet per page from the real
tool output, a fresh agent answers it, and `apply` sends the answers through
`tobi_answer_questions` and scores. Run it after any change to a question, rubric
or question input (CLAUDE.md principle 6).

**Leaks we had to close** (each would have handed the agent the answer):
- Fixture file names in link addresses, page-text sources and evidence
  (`f09-key-in-comment-only`): every local URL becomes
  `https://example.gov/site/pageN.html`. Cross-origin fixtures use
  `localhost`, so scrub that too.
- Packet folder names: shuffled `qNN` IDs, not case names.
- The answer key: kept outside the packet tree (`/tmp/eval` vs
  `/tmp/eval-packets`), never in a parent folder of a packet.
- Check with a grep for `127.0.0.1|localhost|/4[a-f]/f[0-9]|fail-1|act-rules`
  before launching agents (zero matches).

**What an agent needs, learned from its "unsure"s.** Everything the rubric
mentions must be in the input (the backward order, what a menu revealed,
what a key press changed); a note that does not apply (a "walk incomplete"
note on a page with nothing focusable) makes agents doubt good evidence;
when no answer is possible except one (no stops at all, so no keyboard
alternative), decide it mechanically instead of asking.

**Isolation is by instruction.** Agents are told to open nothing outside
their packet and to list what they opened; all did. One wrote a helper
script outside the packets. A sandboxed runner is on the roadmap.

**A rubric's only example becomes the rule.** 5.A 1.1.0 showed the agent
the buttons beside a field, with one example: "a Search button beside a
search box". The agent then counted "Subscribe" and "Find" as labels, two
false PASSes (evals/README.md run 12). Naming the cases that do not count
("Go", "Find", "Submit", "Subscribe" only say what the button does) fixed
it (run 13). When an input field is added to a question, give an example
on each side of the line.

**The judge eval hands images over as files; a real agent gets links it
rarely opens** (round1-answers, 2026-11-04).
- **The difference:** packets copy each `run://` image into the packet
  folder, so a judge-eval agent opens it like any file. In real use the
  question names `run://…png`, which only the client's MCP read-resource
  tool opens.
- **What happened:** told to answer every question, Agent A viewed 2
  screenshots across two runs (both 5.A), tried its file `Read` on a
  `run://` link 3 times (refused), and never opened a 4.F order image. All
  of its 4.F answers were "unsure, cannot settle", with no reason given.
- **So** the judge eval measures answers with the evidence in hand, and
  overstates how often a real agent answers a question that needs
  looking. To measure the real path, use an agent eval run (or an
  answering run), not the judge eval. Post-round 1 plan, fix 19.

**Rubric examples must not be a fixture's own words (runs 26-27,
2026-11-07).** When 9.C's rubric example was the fixture's pair, the agent
said "the rubric names this exact pair", and the eval measured matching.
Grep `tests/fixtures/` for an example before using it. See
[agent-follow-through.md](agent-follow-through.md).
