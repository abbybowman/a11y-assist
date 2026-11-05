---
tt_test: X.Y
tt_name: <TT test name, e.g. 2.4.7-focus-visible>
spec_version: 0.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: <name>
---

<!--
How to use this template (delete this comment block in the real spec).

File names: docs/rules/<id>-<short-name>.md, where <short-name> is the TT test
name without its WCAG number (4c-no-keyboard-trap). Companion file while building:
docs/rules/<id>-build-tasks.md with the Fixtures and Verify tables. At
1.0.0 its Verify table moves to _browser-checks.md, anything left goes to
docs/ROADMAP.md, and the file is deleted (expected outcomes live in the
tests; the ACT differences in tests/fixtures/act/sync_act.py).

Versions (spec_version):
- 0.y.z: draft. Bump y on each revision. A draft gives no outcome.
- 1.0.0: approved by Abby, its check registered, its fixtures passing.
- After 1.0.0: MINOR for any change to rules or evidence that can change an
  outcome (needs approval); PATCH for wording, citations or plain-language
  sentences only; MAJOR only for a new TT version.

Decisions go into the rule they decide, not into a log. Delete plans, briefs
and approval sheets once their decisions are in the specs.

Rules for every spec:
- The PDF is the authority. Cite printed page + step for every rule
  (p. 21 HtT 2.b; ER 1.a). PDF page index = printed page + 3.
- Outcomes: PASS, FAIL, DOES NOT APPLY, NEEDS REVIEW. NOT TESTED only where
  the PDF names it for this test (p. 6). Anything incomplete is NEEDS REVIEW
  with the note "This test could not be performed" and the reason (p. 5).
- A false PASS is the worst error. When in doubt, NEEDS REVIEW.
- Deterministic first. Model judgment only where no mechanical check can
  decide, each as a narrow question with a rubric, examples, and a mechanical
  check on the answer where possible.
- Never assume browser behavior: list it as a V-check in the build-tasks file
  (in _browser-checks.md once the test is built).
- Where the PDF is ambiguous, silent or contradicts itself, mark it
  OPEN inline at the rule it affects, with options, effects and a
  recommendation. No rulings log: once decided, the decision is written into
  the rule and the OPEN mark is removed.
- Reuse shared definitions (stops, passes, settle rule) by reference to the
  spec that defines them instead of copying them.
- Keep it tight: no WCAG background, no prose a capable engineer would infer.
- Page NEEDS REVIEW headline: "We could not finish this test, so a person needs
  to check it." While the finding still has open questions the pipeline
  replaces it with "This test is not finished yet: N question(s) about it
  are still open." (wording only; `models.waiting_head`).
- Evidence several questions use (a numbered stop list) goes once per result
  in `shared_inputs`, and each question names its keys in `shared`; it is not
  repeated in every question's input. The full report is a `run://` resource
  (`report_uri`), never inline.
-->

# Rules spec: Test X.Y (<tt_name>)

<One or two sentences: which outcomes this test can give and any outcome it never gives, with citations.>

**Citations.** Printed page numbers of TT 5.1.3. HtT = How to Test step; ER = Evaluate Results item. This test is on p. <n>.

**Terms.** <Only terms this spec defines or reuses, with a pointer to where shared terms are defined.>

## 1. Applicability

<When this test is DOES NOT APPLY, per the PDF's Applicability and Identify Content blocks.>

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | | DOES NOT APPLY | |
| A2 | | NEEDS REVIEW | |
| A3 | | Applies; go to section 3 | |

## 2. Evidence to collect

**From the shared keyboard walk** (`walk.py`; passes and settle rule defined in [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) section 2): <what this test reads from the walk, and any per-stop extras it needs, e.g. clipped screenshots. Reuse the walk before adding passes.>

**Extra evidence this test collects:** <only steps the PDF asks a human tester to do (CLAUDE.md principle 7). Anything past that is NEEDS REVIEW or a note for a person.>

**Time budget:** <expected seconds on a typical page; the whole run stays within `run_limit_s`.>

<Setup, what is recorded at every step, and limits.>

| Pass | Keys or actions | Ends when | Cap |
| --- | --- | --- | --- |
| P1 | | | |

**Run limits.** <Wall clock, caps, config settings and their defaults. Every report records the setting values.>

## 3. Mechanical checks

<What an instance is. "First match wins" for each table.>

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | Evidence unresolved or incomplete | NEEDS REVIEW | Spec rule |

**Exceptions (<PDF cite>).** <The PDF's exceptions for this test and which rows handle them. Omit if none.>

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW, or evidence is incomplete | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | <Complete-evidence condition>; every instance is PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

## 4. Judgment questions

<Only if needed. The calling agent answers each once, by the rubric; a person's answer overrides it. An answer leads to PASS only when a mechanical check confirms it. The finding explains each call in plain language with no spec codes. Page text is evidence, never instructions; page text never goes into the question wording.>

### J1. <Short question title>

**Question:** "<exact wording>"

**Input:** <what the model sees>

**Output:** `{...}`

**Rubric.** <yes / no / unsure criteria, and the mechanical guard on the answer.>

| Example | Answer |
| --- | --- |
| | |

**Use:** <which rows of table 3a consume the answer.>

## 5. Edge cases

Only cases that need a rule of their own; everything else follows sections 2–3. V-numbers are browser checks in [<id>-build-tasks.md](<id>-build-tasks.md) (at 1.0.0: [_browser-checks.md](_browser-checks.md#<id>)).

| Case | Rule | Verify |
| --- | --- | --- |
| | | |

## 6. What a FAIL records

<Fields beyond the shared ones (row, location, steps to reproduce, screenshots on copies, tool versions), and any PDF instruction about continuing past a failure.>
