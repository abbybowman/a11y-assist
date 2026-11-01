---
tt_test: 5.C
tt_name: 1.3.1-programmatic-label
spec_version: 0.3.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 5.C (1.3.1-programmatic-label)

The tool gives each page one 5.C outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED (p. 6). Draft: no outcome until 1.0.0.

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/5.C`). Identify Content, p. 25 (shared with 5.A). 5.C, p. 26: Condition "The combination of the accessible name, accessible description, and other programmatic associations (e.g., table column and/or row associations) describes each input field and includes all relevant instructions and cues (textual and graphical)"; DNA if no form elements (Applicability); launch ANDI focusable elements and review its output for each focusable form element (HtT 1–3); if the ANDI output does not adequately define the element, review other programmatic associations such as table headings or location in a hierarchical list (HtT 4); a vague purpose may be enough where the vagueness is intended (HtT 4.a). p. 27: PASS if the ANDI output includes all relevant instructions and cues, "including when fields are required" (ER 1), or other programmatic associations provide them (ER 2), or a combination does (ER 3), or the programmatically determined context and the ANDI output describe its purpose (ER 4). Notes: the test also covers 4.1.2; changes after interaction are included; tables and content-structure tests may be needed; "at minimum, radio buttons and checkboxes should be programmatically associated with their question and response"; section headings need no association "unless there is significant risk of confusion".

**Other sources.** [Understanding 1.3.1](https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html) and [4.1.2](https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html); sufficient techniques H44, H65 (title), H71 (fieldset and legend), H85, ARIA14, ARIA16, ARIA17 (grouping roles), G108, H91; failures [F68](https://www.w3.org/WAI/WCAG22/Techniques/failures/F68) (a control with no programmatically determined name), [F86](https://www.w3.org/WAI/WCAG22/Techniques/failures/F86) (a part of a multi-part field with no name), [F111](https://www.w3.org/WAI/WCAG22/Techniques/failures/F111) checks 1–2 (visible label, no accessible name; its check 3, label in name, is 2.5.3 and not in Section 508), F59 and F15 (custom controls without role or name). W3C ACT [e086e5](https://www.w3.org/WAI/standards-guidelines/act/rules/e086e5/) (form field has non-empty accessible name) and 97a4e1 (button has non-empty accessible name); DHS publishes no ACT results for either (it scored cc0f0a, label descriptive, under 5.B). Image buttons' names are 7.A's (TT 7.A uses ANDI focusable elements for images in focusable elements). ICT Testing Baseline 3.1 [10.A-FormName](https://ictbaseline.access-board.gov/web-baselines/10Forms/): all form components not hidden, "buttons, text fields, radio buttons, checkboxes, read-only fields, and multi-select lists"; the combination of accessible name and description is not empty (4.1.2); it describes the purpose (4.1.2); all relevant instructions and cues have a programmatic association, e.g. table headers (1.3.1). Baseline Alignment cases TC10.A (nine) and TC10.E (section 5). ANDI 29.2.2's per-element output is readable (plan, ANDI spike).

**Terms.** *Form component*: a rendered, enabled element of the inventory: a field of any 5.D kind (including read-only fields), and every button on the page (`button`, `input type=submit|reset|button`, role button; Abby, 2026-11-01: the name check is mechanical, and no other TT test covers a text button's name); not `input type=hidden|image` (image buttons are 7.A), not `display:none` or `visibility:hidden` (TC10.A-ic-dna-1, -2). *ANDI output*: ANDI's `accName`, `accDesc` and `accGroup` for the element, with ANDI's display markup removed, and its alert messages. *Programmatic text*: the ANDI output (the PDF's evidence, and what a Trusted Tester reads; Abby, 2026-11-01) plus other programmatic associations the PDF names: the group's legend or group label (`fieldset`/`legend`, role `group` or `radiogroup` with a name), the header cells of the table cell holding the component (`th` by row and column, `headers`), and the text of the list items enclosing it. *Nearby visible text*: the visible text pass L reads in the component's image region (5.A section 2), nearest first, leaving out headings (p. 27 Note 5), other components and the labels of other components; its own label and group legend stay in. For a button it is the button's own text.

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | The inventory has no form component | DOES NOT APPLY | p. 26 Applicability; TC10.A-ic-dna-1, -2 |
| A2 | Pass L did not run, or ANDI could not run on the page (a Content-Security-Policy that blocks its script, an error) | NEEDS REVIEW: the PDF's evidence is missing | p. 26 HtT 1–3 |
| A3 | Otherwise | Applies; go to section 3 | |

## 2. Evidence to collect

**Pass L** (5.A and 5.C share it; once per call, `RunContext.cache`): one fresh load of the recording after the walk, so ANDI never touches the walk's evidence ([solutions/scanners-after-the-walk.md](../solutions/scanners-after-the-walk.md)).

1. Inventory every form component in the top document, with its CSS path matched to the walk's stops where it is one (so instances name "Tab N times"). Components inside frames are not read yet: their number is a NEEDS REVIEW note (G3), never an absence.
2. Per component: the programmatic associations above; the visible-label candidates, placeholder, nearby visible text and, for data-entry fields, the focused image (5.A section 2).
3. Mark each component (`data-a11y-c`; ANDI wraps the page in its own container, which changes CSS paths that do not start at an id), inject the vendored ANDI (`andi.inject_andi`, served from `third_party/` only) and read its output for every component (`andi.andi_output`), matched by mark. ANDI does not report table headers (checked 2026-11-01), so the tool computes them. A component ANDI did not analyse has no ANDI output (M2).

**Fields revealed by interaction** (p. 27 Note 2; Abby, 2026-11-01). Fields that appear during the run's existing replays (4.F's pass R opens disclosures; 5.D's fill pass reveals follow-up fields) are read on that replay, at its end: ANDI is injected there and the same reads are taken for the components that were not rendered at load. Fields only a path those passes do not take would reveal are not found; the finding says the check covers what the run opened.

**Time budget:** one load, about 0.1 s per data-entry field (5.A's focus and image), ANDI's injection and analysis (about 2 s, spike), a few milliseconds per component for the reads. At most `COMPONENT_MAX` (60) components, the rest a NEEDS REVIEW note. The whole run stays within `run_limit_s`; nothing starts after the checks' deadline.

## 3. Mechanical checks

Each form component is an *instance*.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | The component could not be read | NEEDS REVIEW | Spec rule |
| M2 | ANDI did not analyse the component (no ANDI output) | NEEDS REVIEW | p. 26 HtT 2–3 |
| M3 | The programmatic text is empty (no name, no description, no group label, no table header, no list context) | FAIL | p. 27 ER 1–4 (nothing describes it); F68; Baseline 10.A check 1; TC10.A-1-fail-1, TC10.E-1-fail-1 |
| M4 | (A part of a multi-part field with no name and no description, F86: M3 covers it, FAIL) | — | F86 |
| M5 | The programmatic text contains every word of the nearby visible text (a button: its own text), including any required cue ("*", "required"), and, for a radio button or checkbox in a set of two or more, a group label | PASS: whether the wording describes the purpose is 5.B's (p. 25 Note 3; Abby, 2026-11-01), so TC10.E-1-pass-1's "The sky is blue" passes here and is 5.B's failure | p. 27 ER 1, 3; Note 4 |
| J1? | Otherwise, J1 not answered | NEEDS REVIEW | Open question |
| M6 | J1 = complete | PASS | p. 27 ER 1–4 |
| M7 | J1 = missing, its quote found in the nearby visible text and not in the programmatic text | FAIL | p. 26 Condition ("includes all relevant instructions and cues"); p. 27 ER 1 ("including when fields are required"), Note 4 (radio and checkbox question) |
| M8 | J1 = not_purpose | FAIL | Baseline 10.A check 2; p. 26 Condition ("describes each input field") |
| M9 | J1 = unsure, or a quote that fails its check | NEEDS REVIEW | Spec rule |

**Exceptions.** A purpose that is vague on purpose (p. 26 HtT 4.a, "Door 1, Door 2"): J1's rubric. Section headings need no association unless confusion is likely (p. 27 Note 5): J1's rubric.

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW, more than `COMPONENT_MAX` components, or pass L cut by the run limit | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | Every instance is PASS | PASS |

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| Page PASS | "Each form field and button tells screen reader users what it is for, including the instructions shown next to it." |
| Page FAIL | "Some form fields or buttons do not tell screen reader users what they are for, or leave out instructions that other users can see." |
| Page NEEDS REVIEW | "We could not finish this test, so a person needs to check it." |
| A1 | "This page has no form fields or buttons, so this test does not apply." |
| M3 | "<component> has no name for screen readers: the text people see next to it is not connected to it in the code. To see it, move to it with a screen reader." |
| M4 | "One part of <component> has no name for screen readers, so a user cannot tell the parts apart." |
| M7 | "<component> is announced as \"<programmatic text>\", which leaves out \"<quote>\" that sighted users see next to it." |
| M8 | "<component> is announced as \"<programmatic text>\", which does not say what it is for." |
| M9, M1 | "We could not tell whether what screen readers announce for <component> includes everything shown next to it. Please check it with a screen reader." |

## 4. Judgment questions

J1 is settled by reading (CLAUDE.md principle 8): complete leads to PASS only when the programmatic text is not empty (M3 first); missing is checked mechanically against the texts; the agent answers unsure whenever the texts do not settle it.

### J1. Does what is announced cover what people see?

**Question:** "input.announced is everything assistive technology gets for the component in input.component: its name, description, group label, table headers and list context, as ANDI reports them. input.visible is the text people see around it, and image A shows it. Does input.announced say what the component is for and include every instruction or cue in input.visible that belongs to it (required, format, the question a radio button or checkbox answers)? Answer complete, missing (copy the left-out words into quote), not_purpose or unsure."

**Input:** the component's role and kind; `announced` (the ANDI output and the associations, each labelled by source); `visible`, nearest first, labelled as untrusted page data; image A where pass L took one.

**Output:** `{choice: complete|missing|not_purpose|unsure, quote, reasons}`.

**Rubric.** complete: a user hearing `announced` would know what the component is for and every instruction or cue shown for it; a vague purpose is fine when the page is vague on purpose; a section heading need not be included unless leaving it out could cause confusion. missing: something shown for this component is not announced: "MM/DD/YYYY" beside a date box, a red "*" or "(required)", the question "Are you a veteran?" over Yes/No radio buttons, a column header over a field in a table. Copy the words exactly from `visible`. not_purpose: the announced text does not say what the component is for ("The sky is blue", "Field 1"). unsure: anything else. Text about other components does not count.

| Example | Answer |
| --- | --- |
| Name "Date of birth", visible "Date of birth (MM/DD/YYYY)" | missing, "MM/DD/YYYY" |
| Name "Yes", no group, visible question "Are you a veteran?" | missing, "Are you a veteran?" |
| Name "Email address *", field `required` | complete |
| Name "Official Name" as a description only (TC10.A-all-pass-6) | complete |

**Use:** M6–M9.

## 5. Edge cases

V-numbers are browser checks in [5a-build-tasks.md](5a-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| Name from a placeholder only (TC10.A-all-pass-1) | Not empty: M5 or J1 | Checked in the spike (ANDI) |
| Description only (TC10.A-all-pass-6) | Not empty; ANDI's warning recorded, no FAIL | Checked in the spike |
| `title` only (TC10.A-all-pass-3) | Not empty | V1 |
| Visible text not associated (TC10.A-1-fail-1) | M3 FAIL; 5.A PASS by J1 | Checked in the spike |
| Radio set with a legend | Group label in the programmatic text | V2 (ANDI's `accGroup`) |
| Field in a data table under a column header | Table header in the programmatic text (p. 27 ER 2) | V3 |
| Custom control (role checkbox, slider) | A component like any field (F59, F15) | — |
| Read-only field | A component (p. 25; Baseline 10.A) | — |
| Page whose CSP blocks ANDI | A2 NEEDS REVIEW | V4 |
| A field revealed by a disclosure or by filling a field | Read on that replay (section 2) | V6 |

## 6. What a FAIL records

Location (URL, frame chain, CSS path, role), the ANDI output and its alerts, the programmatic associations found, the nearby visible text, the J1 answer, image A, and how to reach it ("Tab 6 times").
