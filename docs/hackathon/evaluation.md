# Evaluation Document

GSA MCP and AI Agent Hackathon

> **Draft.** Work is in progress, so no results are recorded yet.
> **[FILL: …]** marks a final figure to copy from the submission run.
> **[PENDING]** marks work not done yet; don't present it as done.
> Structure follows GSA's sample evaluation document (sections 1–5).

| | |
| --- | --- |
| Server under test | A11y Assist (working name), [github.com/abbybowman/a11y-assist](https://github.com/abbybowman/a11y-assist) |
| What it does | Runs parts of the DHS Trusted Tester (TT) 5.1.3 Section 508 web test process in a real Chrome browser and reports agent-assisted findings by TT test ID. **Not a certified Trusted Tester result.** |
| Tests implemented | **[FILL: TT test IDs and spec versions at the submission commit]** |
| Evaluation framework | pytest with a scoring module (`tests/scoring.py`) that compares outcomes to DHS's published Trusted Tester verdicts and W3C's expected results. Exact match; no LLM judge |
| Agent model | Claude Opus 5.5 in Claude Code, as the calling agent that answers open questions. **[FILL: scripted or live answers in the scored run]** (see 2.3) |
| Browser | **[FILL: Playwright and browser versions, OS, headed or headless for the scored run]**. Target: headed Google Chrome on Windows |
| Dataset | W3C ACT test cases with DHS Trusted Tester verdicts, per TT test: **[FILL: case counts per test]** |
| Run | **[FILL: commit, date, command, tests passed, duration]** |

## 1. Overview and objectives

### Why this matters

The goal is to put some of the Trusted Tester process into more hands, so certified testers spend their time on edge cases and low-confidence calls instead of the clear-cut ones.

- **Agencies lack trained testers.** In GSA's FY 2024 governmentwide assessment, 60% of reporting entities (146) said they had no or only some development and testing staff trained in Section 508 web testing, and only 22% required specific training or certification for web testers ([GSA, FY 2024](https://www.section508.gov/manage/section-508-assessment/2024/findings/program-staff/)).
- **Testing is the weakest link.** In FY 2025, testing and remediation was the weakest implementation area, averaging 2.00 (Low) on a 5-point scale. Agencies cited limited staffing and gaps in specialized expertise as barriers to testing at scale ([GSA, FY 2025](https://www.section508.gov/manage/section-508-assessment/2025/findings/accessibility-implementation-outcomes/testing-and-remediation/)). Governmentwide conformance averaged 1.96 of 5 ([GSA, FY 2025](https://www.section508.gov/manage/section-508-assessment/2025/findings/accessibility-conformance-outcomes/)).
- **Certification is a real investment.** Training and exams are free and self-paced. A federal team at the Office of Natural Resources Revenue estimated about 70 hours of training, about 6 hours for the practice exam, and a final exam with three attempts in three days ([ONRR](https://blog.onrr.gov/trusted-tester/)). In April 2024, DHS lowered the passing score for the practice and final exams from 90% to 85% "to make the certification more attainable" ([Section508.gov](https://www.section508.gov/blog/trusted-tester-update-april2024/)). Individual testers report 40 to 80 hours and failed first attempts ([Krull](https://manningkrull.com/digital-philosophy/my-508-trusted-tester-exam-experience/), [MacDonald](https://dustinkmacdonald.com/dhs-trusted-tester-section-508-training/)). These are anecdotes, not data.
- **No public count of certified testers.** DHS doesn't publish a count or a directory of certified Trusted Testers. **[PENDING: ask DHS; see "Data to request from DHS" below.]**
- **Scanners miss most barriers, and all of these.** In the UK Government Digital Service's 2017 audit of a page with 143 deliberate barriers, the best tool found 37% to 41%, and 29% of the barriers were missed by all 10 tools ([GDS](https://accessibility.blog.gov.uk/2017/02/24/what-we-found-when-we-tested-tools-on-the-worlds-least-accessible-webpage/)). Deque counts by volume of issues in real audits and reports 57% ([Deque](https://accessibility.deque.com/hubfs/Accessibility-Coverage-Report.pdf)), so the figure depends on how coverage is counted. For the keyboard tests in scope, there's no ambiguity: axe-core 4.14 has no rules for WCAG 2.1.2, 2.4.7, 3.2.1 or 2.4.3, nor for 3.2.2 On Input (5.D), and pa11y's default engine reports them only as warnings or manual-check notices, which it hides by default (verified by installing both). On one federal homepage, Lighthouse flagged 3 failed conditions where Trusted Tester found 12 ([ONRR](https://blog.onrr.gov/trusted-tester/)). Across all 60 active TT test conditions, our coverage map (axe-core 4.14.0 and pa11y 10.0.0's default HTML_CodeSniffer 2.5.1 errors, rated per test condition) finds 3 reliably covered, 21 partly covered and 36 not covered at all ([research/2026-10-31-tt-coverage-map.md](../research/2026-10-31-tt-coverage-map.md)); the ratings are estimates still to be checked with certified Trusted Testers.

### Data to request from DHS

- How many people hold active Trusted Tester for Web certification, and how they spread across agencies.
- The average number of practice and final exam attempts per certified tester.
- Average hours or calendar days from enrollment to certification.
- Pass rates, and the share of enrollees who never finish.
- Item-level answer distributions from the practice and final exams, per TT test (section 2.3).

### What we're testing

This evaluation asks one question first: **does the tool reach the same outcome a certified Trusted Tester reaches on the same page?** A passing server:

- misses no real failures: a false PASS (marking a failing page PASS) hides a barrier from disabled users, so it is the worst error;
- rarely flags passing pages: a false FAIL wastes a developer's time;
- says "needs review" instead of guessing, without escalating everything;
- gives the same outcome on repeated runs of the same frozen page.

A second question comes after the rules are proven: **does an agent with no accessibility training use the tools correctly**, relay outcomes faithfully, and never describe results as certified? **[PENDING: agent-level evaluation, section 2.3.]**

| Metric | Target | Why |
| --- | --- | --- |
| False-PASS rate | ≤ 5% per TT test | The worst error |
| False-FAIL rate | ≤ 15% | Wastes time, erodes trust |
| Needs-review rate | Reported | Escalating everything would fake accuracy |
| Consistency over 5 runs | Reported | Shows where judgment wobbles |

Targets were set before the first scored run.

## 2. Testing methodology

### 2.1 Framework and reproducibility

- **The TT PDF is the authority.** Each TT test has a rules spec in `docs/rules/`, citing the PDF's page and step for every rule. Code may decide an outcome only through a spec row, and each report records the spec version.
- **Frozen pages.** ACT test pages are stored byte for byte with SHA-256 hashes and served locally; tests never fetch from the network. Live pages are recorded once (HAR) and every pass replays the recording.
- **Pinned versions.** Dependencies are locked; ANDI 29.2.2 and jQuery are bundled with hashes. Every report records ANDI, Playwright, browser, OS, Python, spec and judging-model versions.
- **One command** runs the scored set and prints the agreement table: `uv run pytest tests/test_act_cases.py`.

### 2.2 Golden dataset

We used ground truth published by the people who run the Trusted Tester program instead of writing our own answers.

- **Pages:** W3C's ACT test cases for three keyboard-trap rules (a1b64e, ebe86a and their composite 80af7b). These rules are still *proposed*, not yet approved by W3C; scores are reported with that label.
- **Verdicts:** DHS's Section 508 Coordinators published Trusted Tester 5.1 results on these cases ([act-tt](https://github.com/Section508Coordinators/act-tt)). Joined on each test case's hash, not its URL, because some cases were filed under another rule's folder.
- **Size:** **[FILL: per TT test, distinct cases and DHS's split of PASS / FAIL / DNA]**.
- **Coverage gaps in the answer key:** per the repo's specs, no ACT rule covers 3.2.1 (4.E), 2.4.3 (4.F) or 3.2.2 (5.D), so those tests have no published DHS verdicts to compare against. Their accuracy must come from held-out pages. 5.D is also checked against the five Section 508 Baseline Alignment TC10.C cases, and 5.F (3.3.1 Error identification) against the seven TC10.D cases, 5.C (form names) against the nine TC10.A cases and 5.A (visible label) against the four TC10.E cases (expected results published by the federal baseline, not by DHS). No ACT rule or Baseline case covers 3.3.3 (5.G); DHS publishes no ACT verdicts for the form-name rules. 5.B (2.4.6, label descriptive; spec 1.0.0) is checked against W3C ACT rule cc0f0a, on which DHS published verdicts for 14 cases (ours agree with all 14), and 5.H (3.3.4, error prevention; spec 1.0.0) against the six TC10.G cases; four of those are one-page forms, which the TT makes DOES NOT APPLY and Baseline tests. The multi-page tests (9.A, 9.B and 9.C, spec 1.0.0) have no DHS verdicts either: DHS scored none of W3C's five proposed bypass-blocks rules, and no ACT rule or Baseline Alignment case exists for 3.2.3 (9.B) or 3.2.4 (9.C). 9.A is checked against 28 W3C ACT cases with W3C's expected results (ours differ on three: a heading or landmark alone is not a keyboard method, per the federal baseline, and a page whose only repeated content follows the main content does not apply); 9.B and 9.C rely on custom multi-page fixtures. No ACT rule, DHS verdict or Baseline Alignment case exists for 2.4.5 (19.A, spec 1.0.0); it relies on a custom site with a site map and a site search. **[FILL: confirm against W3C's ACT rules list at submission.]**
- **These are a development set, not a test set.** The 4.C spec was written and revised with these cases in view, and they have been public for years. Agreement on them shows the rules do what we intended; it is not independent evidence of accuracy. They are always reported separately from held-out results.
- **Not counted toward accuracy:** **[FILL: number]** custom fixture pages in `tests/fixtures/` cover cases ACT doesn't (iframes, shadow DOM, modal dialogs, cookie banners, injected instructions). Their expected outcomes are ours, so they test code behavior, not agreement with a certified tester.
- **[PENDING] Holdout:** real .gov pages, chosen without running the tool (so the set isn't limited to failures it already catches) and labeled blind by a certified tester in DHS's SCRT before any run; a second certified tester on a subset if available. Split by site, not page: pages on one site share templates and bugs, so a site used for tuning never appears in the held-out round. **Commit and reveal** (`evals/judging.py`): the tester commits the page list with the SHA-256 of each SCRT answer file only when a round starts, so development never sees the pages first; the tool's results are locked by hash and committed before any answer file is added; scoring refuses an answer file, result, page list or comparison code that changed after the lock. Scored test by test against the tester's file: agreement, false PASS, missed fail (Does Not Apply where the tester found a failure), false FAIL and NEEDS REVIEW, with tests the tool does not perform reported apart. Round 1's pages were tested live, not frozen, on the day of the scan; later rounds record each page the day it is tested. Each round is recorded in `evals/README.md`; the figures in this document come from one round chosen at submission.
- **[PENDING] Seeded faults:** real keyboard traps are rare, so copies of frozen real pages get one injected fault each, confirmed by hand and reported as planted. Seeds come from sources independent of our code (W3C failure technique F10, reported library bugs, traps written by someone who hasn't seen the code) and are reported by source. A missed seed must end NEEDS REVIEW; a PASS on any seed is a false PASS.
- **[PENDING] Practice-exam pages:** the DHS training site's practice pages are behind a login, so they are less likely to have been seen during development or in model training. Their quizzes give one answer per page per test. Use them as a second held-out set only if DHS's terms allow and the hackathon organizers confirm they count as publicly available government data.
- **[PENDING] Real-page replication** (section 2.5).

### 2.3 Evaluators

Outcomes are categories (PASS, FAIL, DNA, NEEDS_REVIEW), so we score by **exact match** against DHS's verdict and, separately, against W3C's expected result for each rule. No LLM judge is involved, so judge bias and variance don't enter the score. NEEDS_REVIEW matches neither answer key and is reported as its own rate.

**[PENDING] Instance-level scoring.** A page can be marked FAIL for the wrong reason. Each FAIL is also scored on whether the tool found the same failing elements the tester did, reported as instance recall (failures found) and precision (flags that were real).

**Human baseline from published research.** How often experts agree is already studied, at larger scale than we could run:

- W3C defines a WCAG 2.0 success criterion as "reliably human testable" when at least 80% of knowledgeable evaluators would agree on the result.
- In a study of 22 experts and 27 non-experts rating all 61 WCAG 2.0 criteria on four pages, about half the criteria fell below that 80% bar; experts produced 20% false positives and missed 32% of true problems ([Brajnik, Yesilada and Harper 2010](https://dl.acm.org/doi/10.1145/1878803.1878813)). Non-experts did worse.
- A follow-up found average expert agreement of about 70–75%, with an error rate around 29% ([Brajnik, Yesilada and Harper 2012](https://www.researchgate.net/publication/235339930_Is_accessibility_conformance_an_elusive_property_A_study_of_validity_and_reliability_of_WCAG_20)).
- Comparing methods, web developers using a screen reader found about half of known problems; multiple evaluators did best ([Mankoff, Fait and Tran 2005](https://kilthub.cmu.edu/articles/journal_contribution/Is_Your_Web_Page_Accessible_A_Comparitive_Study_of_Methods_for_Assessing_Web_Page_Accessibility_for_the_Blind/6470195)).
- W3C created the ACT Rules partly because tools and testers handle edge cases differently. Its ACT implementations list reports how consistent each tool or methodology is with the rules' expected results; Trusted Tester 5.1 is listed as consistent on 6 approved and 6 proposed rules ([W3C](https://www.w3.org/WAI/standards-guidelines/act/implementations/)). That measures methodologies against test cases, not people against each other on real pages.

**The gap:** these studies are of open-ended WCAG audits from 2005–2012. None measures agreement among certified Trusted Testers following TT 5.1.3, whose step-by-step procedure exists to raise agreement. No published DHS data on this was found.

**[PENDING] Ask DHS for exam-based agreement data.** Every candidate answers questions on the same pool of practice and final exam pages, per TT test. Item-level answer distributions would be the most authoritative Trusted Tester agreement baseline available, far larger than any study we could run.

**[PENDING] Small two-tester check** on our held-out pages, framed as a sanity check against the published figures, not as the baseline.

**[PENDING] Submit to W3C's ACT implementations list.** Publish an ACT implementation report for A11y Assist so W3C lists its consistency per rule, alongside Trusted Tester's own entry. That's third-party, public and comparable.

**[PENDING] Model dependence.** Every run reports how many outcomes the rules decided alone, how many needed an answer to an open question, and accuracy on that second group when Claude answers instead of a script.

Two automated checks run with every test:

- **Plain language:** a finding's summary may not contain spec codes or jargon.
- **No certification claims:** every report carries the disclaimer, and the report model can't be marked certified.

**What this does not measure yet.** When a rule needs a judgment (for example, "does the page document a key that escapes this section?"), the scored runs answer with scripted, known-correct answers. So these scores measure the rules and the evidence collection, not Claude's judgment. **[PENDING] Agent-level evaluation** (`docs/plans/2026-10-31-agent-eval.md`): a model with this server (Agent A) and the same model with Playwright MCP and web search instead (Agent B, the baseline), given the same task, the same frozen pages and the same prompt. Both are scored in code against a certified tester's blind SCRT files, with weights fixed before any run (correct +1, needs review 0, false FAIL or FAIL on the wrong element −1, false PASS −3; raw counts always shown). Tokens and wall time are logged for every step. Round 1: 9 pages from one site, one run per arm, a prompt naming the WCAG 2.0 criteria under test, Agent A scored per TT test and both arms per WCAG 2.0 criterion. Later rounds add plain-language tasks, repeats, a wording judge from another model family, and GPT 5.6 Sol and Gemini 4 Argon; questions, prompts, weights and labels are frozen before the final round. Agents run through NASA's Ask Sage API on NASA's network.

### 2.4 Test design rationale

The false-PASS asymmetry drives the design. When a rule can't decide, the outcome is NEEDS_REVIEW, never PASS. An agent's opinion leads to PASS only when a key press confirms it.

DHS verdicts make "agrees with a certified tester" measurable instead of a claim. Comparing against W3C's expected results as well shows where DHS's procedure and W3C's rule differ, so a mismatch can be traced to a ruling rather than a bug.

### 2.5 Evidence standard for skeptics

Experienced manual reviewers already know scanners miss most WCAG failures. Adrian Roselli's comparison of a manual review with four free tools on one real page is a widely cited example ([Roselli](https://adrianroselli.com/2023/01/comparing-manual-and-free-automated-wcag-reviews.html)). An agent-assisted tool should expect the same scrutiny and more, so we hold ourselves to these standards:

- **[PENDING] Replicate a manual-review comparison on real pages and publish everything.** Archive several live .gov pages (Wayback Machine plus our recording). Certified testers do Test 4 by hand. Run A11y Assist beside axe, WAVE, ARC Toolkit, Equal Access and pa11y. Publish a per-instance side-by-side table with the archived pages and every tool's raw output.
- **Keep development and test results apart** (section 2.2), and report each test set separately.
- **[PENDING] More than one viewport and state.** The keyboard walk currently runs at a fixed 1280 × 900 window. TT 5.1.3 doesn't set a window size for Test 4, but real focus failures often appear only at narrow widths or with menus open. Run at least desktop and a narrow width, with menus opened, and say "not tested at this width" for anything not run.
- **Scope before results.** Every report should open with which TT tests were performed and which were not. At submission the tool performs **[FILL: n]** of 61 active tests. **[PENDING: the report's first section lists the tests not performed.]**
- **No single coverage percentage.** Report what each TT test covers and how accurately, never one "percent automated" figure.
- **[PENDING] Severity.** TT outcomes are binary. Triage adds a user-impact rating (for example, low to critical) so a keyboard trap outranks a cosmetic issue.
- **Say what agreement means.** Agreeing with a Trusted Tester means agreeing with a code-inspection process for WCAG 2.0 A and AA. It does not mean a page is accessible, works with screen readers, or meets WCAG 2.1 or later.

## 3. Performance metrics

### 3.1 Results

**[FILL: commit, environment and date of the scored run.]** Report each TT test separately, and the development set separately from held-out pages (section 2.2).

| TT test | Answer key | Cases | Agreement | False PASS | False FAIL | Needs review |
| --- | --- | --- | --- | --- | --- | --- |
| [FILL] | DHS verdicts on ACT cases (development set) | [FILL] | [FILL] | [FILL] of [FILL] failures | [FILL] of [FILL] passes | [FILL] |
| [FILL] | Held-out real pages, blind-labeled | [FILL] | [FILL] | [FILL] | [FILL] | [FILL] |

- **Agreement with W3C's expected results:** **[FILL]**.
- **Model dependence:** **[FILL: outcomes decided by rules alone vs. needing an answer; accuracy when Claude answers]**.
- **Run time:** **[FILL: per-page time on real pages]**. Target: under 60 s for Test 4 on a typical page, hard limit 120 s per call (checks stop 10 s early so the report is written in time; anything cut short is NEEDS REVIEW). A page too large to walk within the limit is refused within seconds, before anything is tested, and the caller may rerun it with `no_time_limit` (4.C spec 1.6.0; a 600-link page is refused after about 5 s). Replays to a walk stop skip the quiet window on presses the walk saw change nothing, and are redone fully settled if focus ends elsewhere (4.C spec 1.7.0): a realistic agency home page went from 151 s to 97 s with every outcome unchanged. With 5.D (On input) included, both realistic pages finish every implemented test in 108–111 s; a page with more than 40 form fields is refused at the first load (5.D spec 1.0.0). With 5.F and 5.G (error identification and suggestion) added they went over the limit; checks now reuse each other's replays (4.A reads 4.D's arrow presses and 4.F's Enter presses when they cover what it needs, no outcome change), and 4.A treats the parts of a native date input as native (4.A spec 1.2.0), so all nine tests finish in 108.6 s and 92.4 s. With 5.A and 5.C (one fresh load: labels, images and ANDI's output, 1–2 s) all eleven finish in 110.2 s and 97.1 s. The multi-page tests 9.A–9.C (spec 1.0.0) need other pages of the same site; without them they are NEEDS REVIEW and cost nothing (all fourteen tests: 108.0 s and 94.6 s). With other pages the run limit grows by 20 s per page; with one other page the agency page finishes all fourteen in 110.1 s of 140 s (9.x about 3 s). 19.A (Multiple ways) shares that read and adds 0.0 s. 5.B and 5.H (completing Test 5) reuse the label pass and the error pass: 0.0 s and 0.1 s; all sixteen tests on the agency page take 109.1–110.4 s (at the soft deadline, nothing cut) and 97.6 s on the benefits form.
- **Consistency over 5 runs:** **[FILL]**.

**Sample-size caveat.** If the tool misses none of n true failures, the 95% upper bound on its miss rate is about 1 − 0.05^(1/n) (roughly 3/n). Showing ≤ 5% needs about 60 failing cases with no misses. **[FILL: n per test and the resulting bound.]** Unless n reaches about 60, describe results as "promising," not "validated."

### 3.2 Failure analysis

**[FILL: one row per disagreement in the scored run.]** For each, say whether it is a false PASS (the worst error), and whether it traces to a spec ruling, a bug, or a difference between DHS and W3C.

| Case | Tool | Reference | Why |
| --- | --- | --- | --- |
| [FILL] | [FILL] | [FILL] | [FILL] |

## 4. Security considerations

### Data classification

The server reads public web pages, by default only on `.gov` and `.mil`. It needs no credentials and tests no pages behind a login. Pages can still contain anything, including user-submitted text, so recorded pages, screenshots and logs are treated as untrusted. They are kept for at most 24 hours (configurable), then deleted; durable results belong in the user's own repository.

### Scope containment as a control

- **Allowlist on every hop.** The allowlist is checked on every top-level navigation and every redirect, not just the first URL.
- **One live request shaped by page content: 19.A's site search.** Only when the caller's pages show fewer than two ways to reach the page, the tool submits the site's own search form once: a GET form on the tested page's host (allowlist on every hop), the tested page's heading as the term, the results recorded as their own replay file. Other links found on pages are only suggested to the user, never visited.
- **Other pages chosen by the caller only.** The multi-page tests compare the tested page with up to five other pages the caller names (up to 50 when the caller turns the time limit off). Each must pass the allowlist and be on the tested page's host before and after redirects, or nothing is tested; one that cannot be recorded within its 20 s share leaves the multi-page tests NEEDS REVIEW while the other tests still run; page content never adds a page (links on the tested page are never followed). Each is recorded as its own replay file.
- **Refused pages produce no findings.** A blocked, unreachable or invalid page is a tool error with no findings, so no "result" exists for a page that was never tested.
- **Dev-only local files.** `file://` URLs work only in development mode.
- **Connection-time address checks.** The allowlist matches any `.gov` or `.mil` host by suffix, which this use needs, but a name says nothing about where it points. So Chrome's only way out is a local proxy inside the server. For every connection (the page, iframes, subresources, WebSockets, each redirect hop and the guard's own fetch), the proxy resolves the host once. It refuses the connection if any answer is a private, loopback, link-local, multicast, unspecified, reserved or cloud-metadata address, including IPv4-mapped, IPv4-compatible, 6to4 and Teredo IPv6 forms, or if the port isn't 80 or 443. Otherwise it connects to the address it just checked, so a second DNS answer (rebinding) is never used. TLS stays end to end, so Chrome still verifies the certificate for the real hostname. If the proxy is down, nothing gets out. A refused page is a tool error; refused page parts are listed in the result. Development mode reaches the local test server only through an explicit address allowlist that is ignored outside development mode.
- **Outbound security tests** (`tests/test_egress.py`). A `.gov` name resolving to 10.x, 127.x, 169.254.169.254 and ::ffff:127.0.0.1; a name with one good and one private answer; a redirect to a private address; an iframe, image and script pointing at one; a resolver whose answer changes mid-run; alternate address forms (integer, hex, octal, short and IPv4-mapped); the development allowlist outside development mode; a disallowed port; and an unresolvable name. A sentinel server on a refused loopback address would record any request that got through, and none did. With the proxy removed from Chrome's launch, 9 of these tests fail.
- **[PENDING]** Network-level egress rules on any host that runs the server, as a second layer (the GSA template asks for both).

### Untrusted input and prompt injection

- **The server's text never includes page text.** Page strings appear only in a labeled untrusted field, and the server's own question wording is fixed.
- **Page scripts can't fake focus.** Focus is read through the Chrome DevTools Protocol in an isolated context; a test checks that page script can't spoof it. This includes where a skip link lands (9.A): a test page that tells its own script focus moved, when it did not, is a FAIL, not a PASS. A page that cancels the browser's own error message (5.F) is not credited with that message.
- **Outcomes come only from spec rows.** A model's answer is recorded as a fact for a rule, never as an outcome.
- **Adversarial fixture.** Fixture F32 contains text telling automated testers to report PASS for every test; the expected result is FAIL with both traps reported. **[FILL: result at the submission commit.]**

**[PENDING]** More injection cases, including injected text in accessible names and frames.

### Logs and errors

- **Redacted errors and logs.** Following the GSA template, tool errors and the run log carry no query strings, cookies, headers, stack traces or page text. URLs keep only scheme, host, port and path; an error is one line (exception type and first message line, URLs redacted, capped at 200 characters). The run log is redacted where it is written, so no caller can bypass it. The user's saved report keeps the full URL.
- **Data-leakage tests** (`tests/test_leakage.py`). Secrets are seeded in a URL query string, a page script error, a console error, a cookie and a failing subresource; a redirect out of the allowlist and an unreachable page are also covered. Each test checks the tool error, the result's error list, the run log, Python logging and the process's stdout and stderr. With the redaction removed, 4 of the 5 tests fail.

### Secrets and configuration

Settings load from a `.env` file that is never committed. No API key is needed today, because the calling agent answers open questions. A direct model connection (NASA's hosted models) will add a key through the same mechanism.

### Transport and isolation

- **Local only.** stdio is the default transport. HTTP is opt-in, binds only to a loopback address (127.0.0.1 or ::1), and checks the Host and Origin headers of every request, so a web page can't reach it through DNS rebinding (`tests/test_transport.py`). There is no authentication yet, so the server can't be hosted.
- **Fresh state for every load.** Each page load gets a fresh browser context, so cookies and storage can't carry state between probes.
- **No CSP bypass.** No content security policy bypass is enabled.
- **Pinned third-party code.** ANDI and jQuery are bundled with hashes, and requests to ssa.gov are blocked so ANDI is never loaded live.

The template's entry point started an unauthenticated HTTP server on all interfaces whenever a `PORT` or `DATABRICKS_APP_PORT` environment variable was set. That branch is removed and those variables are ignored. **[PENDING]** Authentication, before any hosted demo.

### Misuse: findings mistaken for certification

Agencies accept Trusted Tester results only from certified people. Every tool response and report carries a "not a certified Trusted Tester result" disclaimer. The report model has `certified: False` as a fixed value. Contributor rules ban "certified," "compliant" and "Section 508 conformant" about a tested page.

## 5. Lessons learned and recommendations

### What worked

- **Borrow the ground truth.** DHS's published verdicts on W3C test pages gave us a certified-tester answer key on day one. Writing our own would have measured agreement with ourselves.
- **Exact match beats an LLM judge when outputs are categories.** It is cheaper and reproducible, with no judge bias to review.
- **Proportionate to the procedure.** Cutting spec steps that went beyond what the PDF asks a human to do cut test time sharply without reducing agreement with DHS. **[FILL: before and after figures, if still representative.]** The aim is consistency with a careful tester, not exceeding one.
- **Collect once, evaluate many.** One keyboard walk per page feeds every Test 4 check and 5.D, so each new test costs less to add than the last: 5.D reused the walk's stops, its replays and 4.A's observer; 5.F and 5.G share one error pass, 5.A and 5.C one label pass that reads ANDI's own output (what a Trusted Tester reads), and 4.A reuses 4.D's and 4.F's replays.
- **Write lessons down.** `docs/solutions/` records problems that took over an hour to understand. Examples: pages can fake focus, cookie banners leak state between probes, ANDI changes the page it inspects, and the TT PDF disagrees with itself in places.

### Limitations

- **[FILL: TT tests implemented; scored cases and true failures per test.]**
- **[FILL: whether judgment answers were scripted in the scored run.]**
- **[FILL: whether the scored run used the target environment (headed Chrome on Windows).]**
- The W3C rules used are still proposed, and the scored cases served as the development set.
- One viewport (1280 × 900) and the page's initial state only.
- Trusted Tester scope: WCAG 2.0 A and AA by code inspection and keyboard; no screen reader testing.
- No real-site holdout or repeat runs yet.

### Recommendations for hackathon participants

- **Look for an official answer key before writing your own.** Agencies often publish the verdicts you need.
- **Name your worst error and design around it.** For us that is a false PASS; when unsure, the tool says so.
- **Keep rules and model judgment apart.** Score the rules with known answers first, then score the model separately.
- **Report needs-review and refusal rates beside accuracy.** Escalating everything can fake a high score.
- **Record what you verified and what you assumed.** Human-review anything a model wrote, including this document.
