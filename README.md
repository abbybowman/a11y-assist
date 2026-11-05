# a11y-assist

> **Not a certified Trusted Tester result.** This tool produces agent-assisted
> findings only. Its output is not a DHS Trusted Tester certified test result
> and must not be reported, cited or relied on as one. A certified Trusted
> Tester must perform any test that counts for Section 508 conformance.

An MCP server that runs parts of the DHS Trusted Tester (TT) 5.1.3 Section 508
web test process in a real Chrome browser and reports findings by TT test
ID. Your agent calls it, answers the judgment questions it sends back, and
gets PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW per test, with evidence
and a pre-SCRT file a Trusted Tester can review. The package name is
provisional.

- **How it decides:** outcomes come only from the rules specs in
  [docs/rules/](docs/rules/), one per TT test, checked against the TT 5.1.3
  PDF.
- **When it can't decide,** the result is NEEDS REVIEW, never a guessed
  PASS.
- **Contributors:** read [CLAUDE.md](CLAUDE.md), then
  [docs/ROADMAP.md](docs/ROADMAP.md).

## TT tests in scope

The 17 implemented tests, each with its rules spec version and how its
results compared with a certified Trusted Tester's blind SCRT files. Every
other active TT 5.1.3 test is NEEDS REVIEW, with the note "This test could
not be performed".

| ID | TT test name | WCAG 2.0 | Spec | Round 1: agree · false PASS · false FAIL · undecided | Told to answer (unscored): same |
| --- | --- | --- | --- | --- | --- |
| 4.A | 2.1.1-keyboard-access | 2.1.1 | [1.2.1](docs/rules/4a-keyboard-access.md) | 8 · 0 · 0 · 16 | 4 · 0 · 0 · 5 |
| 4.B | 2.1.1-no-keystroke-timing | 2.1.1 | [1.2.0](docs/rules/4b-no-keystroke-timing.md) | 15 · 0 · 0 · 9 | 8 · 0 · 0 · 1 |
| 4.C | 2.1.2-no-keyboard-trap | 2.1.2 | [1.8.0](docs/rules/4c-no-keyboard-trap.md) | 18 · 0 · 0 · 6 | 9 · 0 · 0 · 0 |
| 4.D | 2.4.7-focus-visible | 2.4.7 | [1.1.1](docs/rules/4d-focus-visible.md) | 10 · 0 · 7 · 7 | 4 · 0 · 4 · 1 |
| 4.E | 3.2.1-on-focus | 3.2.1 | [1.1.0](docs/rules/4e-on-focus.md) | 16 · 0 · 0 · 8 | 9 · 0 · 0 · 0 |
| 4.F | 2.4.3-focus-order-meaning | 2.4.3 | [1.1.3](docs/rules/4f-focus-order-meaning.md) | 0 · 0 · 1 · 23 | 0 · 0 · 1 · 8 |
| 5.A | 3.3.2-label-provided | 3.3.2 | [1.1.0](docs/rules/5a-label-provided.md) | 0 · 0 · 0 · 24 | 9 · 0 · 0 · 0 |
| 5.B | 2.4.6-label-descriptive | 2.4.6 | [1.1.0](docs/rules/5b-label-descriptive.md) | 0 · 0 · 0 · 24 | 2 · 0 · 0 · 4 (3 other) |
| 5.C | 1.3.1-programmatic-label | 1.3.1, 4.1.2 | [1.1.0](docs/rules/5c-programmatic-label.md) | 6 · 0 · 0 · 18 | 4 · 0 · 0 · 5 |
| 5.D | 3.2.2-on-input | 3.2.2 | [1.0.0](docs/rules/5d-on-input.md) | 8 · 0 · 0 · 16 | 6 · 0 · 0 · 3 |
| 5.F | 3.3.1-error-identification | 3.3.1 | [1.1.0](docs/rules/5f-error-identification.md) | 0 · 0 · 0 · 24 | 0 · 0 · 0 · 9 |
| 5.G | 3.3.3-error-suggestion | 3.3.3 | [1.1.0](docs/rules/5g-error-suggestion.md) | 0 · 0 · 0 · 24 | 0 · 0 · 0 · 9 |
| 5.H | 3.3.4-error-prevention | 3.3.4 | [1.1.0](docs/rules/5h-error-prevention.md) | 5 · 0 · 0 · 19 | 9 · 0 · 0 · 0 |
| 9.A | 2.4.1-bypass-function | 2.4.1 | [1.0.0](docs/rules/9a-bypass.md) | 21 · 0 · 0 · 3 | 8 · 0 · 0 · 1 |
| 9.B | 3.2.3-consistent-navigation | 3.2.3 | [1.0.0](docs/rules/9b-consistent-navigation.md) | 24 · 0 · 0 · 0 | 9 · 0 · 0 · 0 |
| 9.C | 3.2.4-consistent-identification | 3.2.4 | [1.1.0](docs/rules/9c-consistent-identification.md) | 11 · 0 · 0 · 13 | 9 · 0 · 0 · 0 |
| 19.A | 2.4.5-multiple-ways | 2.4.5 | [1.1.0](docs/rules/19a-multiple-ways.md) | 0 · 0 · 0 · 24 | 0 · 0 · 0 · 9 |

**How to read the results columns.**
- **What was counted:** pages × runs, against the key, for the tool's own
  results (not what the agent then reported). "Undecided" is the tool's
  NEEDS REVIEW. `tests/test_readme.py` checks the names and spec versions.
- **Round 1** (scored 2026-11-04): 9 www.nasa.gov pages and 3 runs, 24
  page-runs in all. The agent did not answer the open questions, and many
  calls hit the time limit.
  - Results: [evals/agent/README.md](evals/agent/README.md#results).
  - The table comes from `uv run python -m evals.agent.per_test`. It counts
    one call more than the locked score: a run that split a page's tests
    across two calls.
- **Told to answer:** the same 9 pages, one development run told to answer
  every question and to use `no_time_limit`.
  - Analysis:
    [evals/judging/round1-answers/README.md](evals/judging/round1-answers/README.md).
  - It is unscored: nasa.gov is now a development site, so these figures are
    not a holdout result.
- **Why tests are still undecided** (post-round 1 plan:
  [docs/plans/2026-11-04-post-round1-fixes.md](docs/plans/2026-11-04-post-round1-fixes.md)):
  - 5.F and 5.G wait for a form's server reply;
  - 19.A waits for more pages;
  - 4.F's answers were mostly "unsure".

## Tools

| Tool | What it does | Main inputs |
| --- | --- | --- |
| `a11y_run_tt_tests` | Tests one page: records it once, then runs the chosen TT tests on the recording in Chrome. Returns findings with plain-language summaries, open questions for your agent, and links to the full report and pre-SCRT file. | `url` (allowlisted: `.gov` and `.mil` by default); `tests` (TT IDs; default: every implemented test); `other_pages` (1-5 other pages of the same site, for 9.A-9.C and 19.A; up to 50 with `no_time_limit`); `no_time_limit` (for a page the tool refused as too large) |
| `a11y_answer_questions` | Records your agent's (or a person's) answers to the open questions and decides again by the spec. A person's answer overrides the agent's. A key the answer names is pressed in the recorded page to check it. | `run_id`; `answers` (one per question: `question_id`, `rationale`, `decided_by`, and the answer object the question asks for) |
| `a11y_read_report` | Reads an SCRT file (from DHS's [SCRT](https://github.com/Section508Coordinators/SCRT)) or a pre-SCRT file: what failed, what still needs a person, who tested it. With `compare_to`, lists every test whose result differs between two files of the same page (for example, before and after a fix). | `content` (the file's text or a `run://` link); `compare_to` |

**Also:**
- **Resources:** `run://{run_id}/{path}` (a run's report, pre-SCRT file and
  evidence, kept 24 hours) and `tt://5.1.3/...` (the TT 5.1.3 text).
- **Prompt:** `explain`, a command that explains a test or a result in plain
  language.

Answers are facts, never outcomes: the spec turns them into an outcome.

## How long a call takes

- **One `a11y_run_tt_tests` call:** at most 120 s (`RUN_LIMIT_S`), plus 20 s
  for each other page (`OTHER_PAGE_S`). In round 1, calls on www.nasa.gov
  with 3 other pages took 100-183 s, and tests not finished in time come
  back NEEDS REVIEW with the reason.
- **Large pages:** a page with more than 40 form fields, or too large to Tab
  through, is refused at once with the advice to call again with
  `no_time_limit: true`. Then expect minutes: Missions (98 form fields) took
  15 min and the NACA feature 20 min.
- **Answering questions:** `a11y_answer_questions` usually takes under a
  second. It takes longer when it has to press a key in the recorded page.
- **Client settings:**
  - Claude Code cut MCP calls off at 60 s in our cloud tests. Set
    `MCP_TOOL_TIMEOUT` (ms) above your longest call.
  - It also moves a call that runs past 120 s to the background, and a
    headless (`claude -p`) session that then ends its turn loses the call.
    Set `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` too.
  - Both are checked only in a cloud container so far.
- **Batches:** run a few pages at a time. The server runs calls side by
  side, each with its own browser. On a 4-CPU, 15 GB machine, 3 at once ran
  normally, and 12 at once overloaded it: tests timed out and were left
  NEEDS REVIEW.

## Use it

### Setup (Windows, Git Bash)

Run natively on Windows, not in WSL2, so the browser can be shown. You need
[uv](https://docs.astral.sh/uv/) and Google Chrome.

```bash
cp .env.example .env
uv sync --group dev
```

Check the setup with real, visible Chrome. This runs every browser test in
installed Chrome:

```bash
TEST_BROWSER_CHANNEL=chrome TEST_HEADED=1 uv run pytest -v
```

While it runs:
- Keep the screen on and unlocked. A locked screen stops Chrome drawing, and
  the run then waits forever. Playing a video in a small window keeps the
  display awake.
- Don't click in the test windows: a click moves keyboard focus.

Plain `uv run pytest` uses Playwright's bundled Chromium, headless; it needs
`uv run playwright install chromium` once. What the first Windows runs
found: [docs/solutions/windows-chrome-results.md](docs/solutions/windows-chrome-results.md).

### Connect to Claude Code

Add to `.mcp.json` in your project, with the absolute path to this repository:

```json
{
  "mcpServers": {
    "a11y-assist": {
      "command": "uv",
      "args": ["--directory", "C:/path/to/a11y-assist", "run", "a11y-assist"]
    }
  }
}
```

### Examples

Ask in plain words, and your agent makes calls like these.
`tests/test_readme.py` checks each one against the tool's schema and runs
example 4 end to end.

**1. Every implemented test on a page.** "Check https://www.section508.gov/
for keyboard, focus and form problems."

<!-- example -->
```json
{"tool": "a11y_run_tt_tests", "arguments": {"url": "https://www.section508.gov/"}}
```

`tests` defaults to every implemented test. Without `other_pages`, 9.A-9.C
and 19.A come back NEEDS REVIEW, because they need pages to compare.

**2. With other pages of the site.** "Test the home page, and compare it
with two other pages for navigation and multiple ways."

<!-- example -->
```json
{"tool": "a11y_run_tt_tests", "arguments": {"url": "https://www.section508.gov/", "other_pages": ["https://www.section508.gov/manage/", "https://www.section508.gov/test/"]}}
```

Each other page must be on the same host, and each adds up to 20 s to the
call. 19.A may suggest more pages (a site map, the home page). Your agent
can add them in another call.

**3. Chosen tests only.** "Is there a keyboard trap on
https://www.section508.gov/, and is focus visible?"

<!-- example -->
```json
{"tool": "a11y_run_tt_tests", "arguments": {"url": "https://www.section508.gov/", "tests": ["4.C", "4.D"]}}
```

**4. A local page, then an open question.** With `DEV_MODE=true`, `file://`
pages can be tested (use your clone's absolute path). This fixture has three
links that pass focus among themselves forever:

<!-- example -->
```json
{"tool": "a11y_run_tt_tests", "arguments": {"url": "file:///ABSOLUTE/PATH/a11y-assist/tests/fixtures/4c/f06-script-loop.html", "tests": ["4.C"]}}
```

4.C comes back NEEDS REVIEW with one open question (`4.C-i1-J1`): does the
page tell users a key that gets out of the loop? The agent reads the page
text it was given and answers:

<!-- example -->
```json
{"tool": "a11y_answer_questions", "arguments": {"run_id": "<run_id from the result>", "answers": [{"question_id": "4.C-i1-J1", "decided_by": "model", "rationale": "The page text names no key that moves focus out of the three looping links.", "j1": {"documented": "no"}}]}}
```

4.C is now FAIL: "Keyboard focus gets trapped on this page. Keyboard focus
kept cycling between "Loop link 1" (link), "Loop link 2" (link), "Loop link
3" (link), and none of the usual keys … move it out." A person can override
the answer with `"decided_by": "human"`. If they name a key, the server
presses it in the recorded page to check it.

### Example output from a real run

These are files from the answering run on NASA's accounts receivable form
page (2026-11-04). It ran all 17 tests, and the agent answered its 10
questions:

- **[report.json](evals/judging/round1-answers/results/arm-a/runs/20261104T200634Z-d02d2f/report.json):**
  the findings, each with its spec rows, instances and plain-language
  summary; the questions, the agent's answers and its reasons; and every
  version (spec, ANDI, browser, model).
- **[pre-scrt.json](evals/judging/round1-answers/results/arm-a/runs/20261104T200634Z-d02d2f/pre-scrt.json):**
  the same results as SCRT's 61 TT 5.1.3 rows, in SCRT's words, with
  screenshots inline and rows left for a person flagged. It is a top-level
  object, so SCRT does not load it as a formal report.
- **[steps.jsonl](evals/judging/round1-answers/results/arm-a/runs/20261104T200634Z-d02d2f/steps.jsonl):**
  the run's step log, with each phase's time.

Each run writes these to `runs/<timestamp>-<id>/` (git-ignored), with the
page recordings and evidence under `evidence/`. Evidence holds page content:
treat it as untrusted. Save the report in your repository before it expires
(24 hours).

## Configuration

Settings come from the environment or `.env` in this repository's root
(`.env.example`, `src/a11y_assist/config.py`):
- `ALLOWED_DOMAINS`: the allowlist, `.gov` and `.mil` by default. It is
  enforced on every navigation and redirect.
- `RUN_LIMIT_S` and `OTHER_PAGE_S`: the time limits above.
- `BROWSER_CHANNEL` and `HEADLESS`: which Chrome, and whether it is shown.
- `DEV_MODE`: allows `file://` pages and `DEV_ALLOWED_ADDRESSES`.
- `UPSTREAM_PROXY`: for a container that re-signs TLS.
- Evals only: `FROZEN_PAGES_DIR` and `FROZEN_PAGES_MODE`.

## Safety

- **Allowlist:** every top-level navigation and redirect hop is checked
  against it.
- **Address checks:** Chrome connects only through a local proxy that
  refuses private, loopback and cloud-metadata addresses and pins the
  address it checked, so DNS rebinding cannot get past it.
- **ANDI:** served from the vendored copy, never from ssa.gov.
- **Page content is untrusted data:** it never chooses a URL, a tool or an
  outcome. The one approved exception is 19.A's single live site search.
- **Versions:** all are pinned, and every report records them.

Details: [docs/hackathon/evaluation.md](docs/hackathon/evaluation.md).

## Known limits

- **Recording:** a recorded page freezes network responses, not
  client-side randomness or time.
- **Content-Security-Policy:** a page's CSP that forbids inline scripts
  blocks ANDI. No CSP bypass is enabled.
- **Linked help pages:** pages linked from the tested page are not
  followed for 4.C's question.
- **Browsers tested:** CI runs Playwright's Chromium, headless. Headed
  Google Chrome on Windows is checked by hand.
- **Planned:** see [docs/ROADMAP.md](docs/ROADMAP.md).

## License

MIT (see [LICENSE](LICENSE)), from the GSA-TTS
[mcp-hackathon-template](https://github.com/GSA-TTS/mcp-hackathon-template).

Third-party software (see [NOTICE](NOTICE)):

- **ANDI 29.2.2**, Copyright Social Security Administration, Apache License 2.0
  ([third_party/andi/NOTICE](third_party/andi/NOTICE),
  [LICENSE.md](third_party/andi/LICENSE.md)). Unmodified copy; use does not
  imply SSA endorsement.
- **jQuery 3.7.1**, Copyright OpenJS Foundation and other contributors, MIT
  ([third_party/jquery/LICENSE.txt](third_party/jquery/LICENSE.txt)).
