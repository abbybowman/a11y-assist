# a11y-assist

> **Not a certified Trusted Tester result.** This tool produces agent-assisted
> findings only. Its output is not a DHS Trusted Tester certified test result
> and must not be reported, cited or relied on as one. A certified Trusted
> Tester must perform any test that counts for Section 508 conformance.

An MCP server that runs parts of the DHS Trusted Tester (TT) 5.1.3 Section 508
web test process in a real, visible Chrome browser and reports findings by TT
test ID. The package name is provisional.

## Status

**Seventeen TT tests are implemented: 4.A–4.F (keyboard and focus), 5.A, 5.B, 5.C,
5.D, 5.F, 5.G and 5.H (forms; all of Test 5, whose 5.E is obsolete), and 9.A–9.C and
19.A (pages of the same site). The other TT
tests are not.** Outcome logic comes only from
the rules specs in [docs/rules/](docs/rules/), one file per TT test
(`<id>-<short-name>.md`), checked against the TT 5.1.3 PDF in
[docs/sources/](docs/sources/).

For contributors: start with `CLAUDE.md` (principles and layout), then
`docs/ROADMAP.md` (what is next) and `docs/solutions/` (lessons). To add a TT
test, follow the steps at the top of `src/a11y_assist/checks/base.py`.

What works today:

| Area | State |
| --- | --- |
| `a11y_run_tt_tests(url, tests=["4.C"], other_pages=[...])` | Runs the selected TT tests (any of the implemented ones) and returns a typed result: findings with plain-language summaries, open questions (with the page text once), evidence as `run://` resources, and the full report for the user to save. One shared keyboard walk (Tab, Shift+Tab) per page feeds every keyboard check; 4.C adds its exit probes. A record per key press (stop identity, role and name from Chrome's accessibility tree, frames, shadow roots, focus events); screenshots at traps. 9.A–9.C and 19.A also compare the page with up to 5 other pages of the same site that the caller names (up to 50 with `no_time_limit`) (`other_pages`; never taken from the page itself). Progress notifications while it runs; at most `RUN_LIMIT_S` (120 s) per call, plus `OTHER_PAGE_S` (20 s) for each other page |
| Tool errors | A URL outside the allowlist, a redirect out of it, a page that cannot load, or an unknown or expired run id is a tool error (isError) with no findings |
| TT 5.1.3 as data | The whole PDF as Markdown plus `tt.json` (all 63 conditions with requirements and WCAG links), checked word for word against the PDF. Served as `tt://5.1.3/index`, `tt://5.1.3/tests/{id}` and `tt://5.1.3/parts/{part}`; every finding links its test (`reference`) and Understanding pages. See `docs/sources/README.md` |
| `explain(about?, run_id?)` prompt | A command that explains Trusted Tester tests in plain language, before a run (what a test checks, what this tool does for it) or after (what was found, how to fix it). `about` takes a test ID, WCAG criterion, test name or words. Built on `explain.py`, which failure reports will reuse |
| `run://{run_id}/{path}` resources | `report.json`, `pre-scrt.json`, `evidence/*.json` and screenshots of a run, while it is kept (`RUN_TTL_HOURS`, default 24). Durable results belong in the user's repository |
| HAR record + replay | Page is recorded once (scrolled to load lazy content); every pass and probe runs against the replay. A page with cross-site iframes replays in full Chromium, never Playwright's headless shell (which runs those frames in-process, unlike users' Chrome); the report records each page's replay browser |
| Frozen pages (evals only) | `FROZEN_PAGES_DIR`: a server setting, never a tool input. In "replay" mode every page a run loads (the tested page, other pages, 19.A's search) comes from a folder of recordings, and a URL with none is a tool error, never fetched live. In "tested_frozen" mode (the agent eval) the tested page must be frozen, and other pages of its site load live as usual |
| Agent eval (`evals/agent/`) | Agent A (a model with this server) against Agent B (the same model with Playwright MCP) on the same frozen pages and WCAG 2.0 prompt, scored against a tester's SCRT files. **Built and tested on fixtures with a scripted model; not yet run on a real model or real pages.** Runbook: [evals/agent/README.md](evals/agent/README.md) |
| Navigation allowlist | `.gov` and `.mil` by default, enforced on every top-level navigation and redirect hop; `file://` only in dev mode |
| Connection address checks | Chrome's only way out is a local proxy (`egress.py`) that resolves each host once, refuses it if any answer is a private, loopback, link-local, multicast, reserved or cloud-metadata address (IPv4-mapped and other alternate forms included) or the port is not 80/443, and connects to the address it checked, so DNS rebinding cannot get past it. Covers the page, iframes, subresources, WebSockets and every redirect hop. A refused page is a tool error; refused page parts are listed in the result's `errors` Optional `UPSTREAM_PROXY` (off by default): for a host whose direct connections are re-signed by a gateway browsers do not trust (a cloud container), the checks run as usual and the connection is then tunneled by name through that proxy, which resolves the name again |
| ANDI 29.2.2 | Vendored, injected from local files, never loaded from ssa.gov. Used by 5.C (what screen readers announce for each form field) and 9.C (names across pages) |
| Findings for any active TT test | The seventeen implemented tests: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW per its spec, with the spec rows that produced it. Every other active TT 5.1.3 test: `NEEDS_REVIEW` with the note "This test could not be performed" (no spec yet). Never `NOT_TESTED`: the PDF allows it only where a test names it (p. 6) |
| `a11y_answer_questions(run_id, answers)` | Records one answer per question (the calling agent's, or a person's override, which wins); presses documented keys in the recorded page and re-applies the spec. Suggested input values go to a person to try. Answers are facts, never outcomes |
| `a11y_read_report(content, compare_to?)` | Reads one page's report file: an SCRT JSON file saved from DHS's [SCRT](https://github.com/Section508Coordinators/SCRT), or this server's pre-SCRT file. Returns what failed, what still needs a person and who tested it. With `compare_to` (another report of the same page, such as the one from before a fix) it lists every test whose result changed, without saying which file is right. Takes the file's text or a `run://` link (and a local path in `DEV_MODE`). Scoring the tool against an answer key is evaluation work: `evals/scoring.py` |
| pre-SCRT files | Every run also writes `pre-scrt.json` (`pre_scrt_uri`): SCRT's fields and its 61 TT 5.1.3 rows, with the spec's outcome in SCRT's words, rows the tool left for a person flagged, screenshots inline, and where each row came from. A top-level object, so SCRT cannot load it as a formal report. Agent-assisted, not a Trusted Tester evaluation |
| ApiJudge | Stub (`NotImplementedError`) |

Planned: Trusted Tester review of a pre-SCRT file in a local page and export
to SCRT once every row is checked, merging a partial file into a run, a
site roll-up, a plain-language report for developers, fix advice for a read
report (its own tool), and a `compare_to` option on `a11y_run_tt_tests` that
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
- Tests run in CI against Playwright's Chromium (headless): the headless
  shell, and full Chromium for pages with cross-site iframes. Headed Google
  Chrome on Windows must be checked locally (see below).

## TT tests in scope

The implemented tests, with their names and WCAG 2.0 criteria from the TT
5.1.3 catalog (`tt.json`; `tests/test_readme.py` checks this table against
`checks.REGISTRY`). Every other active TT test is NEEDS REVIEW, "This test
could not be performed".

| ID | TT test name | WCAG SC |
| --- | --- | --- |
| 4.A | 2.1.1-keyboard-access | 2.1.1 |
| 4.B | 2.1.1-no-keystroke-timing | 2.1.1 |
| 4.C | 2.1.2-no-keyboard-trap | 2.1.2 |
| 4.D | 2.4.7-focus-visible | 2.4.7 |
| 4.E | 3.2.1-on-focus | 3.2.1 |
| 4.F | 2.4.3-focus-order-meaning | 2.4.3 |
| 5.A | 3.3.2-label-provided | 3.3.2 |
| 5.B | 2.4.6-label-descriptive | 2.4.6 |
| 5.C | 1.3.1-programmatic-label | 1.3.1, 4.1.2 |
| 5.D | 3.2.2-on-input | 3.2.2 |
| 5.F | 3.3.1-error-identification | 3.3.1 |
| 5.G | 3.3.3-error-suggestion | 3.3.3 |
| 5.H | 3.3.4-error-prevention | 3.3.4 |
| 9.A | 2.4.1-bypass-function | 2.4.1 |
| 9.B | 3.2.3-consistent-navigation | 3.2.3 |
| 9.C | 3.2.4-consistent-identification | 3.2.4 |
| 19.A | 2.4.5-multiple-ways | 2.4.5 |

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

Keep the screen on and unlocked while it runs, and don't click in the test
windows: a locked screen appears to stop Chrome drawing and the run waits
forever, and a click moves keyboard focus. Playing a video in a small window
keeps the display awake. What the first Windows runs found:
[docs/solutions/windows-chrome-results.md](docs/solutions/windows-chrome-results.md).

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

## Examples

Three ways to call `a11y_run_tt_tests`, the main tool. Your agent makes these
calls when you ask in plain words; they are shown as tool name and arguments.
`tests/test_readme.py` checks every example below against the tool's schema,
and runs example 3 end to end.

**1. Every implemented test on a page.** Ask: "Check
https://www.section508.gov/ for keyboard and focus problems."

<!-- example -->
```json
{"tool": "a11y_run_tt_tests", "arguments": {"url": "https://www.section508.gov/"}}
```

`tests` defaults to every implemented test. Without `other_pages`, 9.A–9.C and 19.A
come back NEEDS REVIEW (they need pages to compare). The result has one
finding per test (PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW, with a
plain-language summary), any open questions, and `report_uri`, the full
report to save in your repository.

**2. Chosen tests only.** Ask: "Is there a keyboard trap on
https://www.section508.gov/, and is focus visible?"

<!-- example -->
```json
{"tool": "a11y_run_tt_tests", "arguments": {"url": "https://www.section508.gov/", "tests": ["4.C", "4.D"]}}
```

Any active TT 5.1.3 test ID is accepted; one with no rules yet comes back
NEEDS REVIEW with the note "This test could not be performed".

**3. A local page, then an open question.** With `DEV_MODE=true`, `file://`
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
the answer with `"decided_by": "human"`; if they name a key, the server
presses it in the recorded page to check it.

## Output

Each run writes `runs/<timestamp>-<id>/`:

```
evidence/page.har.zip       recorded page
evidence/pages/*.har.zip    other pages and 19.A's site search, each recorded
evidence/walk.json          the shared Tab / Shift+Tab walk
evidence/4c.json …          each check's evidence (one file per TT test)
evidence/shots/*.png        screenshots where a check needs them
steps.jsonl                 step log (URLs without query strings, no page text)
report.json                 findings, open questions, answers, versions, disclaimer
pre-scrt.json               the results in SCRT's shape, for a Trusted Tester to review
```

`runs/` is git-ignored. Evidence holds page content; treat it as untrusted.

## Configuration

See `.env.example` and `src/a11y_assist/config.py`. Settings come from the
environment or from `.env` in this repository's root, whatever directory the
client starts the server in. Main settings:
`ALLOWED_DOMAINS`, `DEV_MODE`, `EGRESS_PORTS`, `UPSTREAM_PROXY` (see the table above), `DEV_ALLOWED_ADDRESSES` (dev
mode only: addresses the connection check lets through, e.g.
`["127.0.0.1/32"]` for a local test server), `BROWSER_CHANNEL`, `HEADLESS`,
`JUDGE_BACKEND`, `JUDGING_MODEL`, and for evals only `FROZEN_PAGES_DIR` and
`FROZEN_PAGES_MODE` (`replay`, `tested_frozen` or `record_missing`). Rules spec versions are
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
