# Section 508 TOBI — Tester-Oriented Browser Inspector

TOBI (`tobi508` in code) is an MCP server that helps people test web pages
with the DHS Trusted Tester 5.1.3 process for Section 508. The name follows
the tradition of ANDI, SSA's Accessible Name & Description Inspector, which
TOBI runs inside the browser. TOBI is independent of DHS and SSA.

> **Not a certified Trusted Tester result.** This tool produces agent-assisted
> findings only. Its output is not a DHS Trusted Tester certified test result
> and must not be reported, cited or relied on as one. A certified Trusted
> Tester must perform any test that counts for Section 508 conformance.

**Why it exists.** Automated accessibility scanners read a page's code.
They miss failures you only find by using the page: a keyboard trap, focus
you can't see, a field whose only label disappears when you type, no way
to skip the header.

TOBI finds those failures for site owners and Trusted Testers. It
runs the hands-on parts of the DHS Trusted Tester 5.1.3 process in a real
Chrome browser, does the repetitive tabbing and comparing, and asks your AI
agent the judgment questions. Clear failures surface early, and certified
testers can spend their time on the cases that need a person.

**What you get:** PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW for each TT
test, with plain-language explanations, evidence, and a pre-SCRT file a
Trusted Tester can review in DHS's SCRT.
- **Outcomes** come only from the rules specs in [docs/rules/](docs/rules/),
  one per TT test, checked against the TT 5.1.3 PDF.
- **When the tool can't decide,** it says NEEDS REVIEW. It never guesses
  PASS.

## TT tests in scope

The table lists each implemented test's rules spec and what our tests on
real pages showed. Every other active TT 5.1.3 test comes back NEEDS
REVIEW, "This test could not be performed".

"Real pages" means round 1: 9 www.nasa.gov pages, scored against a certified Trusted Tester's blind SCRT files ([results](evals/agent/README.md#results); [answering run](evals/judging/round1-answers/README.md)). No test gave a false PASS. "Fixed, not yet retested" means the problem round 1 found is fixed and checked on test pages, not yet on real pages ([fixes](docs/plans/2026-11-04-post-round1-fixes.md)).

| ID | TT test name | WCAG 2.0 | Spec | Results from real-page tests |
| --- | --- | --- | --- | --- |
| 2.A | 1.4.2-audio-control | 1.4.2 | [1.0.0](docs/rules/2a-audio-control.md) | ❓ Not yet tested on real pages |
| 2.B | 2.2.2-blinking-moving-scrolling | 2.2.2 | [1.0.0](docs/rules/2b-blinking-moving-scrolling.md) | ❓ Not yet tested on real pages |
| 2.C | 2.2.2-auto-updating | 2.2.2 | [1.0.0](docs/rules/2c-auto-updating.md) | ❓ Not yet tested on real pages |
| 2.D | 4.1.2-change-notify-auto | 4.1.2 | [1.1.0](docs/rules/2d-change-notify-auto.md) | ❓ Not yet tested on real pages |
| 4.A | 2.1.1-keyboard-access | 2.1.1 | [1.2.1](docs/rules/4a-keyboard-access.md) | ⚠️ Mostly undecided (embedded frames, time limit); agrees where decided |
| 4.B | 2.1.1-no-keystroke-timing | 2.1.1 | [1.2.0](docs/rules/4b-no-keystroke-timing.md) | 🟢 Sure and accurate |
| 4.C | 2.1.2-no-keyboard-trap | 2.1.2 | [1.9.0](docs/rules/4c-no-keyboard-trap.md) | 🟢 Sure and accurate |
| 4.D | 2.4.7-focus-visible | 2.4.7 | [1.2.0](docs/rules/4d-focus-visible.md) | ⚠️ Some false FAILs; fixed, not yet retested |
| 4.E | 3.2.1-on-focus | 3.2.1 | [1.1.0](docs/rules/4e-on-focus.md) | 🟢 Sure and accurate |
| 4.F | 2.4.3-focus-order-meaning | 2.4.3 | [1.2.0](docs/rules/4f-focus-order-meaning.md) | ⚠️ Mostly undecided; two false FAILs fixed, not yet retested |
| 5.A | 3.3.2-label-provided | 3.3.2 | [1.2.0](docs/rules/5a-label-provided.md) | 🟢 Sure and accurate once answered; one wrong label fixed, not yet retested |
| 5.B | 2.4.6-label-descriptive | 2.4.6 | [1.2.0](docs/rules/5b-label-descriptive.md) | ⚠️ One wrong PASS; fixed, not yet retested |
| 5.C | 1.3.1-programmatic-label | 1.3.1, 4.1.2 | [1.3.0](docs/rules/5c-programmatic-label.md) | ⚠️ About half decided, agrees where decided; one missed FAIL fixed, not yet retested |
| 5.D | 3.2.2-on-input | 3.2.2 | [1.1.0](docs/rules/5d-on-input.md) | 🟢 Mostly sure and accurate; one missed FAIL fixed, not yet retested |
| 5.F | 3.3.1-error-identification | 3.3.1 | [1.3.1](docs/rules/5f-error-identification.md) | ⚠️ Undecided on every page (site search); fixed, not yet retested |
| 5.G | 3.3.3-error-suggestion | 3.3.3 | [1.2.1](docs/rules/5g-error-suggestion.md) | ⚠️ Undecided on every page (site search); fixed, not yet retested |
| 5.H | 3.3.4-error-prevention | 3.3.4 | [1.1.0](docs/rules/5h-error-prevention.md) | 🟢 Sure and accurate once answered |
| 9.A | 2.4.1-bypass-function | 2.4.1 | [1.0.0](docs/rules/9a-bypass.md) | 🟢 Sure and accurate |
| 9.B | 3.2.3-consistent-navigation | 3.2.3 | [1.0.0](docs/rules/9b-consistent-navigation.md) | 🟢 Sure and accurate |
| 9.C | 3.2.4-consistent-identification | 3.2.4 | [1.1.1](docs/rules/9c-consistent-identification.md) | 🟢 Sure and accurate once answered |
| 19.A | 2.4.5-multiple-ways | 2.4.5 | [1.1.1](docs/rules/19a-multiple-ways.md) | ⚠️ Undecided on every page (needs more pages of the site); fixed, not yet retested |

## Tools

| Tool | What it does | Main inputs |
| --- | --- | --- |
| `tobi_run_tt_tests` | Tests one page. It records the page once, runs the chosen TT tests on the recording, and returns findings, open questions for your agent, and links to the full report and pre-SCRT file. | `url` (`.gov` and `.mil` by default); `tests` (default: all implemented); `other_pages` (1-5 pages of the same site, for 9.A-9.C and 19.A); `no_time_limit` |
| `tobi_answer_questions` | Records answers to the open questions and decides again by the spec. A person's answer overrides the agent's. | `run_id`; `answers` (one per question) |
| `tobi_run_status` | Waits for a run that was still going when its call returned, and gives its result. Without `job_id`: what is left across the session's runs (open questions, follow-up calls, runs still going); with `finish=true` it also makes the follow-up calls the server may make itself. | `job_id` (optional); `finish` |
| `tobi_explain` | Explains tests in plain language: what a test checks, or, with a `run_id`, what that run found and why (full summaries, the reasoning, the places on the page, what can still change a result, and the W3C links for fixing it). Results carry one line per finding; this holds the detail. | `about` (test IDs, a WCAG criterion or words); `run_id` |
| `tobi_read_report` | Reads an SCRT or pre-SCRT file: what failed and what still needs a person. With `compare_to`, it lists every test whose result differs between two files (for example, before and after a fix). | `content`; `compare_to` |

**Also:**
- **Resources:** `run://{run_id}/...` (a run's files, kept 24 hours) and
  `tt://5.1.3/...` (the TT text).
- **Prompt:** `explain` (a test or a result in plain language; the same
  material as `tobi_explain`, as a command for the user).

## How long it takes

- **One run:** by default as long as the page needs, up to 30 min
  (`MAX_RUN_S`); a large page can take several minutes, and each
  still-running result says what the run is doing and for how long. With
  `no_time_limit=false` a run is held to 10 min (`RUN_LIMIT_S`, 600 s),
  plus 20 s for each other page, plus 45 s when something on the page
  keeps changing by itself (a ticker, a carousel), and a page too large
  for that is refused. On www.nasa.gov, runs with 3 other pages took 2-3
  minutes. Tests not finished in time come back NEEDS REVIEW, with the
  reason.
- **One call:** at most 45 s (`CALL_WAIT_S`), under common MCP client
  timeouts. A run not done by then goes on in the server: the result says
  `"status": "running"` with a `job_id`, and `tobi_run_status` waits for it
  again until `"status": "done"`. So you no longer need to raise your
  client's tool timeout (Claude Code's is 60 s, `MCP_TOOL_TIMEOUT`), and
  Claude Code's move of calls longer than 120 s to the background
  (`CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`) no longer applies.
- **Large pages:** a page with too many stops to Tab through is refused at
  once; one with more than 40 form fields is tested without 5.D, and 5.D's
  finding gives the call that runs it. Call again with `no_time_limit:
  true` and expect 15-20 minutes of `tobi_run_status` calls.
- **Answering:** under a second, unless the server has to press a key in
  the recorded page to check an answer.
- **Batches:** the server tests 2 pages at a time (`MAX_CONCURRENT_RUNS`);
  more wait in a queue, and a run's time limit starts only when it leaves
  the queue. Each run gets its own browser, and a second, headless one
  that watches the page for Test 2. On a 4-CPU machine, 3 at once ran
  normally and 12 at once timed out (measured before the second browser).

## Use it

**Setup (Windows, Git Bash).** Run natively on Windows, not in WSL2, so
the browser can be shown. You need [uv](https://docs.astral.sh/uv/) and
Google Chrome.

```bash
cp .env.example .env
uv sync --group dev
TEST_BROWSER_CHANNEL=chrome TEST_HEADED=1 uv run pytest -v   # checks it in real Chrome
```

While it runs, keep the screen unlocked and don't click in the test
windows ([what the first Windows runs found](docs/solutions/windows-chrome-results.md)).

**Connect to Claude Code.** Add to `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "tobi508": {
      "command": "uv",
      "args": ["--directory", "C:/path/to/your/clone", "run", "tobi508"]
    }
  }
}
```

**Examples.** Ask in plain words, and your agent makes calls like these.
`tests/test_readme.py` checks each one against the tool's schema and runs
the last pair end to end.

"Check https://www.section508.gov/ for keyboard, focus and form problems":

<!-- example -->
```json
{"tool": "tobi_run_tt_tests", "arguments": {"url": "https://www.section508.gov/"}}
```

"Also compare it with two other pages of the site" (for 9.A-9.C and 19.A):

<!-- example -->
```json
{"tool": "tobi_run_tt_tests", "arguments": {"url": "https://www.section508.gov/", "other_pages": ["https://www.section508.gov/manage/", "https://www.section508.gov/test/"]}}
```

"Is there a keyboard trap, and is focus visible?":

<!-- example -->
```json
{"tool": "tobi_run_tt_tests", "arguments": {"url": "https://www.section508.gov/", "tests": ["4.C", "4.D"]}}
```

A local page and its open question. With `DEV_MODE=true`, this fixture's
three links pass focus among themselves forever:

<!-- example -->
```json
{"tool": "tobi_run_tt_tests", "arguments": {"url": "file:///ABSOLUTE/PATH/TO/CLONE/tests/fixtures/4c/f06-script-loop.html", "tests": ["4.C"]}}
```

4.C comes back NEEDS REVIEW and asks whether the page names a key that
gets out. The agent answers from the page text:

<!-- example -->
```json
{"tool": "tobi_answer_questions", "arguments": {"run_id": "<run_id from the result>", "answers": [{"question_id": "4.C-i1-J1", "decided_by": "model", "rationale": "The page text names no key that moves focus out of the three looping links.", "seen": "three links in a row and no instructions", "j1": {"documented": "no"}}]}}
```

4.C is now FAIL: "Keyboard focus gets trapped on this page…".

**Example output** from a real run (NASA's accounts receivable form, all 17
tests, 10 questions answered):
- [report.json](evals/judging/round1-answers/results/arm-a/runs/20261104T200634Z-d02d2f/report.json):
  findings, questions and answers, and every version used;
- [pre-scrt.json](evals/judging/round1-answers/results/arm-a/runs/20261104T200634Z-d02d2f/pre-scrt.json):
  SCRT's 61 rows, screenshots inline, rows for a person flagged.

Save the report in your repository: a run's files expire after 24 hours.

## Configuration and safety

**Settings** come from the environment or `.env` (`.env.example`):
- `ALLOWED_DOMAINS`, `NO_TIME_LIMIT_DEFAULT` (default true), `MAX_RUN_S`,
  `RUN_LIMIT_S` and `OTHER_PAGE_S`;
- `CALL_WAIT_S` and `MAX_CONCURRENT_RUNS`;
- `PAGE_CACHE_S` (default 1800): how long an other page's recording, and
  its reads, are reused by later calls of the same server session;
- `BROWSER_CHANNEL` and `HEADLESS`;
- `DEV_MODE` (allows `file://` pages);
- `UPSTREAM_PROXY`, for containers that re-sign TLS.

**Safety:**
- Every navigation and redirect is checked against the allowlist.
- Chrome connects through a local proxy that refuses private and
  cloud-metadata addresses.
- ANDI is served from a vendored copy.
- Page content is treated as data: it never chooses a URL, a tool or an
  outcome.
- Every report records all versions.

Details: [docs/hackathon/evaluation.md](docs/hackathon/evaluation.md).

**Known limits:**
- A recording freezes network responses, not randomness or time.
- A Content-Security-Policy that blocks inline scripts blocks ANDI.
- CI runs headless Chromium; headed Chrome on Windows is checked by hand.

## Contribute

- **Testers:** certified Trusted Testers can run their own judging round
  and contribute it: [docs/how-to/run-a-judging-round.md](docs/how-to/run-a-judging-round.md).
- **Developers:** read [CLAUDE.md](CLAUDE.md), then [docs/ROADMAP.md](docs/ROADMAP.md).

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
