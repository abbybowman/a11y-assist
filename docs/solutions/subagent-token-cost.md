# A subagent per question costs far more than it saves

**Measured** (judge eval, 2026-10-31, Sonnet subagents, the tool's real
output): an open question's own content is about 600 tokens, but each
subagent's start-up costs about 55,000 tokens. 48 subagents (one per page)
used about 2.7 million tokens; one subagent for all 44 pages used about
96,000 (plus 63,000 for a second one with only two follow-up questions).
Parallel agents finished sooner (8–20 s each); the single agent took 77 s.

**What we do.** The tool descriptions tell consumers to hand all of a run's
open questions to one subagent and keep only the answer objects, and to
answer one or two short questions directly. Our own evals use one agent per
round. Figures are the per-agent token counts the harness reports, summed;
billed usage was not checked.
