---
tt_test: 5.B
tt_name: 2.4.6-label-descriptive
spec_version: 1.0.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 5.B (2.4.6-label-descriptive)

The tool gives each page one 5.B outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED (p. 6).

**Citations.** Printed pages 25–26 of TT 5.1.3 (text also in `tt://5.1.3/tests/5.B`). Forms Identify Content, p. 25 (as 5.A). Applicability, p. 25: DNA "if the page does not have form elements, if all form elements are disabled, or if no visual labels are provided for form elements". HtT 1–2, p. 26: review the visual labels and instructions for each component; determine whether they "sufficiently describe the purpose and applicable data requirements (date formats, required fields, data type, etc.)". ER, p. 26: each visual form label is "sufficiently clear and descriptive, so users know what input data is expected" (ER 1) and each visual button label "so users know its function" (ER 2). Notes, p. 26: an error message is not enough to communicate the expected format; a label can be graphical or textual; labels that change automatically or by interaction are included.

**Other sources.** [Understanding 2.4.6](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html): labels "do not need to be lengthy. A word, or even a single character, may suffice"; the criterion "does not require headings or labels", only that labels provided are descriptive; a control can have a good accessible name and still fail if its label is not descriptive. [G131](https://www.w3.org/WAI/WCAG22/Techniques/general/G131): for each component with a label, identify its purpose and "Check that each label makes the component's purpose clear". W3C ACT [cc0f0a](https://www.w3.org/WAI/standards-guidelines/act/rules/cc0f0a/): each visible label, "together with its visual context, describes the purpose"; visible headings are context (repeated "Name"/"Street" under visible "Shipping" and "Billing" pass; the same under off-screen headings fail); "Menu" or "Info:" fail. DHS scored 14 of its 16 current cases (7 PASS, 5 FAIL, 2 DNA); ours follow the visual reading, as DHS's do (DHS passed the case whose visible label is hidden from assistive technology, which ACT calls inapplicable). ICT Testing Baseline 3.1 10.B-FormDescriptiveLabel: labels "describe purpose, inform users what input data is expected and, if applicable, what format is required". No Baseline Alignment case for 10.B.

**Terms.** *Pass L*, *component*, *data-entry field*, *visible label*: [5a-label-provided.md](5a-label-provided.md) Terms and [5c-programmatic-label.md](5c-programmatic-label.md) section 2. An *item* is a data-entry field with a visible label or visible text near it (its pass L reads), or a button with visible text. A field with neither is not an item: it has no visual label to judge (Applicability; 5.A FAILs it). A component's *form* is its form owner (or "none"); fields of one form are judged together, with their group labels (legends) and headings as context (cc0f0a).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | Pass L found no enabled, rendered form component | DOES NOT APPLY | p. 25 Applicability |
| A2 | Components exist, but none is an item (no visual labels) | DOES NOT APPLY | p. 25 Applicability ("no visual labels are provided") |
| A3 | Pass L did not run | NEEDS REVIEW | Spec rule |
| A4 | Otherwise | Applies; go to section 3 | |

## 2. Evidence to collect

Nothing of its own: pass L (shared with 5.A and 5.C; components now record their form). For each item: kind, type, the visible label text, up to three strings of visible text near it, its group label, required, placeholder (shown apart: not a label), the 5.A image of a field, a button's visible text.

**Time budget:** none beyond pass L (measured 0.0 s on both budget pages, 2026-11-02).

## 3. Mechanical checks

Each item is an instance.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| J1? | Its form's J1 not answered | NEEDS REVIEW | Open question (Abby, 2026-11-02: one question per form) |
| M1 | J1 = all_descriptive | PASS | p. 26 ER 1, 2 |
| M2 | J1 = some_not_descriptive and the item is named | FAIL | p. 26 ER 1, 2; cc0f0a |
| M3 | J1 = some_not_descriptive, valid numbers, the item not named | PASS | p. 26 ER 1, 2 |
| M4 | Anything else (unsure, or numbers missing or not in the list) | NEEDS REVIEW | Spec rule |

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing each item |
| G3 | Any instance is NEEDS REVIEW, or pass L is incomplete | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | Every instance is PASS | PASS |

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| Page PASS | "Each form field's and button's label says what it is for." |
| Page FAIL | "Some labels do not say what to enter or what the button does: <items>." |
| A1 | "This page has no form fields, so this test does not apply." |
| A2 | "No form field on this page has a label people can see, so there is no label to judge here (a missing label is reported by the label test)." |

## 4. Judgment questions

J1 is settled by looking (CLAUDE.md principle 8); the agent answers unsure whenever the evidence does not settle it.

### J1. Do these labels describe their fields and buttons?

**Question:** "input.items are the fields and buttons of one form, in page order, with the label people see for each (label), text near it (near), its group's label (group) and, for fields, a picture (image). Taken with what is around them, does each label make clear what to enter (including any format the field needs, such as a date) or what the button does? Answer all_descriptive, some_not_descriptive (put the numbers of the ones that are not in elements) or unsure."

**Input:** per form: items (number, kind, type, label, near, group, required, placeholder, image), and the form's headings and legends.

**Output:** `{choice: all_descriptive|some_not_descriptive|unsure, elements: [numbers], reasons}`.

**Rubric.** descriptive: names what to enter or do, even in one word ("First name", "Search" next to a search box, a magnifier icon on a search button, "Name" under a visible "Billing address" heading). not descriptive: unrelated or empty of meaning ("Menu", "Info", "The sky is blue", "Field 1"), the same label on several fields with nothing visible to tell them apart, a date or number field whose required format appears only in an error message. A placeholder is not a label. unsure: whenever the picture or text does not settle it.

| Example | Answer |
| --- | --- |
| "First name:", "Date of birth:" (date field) | all_descriptive |
| "Menu" on a text field | some_not_descriptive, [1] |
| "Name", "Street" twice, section headings off screen | some_not_descriptive, all four |
| "The sky is blue" on a text field | some_not_descriptive, [1] |

**Use:** M1–M4.

## 5. Edge cases

| Case | Rule |
| --- | --- |
| A field labelled only by a placeholder | Not an item (A2 when it is the only field; 5.A FAILs it) |
| A field labelled by an adjacent button ("Go") | The button's text is its near text; J1 judges it |
| Icon-only button | Not an item: no visible text to judge, and pass L takes no picture of buttons (Abby, 2026-11-02) |
| Fields revealed by interaction | Read where 4.F or 5.D revealed them (pass L) |

## 6. What a FAIL records

Each item named (its label, near text, kind, form) and the J1 answer with its reasons.
