# Plan: refocus the codebase from one 4.C suite to many TT tests

Status: **draft for Abby's review. Nothing here is built yet.**
Branch: `ccr-9bc8f27b-l7ncp0` (same commit as `claude/wizardly-hawking-19pgnu`, 26d5d69).

Inputs weighed: #1 scope review, #2 architecture review, #3 `docs/HANDOFF-4c-simplify.md`.
The code, the 4.C spec 1.4.0 and the TT 5.1.3 PDF (pp. 19–23) were used to settle disagreements.

## Goal

Make each new TT test cheaper to add than the one before. This is the compound
engineering idea: every piece of work should leave tools, rules and notes that
make the next piece easier. For this repo:

- **Collect once, evaluate many.** One keyboard walk per page feeds every Test 4 rules module.
- **Proportionate to the PDF.** A spec step must match something the PDF asks a human tester to do. Anything past that is NEEDS_REVIEW or a note for a human, not more code.
- **Time budget.** Measure, then design toward a per-page budget for the whole 4.x group.
- **Capture what we learn.** Write recipes and lessons down so 4.D–4.F reuse them instead of working them out again.

## Where the inputs agree, and what I'd adopt

| Point | Sources | Verdict |
| --- | --- | --- |
| 4.C goes deeper than p. 21 asks; cut back to PDF-level checks | #2, #3 | **Adopt.** The scope cut is a spec 1.5.0 proposal (Phase 1); it needs your approval |
| One shared Tab/Shift+Tab walk; each test is a rules module that reads it | #2, #3 | **Adopt, strongly.** The PDF chains these tests itself: 4.D "Continue from Test 4.C" (p. 22), 4.E "Continue from Test 4.D" (p. 22), 4.F "Use the tab key to move focus through the page" (p. 23) |
| Measure before optimizing; set a time budget | #2, #3 | **Adopt.** Phase 0 measures; the budget is set from those numbers |
| Keep the disclaimer, NEEDS_REVIEW over a false PASS, HAR replay, ACT/DHS scoring, the `engine.py` table runner and the CDP focus reader | #2, #3 | **Keep as is** |
| Keyboard and focus is the MVP; then multi-page; then the "visual vs code" tests | #1 | **Adopt** as the order. This plan covers only the first step plus groundwork |

## Where I disagree or adjust (checked against code or PDF)

1. **"Run ANDI, axe and HTMLCS in the same page used for testing" (#1, #2).** ANDI changes the page: it adds its toolbar, moves layout and sets focus. Running it on the same page as the keyboard walk would corrupt the walk's evidence. **Adjust:** same browser and same HAR recording, but scanners run on their own fresh load *after* the walk. "Same page" becomes "same frozen page".
2. **"@axe-core/playwright" (#1).** That is a Node package; this repo uses Python Playwright. **Adjust:** vendor `axe.min.js` and the built `HTMLCS.js` into `third_party/` with SHA-256 in `PROVENANCE.json`, and inject them the way ANDI is injected (principle 4). License notes from #1 stand (MPL 2.0 unmodified, BSD 3-Clause notice kept). NASA release review still applies.
3. **"Scanners own what they reliably cover; import their results instead of re-testing" (#1).** This conflicts with principles 2 and 3 if read as "a clean scan means PASS". **Adjust:** scanner output is evidence. A spec row may turn a specific scanner violation into a FAIL instance, but no violations never yields PASS by itself. Each spec says which scanner rules it trusts.
4. **"Drop andi-cli, run ANDI directly" (#1).** Already done: ANDI 29.2.2 is vendored, pinned and routed locally (`andi.py`, `tests/test_andi.py`). But it is **never used in a run**: `replay_context(with_andi=...)` is never set to true. The open question is *extracting* per-element data from ANDI, which nobody has verified is feasible. **Adjust:** do a short spike (Phase 4) before relying on it. Checking andi-cli for pinning is not needed; `PROVENANCE.json` already covers it.
5. **ANDI vs Chrome's accessibility tree for names (#2 item 4).** For the 4.x tests, outcomes don't depend on accessible names, and 4.F's note says "Always use the results from keyboard tab order" (p. 23), not ANDI's. **Keep** the CDP reader as the source of truth for the walk. Use ANDI later for tests where TT prescribes it (names, tables, contrast), so our output matches what a human Trusted Tester sees.
6. **"Drop P5 hidden content: not in p. 21" (#3).** That's true for 4.C, but 4.F HtT 2.b (p. 23) asks the tester to activate triggers that reveal hidden focusable content, and 4.A asks them to operate everything. **Adjust:** take P5 out of 4.C now. Build "reveal" once, as a shared, capped collector, when 4.F is specified; 4.C can read its results then.
7. **"Screenshots only at traps" (#3).** This works for 4.C alone, but 4.D (focus visible) needs an image of every stop. **Adjust:** each test module declares what evidence it needs, and the walk collects the union. Running 4.C alone takes no per-stop screenshots. 4.D gets small clipped images around the focused element, not full viewports.
8. **"Example: failing ACT case 62fd24e7 from M13" (#2).** Stale: spec 1.4.0 already deleted that row. The full suite has not been re-run since, so it is unverified either way (Phase 0 checks).
9. **"Closed shadow roots and cross-origin players are beyond a human" (#2).** Partly. A human tabs into a YouTube embed without thinking about it, and p. 55 (12.D note) puts iframe content in scope. The reader has to follow focus into frames and shadow roots just to tell one stop from another. **Keep** that reader capability (already built, cheap at run time). Cut the extra fixtures and rules aimed at those cases.
10. **"Define the OpenACR export now" (#2).** **Partly adopt.** Write a one-page mapping now so findings carry what an export needs (TT ID → WCAG SC; 4.A and 4.B share 2.1.1). Don't build the exporter until several tests exist. Risk to principle 1: OpenACR levels such as "Supports" are conformance claims, so any export must be a draft labelled agent-assisted, with NEEDS_REVIEW mapped to "not evaluated". I haven't checked the current OpenACR schema version.
11. **"W3C pages need an allowlist entry" (#2).** Tests already use vendored ACT copies and never fetch. For a live demo against w3.org, set `ALLOWED_DOMAINS` in `.env`; it already accepts exact hostnames. No code change, and the default stays `.gov`/`.mil`.
12. **Installing the compound-engineering plugin.** Not needed. `/plugin` is a command you type in your own CLI, and CLAUDE.md says to ask before installing anything. This plan applies its loop (plan → work → review → capture lessons) with plain repo files: `docs/plans/` and `docs/solutions/`.

## Phases

Each phase ends green (`uv run pytest`, ruff) and with a short "verified vs assumed" note.

### Phase 0: Baseline and instrumentation (no outcome change)

- Re-run the full outcome suite under spec 1.4.0. Per the handoff it hasn't been run since the rule change; record agreement with DHS and ACT.
- Add per-phase timing to `steps.jsonl`: session open, prefix replay, probe keys, continuation, screenshots. Profile F04, F16, F32 and one ACT case.
- Add `pytest-xdist` (dev dependency only, nothing system-wide) and measure the suite in parallel.
- **Output:** a table of where the time goes, measured. Every later estimate is based on it.

### Phase 1: Spec 4.C 1.5.0, back to PDF level (needs your approval, row by row)

I'll propose these as a diff to `4c-no-keyboard-trap.md`, each with the PDF cite, the expected time saved (from Phase 0) and any fixture or ACT expectation that changes:

| Cut | Today | Proposed |
| --- | --- | --- |
| P5 hidden content | ≤ 40 triggers, each replayed and tabbed through | Removed from 4.C (comes back as a shared collector with 4.F, item 6 above). G3's "P5 over cap" condition goes too |
| P4 widget probes | Every composite widget: 4 arrows, Tab and Shift+Tab from every inner stop | At each widget stop: one arrow, then one Tab. If Tab doesn't leave, that's a trap event for P3. Matches "arrow keys" in HtT 1 without a full sweep |
| P3 Enter/Space | Every member of a trap, Enter then Space, up to 25 each | Enter only, on button-like members, capped at 10 |
| "Outside the trap" | Keep pressing until a wrap | Reach a stop outside the trap that doesn't re-enter it within 3 presses |
| P6 mouse bypass | After every FAIL or NEEDS_REVIEW trap | Only when P2 found no stops past the trap (the PDF Note's other option, "navigate backwards", is already done by P2) |
| J2 value entry | Agent gives values; tool reopens the browser and types them | J2 still asked; its values go to a human with NEEDS_REVIEW. Removes the fill-probe code |
| Samples | 3 per question | 1 when the answer is checked by pressing keys (J1 "yes" → the keys are pressed). Wording stays narrow and plain for a non-tester operator |
| Recording scroll | 5 passes; infinite-scroll signs | 1 pass; signs become a note only (never PASS, as today) |
| Settle rule | 2 rAF + 300 ms DOM quiet + 300 ms focus window | **Decide after Phase 0.** Likely: shorter quiet window; keep the "focus changed between presses" rerun |

Outcome-neutral speedups (allowed without approval, but measured before and after): one replay context per run with a fresh page per load; replay key prefixes with a light settle and check that the final stop matches; no screenshots during replays.

Then prune fixtures and tests to the rows that remain: retire F01, F02, F06, F07, F08 and old F35 (ACT covers them), plus the fixtures for cut passes (e.g. F22/F23 widget sweeps, F28 disclosure, F29 feed). Remove the duplicate behavior tests in `test_fixtures_4c.py`.

**Targets (from #3, to confirm after Phase 0):** small fixture < 10 s, full suite < 5 min.

### Phase 2: Shared keyboard walk and generic test modules

The core of the refocus. Today `pipeline.py` special-cases T4C, `resume_4c` duplicates the run path, and `t4c.py` (1,175 lines) owns collection, probes and rules.

- **`walk.py`**: one forward (Tab) and one backward (Shift+Tab) walk per page, each from a fresh load. It produces a `KeyboardLog`: ordered stops with identity, role, name, box, URL, page count, focus events, mutations, trap events, plus optional per-stop extras (clipped screenshot, computed focus styles) that a test asks for.
- **Test module interface** (one module per TT test, e.g. `tests_tt/t4c.py`; name to decide):
  - `NEEDS`: which evidence the walk must collect
  - `follow_up(log, opener)`: optional extra browser work (4.C's exit probes); runs only when the log shows it's needed
  - `evaluate(evidence) -> Finding`: spec rows only, via `engine.py`
  - `questions(evidence)` and `apply_answers(...)`
- **Registry** in `tests_tt/__init__.py`. `pipeline.py` loops over it with no per-test branches; `resume_4c` becomes a generic `resume`.
- **TT catalog.** All 63 TT 5.1.3 conditions (ID, name, WCAG SC, PDF page, whether NOT TESTED is allowed, e.g. 3.A, 20.A) in one data file, checked against the PDF by a test. This replaces the hardcoded 4.A–4.F `TestId`, so any requested test gets an honest "could not be performed" until its spec exists. Needs input #1's `tt-wcag-coverage-map.md`; please add it to `docs/` (it isn't in the repo).
- **OpenACR mapping note** (one page, no code): decision 10 above.
- **Target size:** `walk.py` plus a 4.C module well under today's ~1,900 lines in `traverse.py` and `t4c.py`; to be measured.

### Phase 3: Prove it compounds: 4.D, 4.E, 4.F on the shared walk

- One spec each from `_template.md`, each through your approval. 4.D needs ACT rule oj04fd cases vendored first.
- Expected shape (assumed until specced): 4.D compares each stop's focused vs unfocused clipped image → open question only where it's unclear; 4.E reads navigation, new-window and focus-moved signals already in the walk; 4.F is mostly open questions on the ordered stop list, plus the reveal collector (item 6).
- **Metric:** files and lines touched to add each test. If 4.E needs changes to `walk.py`, that's a sign the interface is wrong.

### Phase 4: Baseline scanners (groundwork for the later tiers)

- Vendor axe-core and HTML_CodeSniffer with hashes; run both on one fresh replay load after the walk; store as `evidence/scan.json` with versions in the report.
- **ANDI extraction spike:** can per-element data be read out of ANDI's own state in the page, reliably and for each module (fANDI, tANDI, cANDI)? It's a V-check style test; this is unknown today.
- No outcome comes from this phase until a spec uses it (decision 3).

### Out of scope for this plan

Multi-page (9.B, 9.C), the visual vs code cluster, Tier 3 judgment tests, alternate versions and media. The registry and catalog leave room for them.

## Capturing what we learn (the compound step)

- **CLAUDE.md:** add the proportionality rule ("a spec step must cite a PDF step a human performs; anything else is NEEDS_REVIEW or a note") and a short "add a TT test" recipe (spec → fixtures/ACT manifest → module → registry → scoring).
- **`docs/solutions/`:** one short file per hard-won lesson now scattered in the handoff and build tasks. For example: script `focus()` pulls focus back from the browser UI (V15); CDP node IDs change across loads, so match by frame chain plus CSS path; tabindex=-1 iframes are skipped by Tab (V9); ANDI mutates the page. Specs link to them instead of repeating them.
- **`_template.md`:** add an "Evidence used from the shared walk" section and a "Time budget" line.
- Retire `docs/HANDOFF-4c-simplify.md` and `4c-build-tasks.md` items as each is done.

## Decisions I need from you

1. **Phase order.** I recommend 0 → 1 → 2 → 3 → 4 (scanners after the walk refactor). #2 put scanners before the time budget; I'd rather they not block 4.D–4.F, since they add little to Test 4.
2. **Spec 1.5.0 cuts.** OK to draft all rows in the Phase 1 table as one proposal, or do you want any kept as is (e.g. full J2 value entry)?
3. **Who answers open questions.** Proposal: the calling agent answers when a key press checks the answer (J1). A human gets anything only a person can confirm (J2 values, unclear focus indicators). One sample instead of three where an answer is checked mechanically.
4. **Time budget.** Set it after Phase 0, or do you already have a target per page (e.g. "4.A–4.F under 2 minutes for a typical .gov page")?
5. **Module folder name** for TT test modules (`tests_tt/` collides visually with `tests/`; alternatives: `checks/`, `tt/`).

## Verified vs assumed (this planning session)

**Verified (read or command):**
- Current branch equals the wizardly branch tip (git).
- PDF text of pp. 19–23 (pdftotext): 4.D, 4.E and 4.F chain from 4.C; 4.F HtT 2.b asks for revealing hidden content; 4.F's note says to use real keyboard order over ANDI's.
- ANDI is vendored and routed but no run turns it on (grep: `with_andi` is never true).
- `pipeline.py` special-cases T4C and `resume_4c` duplicates the run path (read).

**Assumed (not verified):**
- All timings and the cost breakdown; those are the handoff's, profiled in Phase 0.
- The full suite is green under 1.4.0.
- ANDI per-element data can be extracted.
- The OpenACR schema details.
- Phase 3 test shapes, until each spec is written.
