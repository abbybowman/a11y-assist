# Agent eval: running a round

Agent A (a model with this MCP server) and Agent B (the same model with
Playwright MCP) test the same frozen pages with the same prompt. Their
results are scored against a tester's SCRT files by commit and reveal.
Plan: [docs/plans/2026-10-31-agent-eval.md](../../docs/plans/2026-10-31-agent-eval.md).
Lessons: [docs/solutions/agent-eval-harness.md](../../docs/solutions/agent-eval-harness.md).

Results are agent-assisted, not certified Trusted Tester results.

**Status:** every step below is tested on the 19.A fixture site with a
scripted model (`tests/test_agent_*.py`). The CLI route was also
smoke-run on that site with Sonnet 5.5 (2026-11-04, both arms; it checks
the plumbing, not accuracy). Nothing has run on real pages, on the Ask
Sage route, or on Windows. Steps 1 and 2 need no model.

## Once per machine

```bash
uv sync --group dev
```

```bash
npm ci --prefix evals/agent/node
```

The second command installs Playwright MCP, pinned in
`evals/agent/node/package.json` and `package-lock.json`.

Then set the model route in the root `.env` (git-ignored) or the
environment:

```
AGENT_API_BASE=https://api.asksage.ai.nasa.gov/server/anthropic
AGENT_API_KEY=...
AGENT_API_AUTH_HEADER=...   # the header Ask Sage takes the token in (default x-api-key)
AGENT_MODEL=claude-sonnet-5-5-gov
AGENT_LEAK_VALUES=...       # optional, comma-separated: values the leak check must not see
```

## Routes

- `--route api` (default): an Anthropic-style API, Ask Sage on NASA's
  network. Set the `AGENT_*` variables above.
- `--route cli`: the Claude Code CLI on the claude.ai account, from a
  cloud session (a laptop's Claude Code goes through Ask Sage). Each arm
  runs as an isolated `claude -p` (`cli.py`). Nothing to set; `--model`
  defaults to `claude-sonnet-5-5`. Every run logs the account's usage
  windows (`rate_limit` rows in `steps.jsonl`, `usage_windows` in the
  summary), so a large arm can start at the beginning of a fresh window.

Both arms of a round use the same route.

In a cloud session, set `UPSTREAM_PROXY="$HTTPS_PROXY"` for the freeze and
both arms. The container re-signs direct connections with a certificate
Chromium does not trust, so live pages would load without their CSS and
scripts (`docs/solutions/agent-eval-harness.md`). On a laptop, leave it unset.

## A round, in commit order

Round folder `evals/judging/<round>/`, for example `evals/judging/round1/`.

1. **Start.** The tester commits `pages.txt` (each URL with the SHA-256 of
   their SCRT file for it) when testing begins.
2. **Freeze.** This is the only step that touches the live site:

   ```bash
   BROWSER_CHANNEL=chromium HEADLESS=true uv run python -m evals.agent.freeze evals/judging/<round>
   ```

   It records the tested pages only, into `frozen/` (an index, the
   recordings and `freeze.json`). Check that every page says `frozen`, and
   compare each frozen page's footer timestamp with your own testing.
   During the arms, the tested pages come only from these copies; other
   pages of the same site (site maps, search results) load live for both
   arms, so run the two arms close together.
3. **Agent A, then Agent B:**

   ```bash
   uv run python -m evals.agent.run --route cli --arm a evals/judging/<round>
   ```

   ```bash
   uv run python -m evals.agent.run --route cli --arm b evals/judging/<round>
   ```

   (`--route api` for Ask Sage.)

   Each run writes `results/arm-<a|b>/`: `steps.jsonl`, `transcript.json`,
   `final.md`, `summary.json`; for Agent A the tool's own runs in `runs/`
   (with each live page it loaded); for Agent B `live.jsonl` (each live page
   and each refusal). A run first checks that the model's context holds nothing of
   the user or this repo, and stops if it does.
4. **Archive, then lock**, then commit. Page recordings, screenshots and
   tool evidence never go in git (`.gitignore`); zip the round folder with
   a SHA-256 manifest and keep it outside git, as round 1 did
   (`evals/judging/round1/results/ARCHIVE.md`). Then:

   ```bash
   uv run python evals/judging.py lock evals/judging/<round>
   ```

   The lock hashes `pages.txt`, `frozen/`, every result file and the
   scoring code.
5. **Reveal.** The tester adds their SCRT files to `keys/` and commits.
6. **Score:**

   ```bash
   uv run python -m evals.agent.score evals/judging/<round>
   ```

   It writes `agent-score.md` and `agent-score.json`: each arm per WCAG 2.0
   criterion, Agent A's tool per TT test, the weighted scores, each Fail's
   elements, and tokens, wall time and tool calls.

## Results

### Round 1 (nasa.gov, scored 2026-11-04)

Agent-assisted results, scored against Abby's blind SCRT files (9 pages,
TT 4.A-4.F, 5.A-5.H, 9.A-9.C, 19.A). Not certified Trusted Tester results.
Files: `evals/judging/round1/agent-score.md` and `.json`, from the locked
scoring code (`results/lock.json`, code commit 7d26a02). nasa.gov is a
development site from now on and is never scored again (eval plan 3.1).
Fixes are in
[the post-round 1 plan](../../docs/plans/2026-11-04-post-round1-fixes.md).

**Scoring checks on the first real keys.** The scorer ran unchanged. All 9
keys matched their pages by hash and passed the P_Location check. The
criteria roll up from the intended TT tests (1.3.1 and 4.1.2 from 5.C only;
2.4.6 from 5.B only). `arm-a-1` and `arm-a-2` are scored on 8 pages:
`arm-a-1` was given the typo URL (`/search?=artemis`), and `arm-a-2` lists
the search page in `not_scored.json` with its reason. `arm-a-3` has no tool
report for Missions (refused, never retried), so the tool is scored on 8
pages there.

**Per WCAG 2.0 criterion, what each agent reported** (weights: agree +1,
needs review 0, false PASS -3, other errors -1):

| Run | Weighted | Agree (of decided) | Needs review | False PASS | False FAIL | Other | Key Fails reported as Fail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A-1 (8 pages) | 40 | 44/48 | 88/136 | 0 | 4 | 0 | 9 of 26 |
| A-2 (8 pages) | 40 | 42/44 | 92/136 | 0 | 2 | 0 | 9 of 26 |
| A-3 (9 pages) | 42 | 45/48 | 105/153 | 0 | 3 | 0 | 9 of 28 |
| B-1 (9 pages) | 20 | 86/112 | 41/153 | **20** | 0 | 6 | 0 of 28 |
| B-2 (9 pages) | 41 | 95/117 | 36/153 | **16** | 0 | 6 | 0 of 28 |

- **Agent A: no false PASS in any run.** Each run's 9 Fails are 2.4.1 on 7
  pages (no way to skip the header, which matches the key's reason) and
  2.4.7 on 2 pages. Across the three runs its 9 errors are all false FAILs: 7 on 2.4.7
  (4.D row M8), 1 on 2.4.3 (4.F row M2) and 1 the agent made up (below). It left
  about two thirds of the cells as needs review.
- **Agent B: no Fail anywhere, in either run.** Its errors are 36 false
  PASSes: 3.3.2 on every page (the site search's only label is its
  placeholder), 2.4.1 on 8 pages in B-1 (landmarks taken as a bypass),
  2.4.7 on 4 pages in B-2, 2.4.5 on the forms page, and 1.3.1 and 4.1.2 on
  Missions. Its "other" errors are Pass where the key says Does Not Apply
  (2.4.6 with no visible labels; 2.4.5 on the results page).
- **The weighted scores tie (A about 40, B-2 41) but measure different
  things.** A gains by deferring, B by passing pages that mostly pass.
  False PASS is the worst error: A 0, B 16-20.

**Agent A's tool, per TT test** (the tool's own pre-SCRT files, against the
key):

| Run | Weighted | Agree (of decided) | False PASS | False FAIL | NEEDS_REVIEW (scored as not performed) |
| --- | --- | --- | --- | --- | --- |
| A-1 | 44 | 48/52 | 0 | 4 | 84 |
| A-2 | 41 | 42/43 | 0 | 1 | 93 |
| A-3 | 47 | 49/51 | 0 | 2 | 85 |

- **Agreement where the tool decided:** 4.B, 4.C, 4.E, 9.A, 9.B and 9.C
  agree on every page they were decided for. 4.A agrees where decided (3
  pages). 5.C and 5.D agree on 2-3 pages each, and 5.H on 1-2.
- **Every false FAIL is 4.D row M8 or 4.F row M2.** M8 fails a focused
  element whose on and off pictures differ by 0 px (Artemis III: "NASA",
  "Hide player controls", "About Orion"; Careers: "Read More"; Missions: 7
  links in the A-Z list), where the key passes 4.D. The failing elements
  change from run to run on the same frozen page, so the measurement is
  unstable. 4.F M2 (`arm-a-1`, Careers): Tab left the "Internships" dialog;
  the key passes 4.F.
- **Why NEEDS_REVIEW,** by the finding's own summary (A-1 / A-2 / A-3):
  - time limit reached: 40 / 35 / 48;
  - open question not answered: 25 / 26 / 21;
  - a form sent to its server (5.F-5.H cannot see the reply): 12 / 12 / 6;
  - 19.A wants more pages: about 8 / 7 / 7;
  - images could not be compared, or a frame could not be read: a few each.

  The scorer files every NEEDS_REVIEW as "not performed": the checks put
  the note "This test could not be performed" on each one (spec rows G3 and
  similar), and the scorer reads that note. Both weigh 0, so the scores are
  unaffected.
- **The tool's rules versus the unanswered questions.** No run was wrong
  because a rule decided wrongly, apart from 4.D M8 and 4.F M2. The rest of
  the gap is time and the unanswered questions. One large case: the key
  fails 5.A on all 9 pages (the site search's only label is its
  placeholder). The tool sent it to an open question (J1) because the
  header's "Explore" button sits in the field's picture, and row M3's "no
  button's text beside it" counts any button. J1's rubric would answer
  `not_labeled` (FAIL), but nobody answered. Where the time limit came
  first, the field was never read (M1).

**The gap between the tool and what Agent A reported.** Agent A relayed
its tool faithfully: across the three runs, 1 cell where the tool said Does
Not Apply and the agent said needs review (`arm-a-1` and `arm-a-2`, 3.3.4,
forms page), and one Fail the agent made up. `arm-a-3` reported 3.2.2 Fail
on Spot the Station ("City select navigates on change, not announced"),
where the tool said NEEDS_REVIEW and the key says Pass. `arm-a-2`'s Missions
results came from two calls (six tests, then 9.A alone), and the scorer
reads only the latest. Its tool score therefore leaves out the six-test
call: 3 agreements and 1 false FAIL (4.D). With them, A-2's tool would score
47 decided, 45 agree and 2 false FAIL, a weighted 43. These figures come
from analysis outside the locked scorer, which refuses changed code.

**Elements.** Matching free-text elements to the key's is not automated.
For review:
- **2.4.1:** all three A runs name the header ("Explore, News & Events,
  Multimedia; no working skip link"), the key's reason. On Missions the key
  also names the long filter list, which no run mentioned.
- **2.4.7, news release:** A-1 and A-2 name the featured image link
  ("Looking up, three white and black fighter jets…"), which is the key's
  element. A-3 names it as well, plus two "needs check" items.
- **2.4.7, Spot the Station:** the outcome agrees, but on other elements
  ("Hide player controls", "NASA Johnson", "Watch Now"). The key's element
  (the linked image above the FAQ) was NEEDS_REVIEW in the tool (M4, no
  clear before-and-after view), not passed.
- **2.4.7, KSC gallery and NACA:** the key fails both for a tiny square of
  about 4x4 px. The tool never decided: images not compared on KSC, and the
  time limit on NACA.
- **Agent B:** reported no Fail, so it named no elements.

**Consistency, runs of one arm on the same pages.**
- **Agent A:** the three runs give the same answer on 122 of 136 cells. 7
  cells differ between A-1 and A-3, and 11 between A-2 and A-3. Every
  difference is Fail or Pass in one run against needs review in another,
  because time limits fell on different tests. Run to run, the failing 4.D
  elements differ too.
- **Agent B:** B-1 and B-2 agree on 128 of 153 cells. All 25 differences
  are Pass against needs review. On 2.4.1 the runs split: B-1 passed 8
  pages on landmarks, and B-2 left them for review.

**Efficiency** (list price; usage windows are whole percent and include
anything else on the account at the time):

| Run | Wall time | Output | Cache write | Cache read | Cost | 5-hour window | 7-day window |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A-1 | 1217 s | 15.6k | 154.9k | 349.5k | $0.81 | 13→21% | 64→66% |
| A-2 | 1246 s | 10.5k | 128.3k | 372.2k | $0.66 | 28→34% | 67→68% |
| A-3 | 1056 s | 16.2k | 158.4k | 491.9k | $0.84 | 69→76% | 74→75% |
| B-1 | 177 s | 16.4k | 40.4k | 872.5k | $0.41 | 50→51% | 71→71% |
| B-2 | 180 s | 19.2k | 43.5k | 1018.5k | $0.47 | 63→64% | 73→73% |

- **Cost:** Agent A costs about 1.7 times as much as B, and its usage-window
  change is several times larger. A's cost is cache writes, since every
  large tool result is written to the cache; B's tokens are mostly cheap
  cache reads.
- **Time:** A takes about 6 times as long. Nearly all of it is the server's
  browser work (8-10 calls at 100-183 s each). The model calls are 5-6, so
  little of the time is the model's.
- **The calls were not queued in the server.** The CLI kept each call in the
  foreground for 120 s and then moved it to the background, so the next call
  arrived about 2 minutes later. The server started each run as soon as it
  arrived (its browser launched within a second), so at most two runs
  overlapped. Each run's limit (120 s plus 20 s per other page) counted
  from its own start. The runs that hit the limit used all of it: these
  pages need more time than the budget allows.

**Caveats confirmed from the transcripts.**
- **Missions** (98 form fields) was refused in all three runs, with advice
  to set `no_time_limit`, and no run took it:
  - `arm-a-1` called again with every test but 5.D;
  - `arm-a-2` called again with six tests, then with 9.A alone;
  - `arm-a-3` never called again.

  So the key's Missions Fails (5.C, 5.D) were never tested.
- **Spot the Station:** `arm-a-1`'s first call crashed (a detached frame),
  and its retry with fewer other pages finished.
- **Both `arm-a-2` and `arm-a-3`** tried `Bash` to read a large result
  (refused); `arm-a-3` then used `Read` on the saved file.
