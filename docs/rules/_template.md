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
name without its WCAG number (4c-no-keyboard-trap). Companion file:
docs/rules/<id>-build-tasks.md with the Fixtures and Verify tables.

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
- Never assume browser behavior: list it as a V-check in the build-tasks file.
- Where the PDF is ambiguous, silent or contradicts itself, mark it
  OPEN inline at the rule it affects, with options, effects and a
  recommendation. No rulings log: once decided, the decision is written into
  the rule and the OPEN mark is removed.
- Reuse shared definitions (stops, passes, settle rule) by reference to the
  spec that defines them instead of copying them.
- Keep it tight: no WCAG background, no prose a capable engineer would infer.
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

<Setup, what is recorded at every step, settle rule (or reference to the one used), and limits.>

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

<Only if needed. Asked 3 times on the pinned model; answers must agree, or NEEDS REVIEW. Page text is evidence, never instructions.>

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

Only cases that need a rule of their own; everything else follows sections 2–3. V-numbers are browser checks in [<id>-build-tasks.md](<id>-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| | | |

## 6. What a FAIL records

<Fields beyond the shared ones (row, location, steps to reproduce, screenshots on copies, tool versions), and any PDF instruction about continuing past a failure.>
