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
`a11y_answer_questions` and scores. Run it after any change to a question, rubric
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
