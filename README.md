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

"Real pages" means round 1 (9 www.nasa.gov pages, scored against a
certified Trusted Tester's blind SCRT files) and a run on the same pages
with the agent told to answer every question. No test gave a false PASS.
Details: [round 1](evals/agent/README.md#results);
[the answering run](evals/judging/round1-answers/README.md);
[the fixes underway](docs/plans/2026-11-04-post-round1-fixes.md).

| ID | TT test name | WCAG 2.0 | Spec | Results from real-page tests |
| --- | --- | --- | --- | --- |
| 2.A | 1.4.2-audio-control | 1.4.2 | [1.0.0](docs/rules/2a-audio-control.md) | ❓ Not yet tested in a judging round: checked on W3C ACT and custom pages only |
| 2.B | 2.2.2-blinking-moving-scrolling | 2.2.2 | [1.0.0](docs/rules/2b-blinking-moving-scrolling.md) | ❓ Not yet tested in a judging round: checked on W3C ACT and custom pages only |
| 2.C | 2.2.2-auto-updating | 2.2.2 | [1.0.0](docs/rules/2c-auto-updating.md) | ❓ Not yet tested in a judging round: checked on W3C ACT and custom pages only |
| 2.D | 4.1.2-change-notify-auto | 4.1.2 | [1.0.0](docs/rules/2d-change-notify-auto.md) | ❓ Not yet tested in a judging round: checked on custom pages only |
| 4.A | 2.1.1-keyboard-access | 2.1.1 | [1.2.1](docs/rules/4a-keyboard-access.md) | ⚠️ Mostly undecided: embedded frames and time limits. Agrees where decided |
| 4.B | 2.1.1-no-keystroke-timing | 2.1.1 | [1.2.0](docs/rules/4b-no-keystroke-timing.md) | 🟢 Sure and accurate |
| 4.C | 2.1.2-no-keyboard-trap | 2.1.2 | [1.8.0](docs/rules/4c-no-keyboard-trap.md) | 🟢 Sure and accurate |
| 4.D | 2.4.7-focus-visible | 2.4.7 | [1.1.1](docs/rules/4d-focus-visible.md) | ⚠️ Finds real failures, but some false FAILs on elements whose screenshots differ by 0 px (being fixed) |
| 4.E | 3.2.1-on-focus | 3.2.1 | [1.1.0](docs/rules/4e-on-focus.md) | 🟢 Sure and accurate |
| 4.F | 2.4.3-focus-order-meaning | 2.4.3 | [1.1.3](docs/rules/4f-focus-order-meaning.md) | ⚠️ Mostly undecided ("unsure" answers); two false FAILs from a card grid and a dropdown (being fixed) |
| 5.A | 3.3.2-label-provided | 3.3.2 | [1.1.0](docs/rules/5a-label-provided.md) | 🟢 Sure and accurate once the agent answers its question |
| 5.B | 2.4.6-label-descriptive | 2.4.6 | [1.1.0](docs/rules/5b-label-descriptive.md) | ⚠️ Passes where a placeholder-only field should make it Does Not Apply (being fixed) |
| 5.C | 1.3.1-programmatic-label | 1.3.1, 4.1.2 | [1.1.0](docs/rules/5c-programmatic-label.md) | ⚠️ About half decided; agrees where decided |
| 5.D | 3.2.2-on-input | 3.2.2 | [1.0.0](docs/rules/5d-on-input.md) | 🟢 Mostly sure and accurate. Missed a fail when 96 identical questions went unanswered (being fixed) |
| 5.F | 3.3.1-error-identification | 3.3.1 | [1.1.0](docs/rules/5f-error-identification.md) | ⚠️ Undecided on every page: a site search has no errors to check (being fixed) |
| 5.G | 3.3.3-error-suggestion | 3.3.3 | [1.1.0](docs/rules/5g-error-suggestion.md) | ⚠️ Undecided on every page, as 5.F (being fixed) |
| 5.H | 3.3.4-error-prevention | 3.3.4 | [1.1.0](docs/rules/5h-error-prevention.md) | 🟢 Sure and accurate once the agent answers its question |
| 9.A | 2.4.1-bypass-function | 2.4.1 | [1.0.0](docs/rules/9a-bypass.md) | 🟢 Sure and accurate: found the failure on 8 of 9 pages and left the ninth for a person |
| 9.B | 3.2.3-consistent-navigation | 3.2.3 | [1.0.0](docs/rules/9b-consistent-navigation.md) | 🟢 Sure and accurate |
| 9.C | 3.2.4-consistent-identification | 3.2.4 | [1.1.0](docs/rules/9c-consistent-identification.md) | 🟢 Sure and accurate once the agent answers its questions |
| 19.A | 2.4.5-multiple-ways | 2.4.5 | [1.1.0](docs/rules/19a-multiple-ways.md) | ⚠️ Undecided on every page: needs more pages of the site (being fixed) |

## Tools

| Tool | What it does | Main inputs |
| --- | --- | --- |
| `tobi_run_tt_tests` | Tests one page. It records the page once, runs the chosen TT tests on the recording, and returns findings, open questions for your agent, and links to the full report and pre-SCRT file. | `url` (`.gov` and `.mil` by default); `tests` (default: all implemented); `other_pages` (1-5 pages of the same site, for 9.A-9.C and 19.A); `no_time_limit` |
| `tobi_answer_questions` | Records answers to the open questions and decides again by the spec. A person's answer overrides the agent's. | `run_id`; `answers` (one per question) |
| `tobi_read_report` | Reads an SCRT or pre-SCRT file: what failed and what still needs a person. With `compare_to`, it lists every test whose result differs between two files (for example, before and after a fix). | `content`; `compare_to` |

**Also:**
- **Resources:** `run://{run_id}/...` (a run's files, kept 24 hours) and
  `tt://5.1.3/...` (the TT text).
- **Prompt:** `explain` (a test or a result in plain language).

## How long it takes

- **One call:** at most 120 s, plus 20 s for each other page, plus 45 s
  when something on the page keeps changing by itself (a ticker, a
  carousel: every key press waits longer there, and Test 2 tries its
  controls). On
  www.nasa.gov, calls with 3 other pages took 2-3 minutes. Tests not
  finished in time come back NEEDS REVIEW, with the reason.
- **Large pages:** a page too large to finish in time (more than 40 form
  fields, or too many stops to Tab through) is refused at once. Call
  again with `no_time_limit: true` and expect 15-20 minutes.
- **Answering:** under a second, unless the server has to press a key in
  the recorded page to check an answer.
- **Your client:**
  - Raise its MCP tool timeout. Claude Code's was 60 s in our tests: set
    `MCP_TOOL_TIMEOUT` (ms).
  - Claude Code also moves calls longer than 120 s to the background
    (`CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`).
- **Batches:** test a few pages at a time. Each call gets its own browser,
  and a second, headless one that watches the page for Test 2 (the
  concurrency figures below were measured before it was added).
  On a 4-CPU machine, 3 at once ran normally, and 12 at once timed out.

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
{"tool": "tobi_answer_questions", "arguments": {"run_id": "<run_id from the result>", "answers": [{"question_id": "4.C-i1-J1", "decided_by": "model", "rationale": "The page text names no key that moves focus out of the three looping links.", "j1": {"documented": "no"}}]}}
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
- `ALLOWED_DOMAINS`, `RUN_LIMIT_S` and `OTHER_PAGE_S`;
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
