# a11y-assist

> **Not a certified Trusted Tester result.** This tool produces agent-assisted
> findings only. Its output is not a DHS Trusted Tester certified test result
> and must not be reported, cited or relied on as one. A certified Trusted
> Tester must perform any test that counts for Section 508 conformance.

An MCP server that runs parts of the DHS Trusted Tester (TT) 5.1.3 Section 508
web test process in a real, visible Chrome browser and reports findings by TT
test ID. The package name is provisional.

## Status

**4.C is implemented; the other tests are not.** Outcome logic comes only from
the rules specs in [docs/rules/](docs/rules/), one file per TT test
(`<id>-<short-name>.md`), checked against the TT 5.1.3 PDF in
[docs/sources/](docs/sources/).

What works today:

| Area | State |
| --- | --- |
| `run_tt_tests(url, tests=["4.C"])` | Runs the selected TT tests (4.A–4.F) and returns a typed result: findings with plain-language summaries, open questions (with the page text once), evidence as `run://` resources, and the full report for the user to save. One shared keyboard walk (Tab, Shift+Tab) per page feeds every keyboard check; 4.C adds its exit probes. A record per key press (stop identity, role and name from Chrome's accessibility tree, frames, shadow roots, focus events); screenshots at traps. Progress notifications while it runs; at most `RUN_LIMIT_S` (120 s) per call |
| Tool errors | A URL outside the allowlist, a redirect out of it, a page that cannot load, or an unknown or expired run id is a tool error (isError) with no findings |
| TT 5.1.3 as data | The whole PDF as Markdown plus `tt.json` (all 63 conditions with requirements and WCAG links), checked word for word against the PDF. Served as `tt://5.1.3/index`, `tt://5.1.3/tests/{id}` and `tt://5.1.3/parts/{part}`; every finding links its test (`reference`) and Understanding pages. See `docs/sources/README.md` |
| `explain(about?, run_id?)` prompt | A command that explains Trusted Tester tests in plain language, before a run (what a test checks, what this tool does for it) or after (what was found, how to fix it). `about` takes a test ID, WCAG criterion, test name or words. Built on `explain.py`, which failure reports will reuse |
| `run://{run_id}/{path}` resources | `report.json`, `evidence/*.json` and screenshots of a run, while it is kept (`RUN_TTL_HOURS`, default 24). Durable results belong in the user's repository |
| HAR record + replay | Page is recorded once (scrolled to load lazy content); every pass and probe runs against the replay |
| Navigation allowlist | `.gov` and `.mil` by default, enforced on every top-level navigation and redirect hop; `file://` only in dev mode |
| ANDI 29.2.2 | Vendored, injectable from local files, never loaded from ssa.gov. Not used by any test yet |
| Findings for any active TT test | 4.C, 4.D, 4.E and 4.F (all of TT Test 4's keyboard and focus tests except 4.A and 4.B): PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW per its spec, with the spec rows that produced it. Every other active TT 5.1.3 test: `NEEDS_REVIEW` with the note "This test could not be performed" (no spec yet). Never `NOT_TESTED`: the PDF allows it only where a test names it (p. 6) |
| `answer_questions(run_id, answers)` | Records one answer per question (the calling agent's, or a person's override, which wins); presses documented keys in the recorded page and re-applies the spec. Suggested input values go to a person to try. Answers are facts, never outcomes |
| ApiJudge | Stub (`NotImplementedError`) |

Planned: `read_report` (read an agency's existing ACR or SCRT report and
recommend fixes and re-tests) and a `compare_to` option on `run_tt_tests` that
takes a saved report (verify a fix). Guidance goes in resources or a prompt.
Tools are broad and outcome-based, not one per test step.

Known limits:

- 4.C: help pages linked from the page are not followed for J1 (only text on
  the page, including text revealed by Enter in a trap). Content behind
  collapsed controls (menus, accordions) is not opened; the finding says how
  many. A run stops at `RUN_LIMIT_S` (default 120 s); tests not finished are
  NEEDS_REVIEW with the reason.
- HAR replay freezes network responses, not client-side randomness or time.
- A page Content-Security-Policy that forbids inline scripts will block ANDI
  injection. No CSP bypass is enabled.
- Tests run in CI against Playwright's Chromium (headless). Headed Google
  Chrome on Windows must be checked locally (see below).

## TT tests in scope

TT 5.1.3 Test 4 has six tests, 4.A to 4.F. Names are checked against the TT
5.1.3 PDF, pp. 19–23.

| ID | TT test name | WCAG SC |
| --- | --- | --- |
| 4.A | 2.1.1-keyboard-access | 2.1.1 |
| 4.B | 2.1.1-no-keystroke-timing | 2.1.1 |
| 4.C | 2.1.2-no-keyboard-trap | 2.1.2 |
| 4.D | 2.4.7-focus-visible | 2.4.7 |
| 4.E | 3.2.1-on-focus | 3.2.1 |
| 4.F | 2.4.3-focus-order-meaning | 2.4.3 |

## Setup (Windows, Git Bash)

Run natively on Windows, not in WSL2, so the browser can be shown. Requires
[uv](https://docs.astral.sh/uv/) and Google Chrome.

```bash
cp .env.example .env
uv sync --group dev
```

Check the setup on your machine with real, visible Chrome. This runs every
browser test (allowlist and redirects, HAR replay, ANDI injection, focus
walks) in installed Chrome:

```bash
TEST_BROWSER_CHANNEL=chrome TEST_HEADED=1 uv run pytest -v
```

Plain `uv run pytest` uses Playwright's bundled Chromium, headless. That needs
a one-time `uv run playwright install chromium`, which downloads into your
user profile.

## Connect to Claude Code

Add to `.mcp.json` in your project (use the absolute path to this repo):

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

Then ask, for example: "Run TT test 4.C on https://www.section508.gov/".

## Output

Each run writes `runs/<timestamp>-<id>/`:

```
evidence/page.har.zip       recorded page
evidence/forward/NNN.png    screenshot after each Tab
evidence/backward/NNN.png   screenshot after each Shift+Tab
evidence/keyboard.json      all focus stops
steps.jsonl                 step log
report.json                 findings, open questions, answers, versions, disclaimer
```

`runs/` is git-ignored. Evidence holds page content; treat it as untrusted.

## Configuration

See `.env.example` and `src/a11y_assist/config.py`. Main settings:
`ALLOWED_DOMAINS`, `DEV_MODE`, `BROWSER_CHANNEL`, `HEADLESS`,
`JUDGE_BACKEND`, `JUDGING_MODEL`. Rules spec versions are
read from each spec's front matter (`spec_version`) and recorded in every report.

## Contributing

Read [CLAUDE.md](CLAUDE.md) first. It lists the project's principles: never
claim certification, outcome logic only from the rules spec, NEEDS_REVIEW over
a false PASS, pinned and recorded versions, page content as untrusted data, and
verify with tests.

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
