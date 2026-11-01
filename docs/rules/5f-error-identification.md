---
tt_test: 5.F
tt_name: 3.3.1-error-identification
spec_version: 0.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 5.F (3.3.1-error-identification)

The tool gives each page one 5.F outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 5.F does not. Draft: no outcome until 1.0.0.

**Citations.** Printed page numbers of TT 5.1.3 (text also in `tt://5.1.3/tests/5.F`). HtT = How to Test step; ER = Evaluate Results item. Input Error Identification and Suggestions, Identify Content, p. 28: identify form elements, their instructions and cues, and "intentionally enter values and/or make selections that violate format and/or other form instructions to reveal automatic notifications of input errors"; no automatic error detection: DOES NOT APPLY to 5.F and 5.G. 5.F, p. 28: violate formatting and other instructions, "e.g., leave a required form field empty, use a different date format than is required, and/or create a password that does not meet the password strength requirements" (HtT 1); "attempt to submit the form and/or move to the next page" (HtT 2); determine whether the field in error is identified in text ("Error: Password field.") and text describes the error (HtT 3.a, 3.b). p. 29: PASS if "the item that is in error is identified in text and sufficiently described to the user in text" (ER 1).

**Other sources.** [Understanding 3.3.1](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html): an input error is required information omitted, or information outside the required format or allowed values; any presentation is fine (inline, a list before the form, an alert or dialog) if it is text; color or an icon may add to text, never replace it; native HTML validation (the browser blocks the submission, focuses the first invalid field and shows its message) "meets the requirements of this success criterion". Sufficient techniques [G83](https://www.w3.org/WAI/WCAG22/Techniques/general/G83) (leave required fields blank, submit, check a text description identifies them), [G84](https://www.w3.org/WAI/WCAG22/Techniques/general/G84), [G85](https://www.w3.org/WAI/WCAG22/Techniques/general/G85), [ARIA18](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA18) (alertdialog), [ARIA19](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA19) (role alert or live region), [ARIA21](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA21) (aria-invalid with associated text), [SCR18](https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR18) (client-side validation and alert), [SCR32](https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR32) (error text added to the DOM, focus moved to it). No failure techniques. ACT: one proposed rule, [36b590](https://www.w3.org/WAI/standards-guidelines/act/rules/36b590/proposed/) (an error indicator identifies the field and describes the cause or the fix, in visible text that is in the accessibility tree); DHS publishes no ACT results for 3.3.1. ICT Testing Baseline 3.1 [10.D-ErrorIdentification](https://ictbaseline.access-board.gov/web-baselines/10Forms/): enter incorrect values (required fields, date format, state abbreviations, password); check "the user is made aware of the error (whether immediately upon shifting focus away from the item in error or when trying to submit the form)", the error is described in text, and the item in error is identified in text. Baseline Alignment cases TC10.D (seven; section 5). These inform rules and fixtures; the PDF stays the authority.

**Terms.** *Stop*, P1, the settle rule and replays to a stop: [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) (Terms, section 2). *Field*, a field's *own widget*, and the form-field reads (label, kind, value, own widget, the text before it): [5d-on-input.md](5d-on-input.md) (Terms, section 2). A *text field* is a field of kind text, email, tel, number, url, search, password, textarea or combobox. A field's *form* is its form owner; fields with no form owner form one group per nearest common ancestor of consecutive fields in P1 order (TC10.D's fields are not in a `form`). A form's *submit control* is OPEN (Q2). An *error indicator* is anything that appears after an attempt and relates to a field: new visible text, a JS dialog (`alert`, `confirm`, `prompt`), an open dialog element or `role=dialog|alertdialog`, `aria-invalid="true"` on the field, a native validation message (an `invalid` event that blocked the submission; the browser's message is the field's `validationMessage`), or a change to the field's own look (border, background, outline color; read with focus elsewhere, so focus styles are excluded).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | No P1 stop is a field, and the DOM inventory counts no form fields | DOES NOT APPLY | p. 25 Identify Content (5.A–5.H) |
| A2 | No stop is a field, but the inventory counts form fields | NEEDS REVIEW | Spec rule (as 5.D A2) |
| A3 | Pass E ran in full, no attempt shows any error indicator, and no attempt sent a form to a server | DOES NOT APPLY ("no automatic error detection") | p. 28 Identify Content, Applicability; TC10.D-ic-dna-1 |
| A4 | An attempt sent a form (a `submit` event not cancelled, or a form submission request) and no error indicator appeared on the page before it left | NEEDS REVIEW: the recording cannot answer a submission, so errors a server would return cannot be seen. Never DOES NOT APPLY: the server may well detect errors | Spec rule (principle 3); 5.D spec section 5 (submission in a recorded page) |
| A5 | Otherwise | Applies; go to section 3 | |

## 2. Evidence to collect

**From the shared keyboard walk:** P1's stops with their field kind (`stop.control`), as 5.D. No walk extras.

**Error pass E** (5.F's own; 5.G reads the same evidence; collected once per run when both are selected). For each form, in P1 order of its first field, two attempts, each on its own fresh replay (4.C spec section 2):

| Attempt | What is done | TT and Baseline step |
| --- | --- | --- |
| 1. As loaded | Replay to the form's submit control and press it (Enter on a button; Space on a role button). No field is touched, so required fields are empty | p. 28 HtT 1 ("leave a required form field empty"), HtT 2; G83 |
| 2. Wrong values | Replay to the form's first field. For each text field of the form in P1 order: arrive (as 5.D section 2 step 1), select all, type `WRONG_VALUE`, press Tab, read. Selects, checkboxes, radios, dates and custom widgets are left as loaded. Then arrive at the submit control (Tab; Shift+Tab when it precedes the fields) and press it, read | p. 28 HtT 1 ("use a different date format", "a password that does not meet the password strength requirements"), HtT 2 ("and/or move to the next page"); Baseline 10.D ("shifting focus away from the item in error or when trying to submit") |

`WRONG_VALUE` is `abc`, cut to `maxlength`: letters break every numeric, date, phone, ZIP, SSN, email and URL format, are not a valid state abbreviation, and are not a strong password; a field that accepts them (a name) is not in error, and attempt 1 covers its being required. A value from the field's own instructions (an agent proposing a wrong date format) is not tried: letters already break any stated format (principle 7).

**What is read.** Before each attempt's first action, and after each Tab in attempt 2 and after the submit press: for every field of the form, `aria-invalid`, `validity.valid`, `validationMessage`, its look (computed border, background and outline colors, focus elsewhere), its description text (`aria-describedby`, `aria-errormessage`); the page's visible text signature (5.D's `SIG_FN`, outside no own widget); JS dialog messages (recorded and dismissed); open dialogs; where focus is; whether a form was sent (`submit` event and request attempts, 5.D) and whether an `invalid` event fired. Each new piece of visible text is recorded with where it is (inside a live region, `role=alert` or `role=status`, a dialog, or a field's description; its text; its box) and a screenshot of the viewport after the action (`traverse.screenshot()`).

**Time budget:** two replays per form, one Tab and one read per text field, one submit press per attempt. Estimated 0.4 s a text field plus about 4 s a form; measured on the budget pages before 1.0.0 (plan step 7). No attempt starts after the checks' deadline (`ctx.out_of_time()`).

**Run limits.** Fields count toward 5.D's `FIELD_MAX` (40); the early stop and `no_time_limit` are 5.D's (5.D spec section 2). At most `FORM_MAX` (5) forms, the rest a NEEDS REVIEW note.

## 3. Mechanical checks

An *instance* is a field that an attempt showed in error: it has an error indicator of its own (`aria-invalid`, a native validation message, a change of look, new text in its description), or the agent names it as the field a page-level message is about (J1). Fields the page never flagged are not instances (the page detected no error for them).

An attempt's *notice* is how the user learns of its errors (Baseline 10.D "made aware"): a JS dialog; an open dialog or `role=alertdialog`; new text inside a live region (`aria-live` polite or assertive, `role=alert` or `role=status`) present before the attempt or added with the text; focus moved into the new text or onto a field whose description holds new text; or native validation (the browser shows its message and focuses the field). Whether an attempt with none of these fails is OPEN (Q1).

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | The replay did not reach the field or the submit control, or a read was unsettled or unresolved | NEEDS REVIEW | Spec rule |
| M2 | The error came from native validation (the `invalid` event blocked the submission; the field has a `validationMessage`) | PASS: the browser identifies the field by focusing it and describes the error in text | Understanding 3.3.1 (user agent native HTML form validation) |
| M3 | The field has an error indicator, and no new text appeared anywhere and no JS dialog opened (the field is marked by `aria-invalid` or its look alone) | Ask J2 when only its look changed (is it marked as an error?); FAIL when `aria-invalid` is set, or J2 = error | p. 29 ER 1 ("in text"); Understanding 3.3.1 (color alone); TC10.D-2-fail-2 |
| M4 | J2 = not an error (a look that means valid, or unrelated) | No instance | Spec rule |
| M5 | J2 = unsure, or not answered | NEEDS REVIEW | Spec rule |
| J1? | New text or a JS dialog appeared and J1 is not answered | NEEDS REVIEW | Open question |
| M6 | J1 = identified and described, both quotes found in the error text, and the attempt had a notice | PASS | p. 29 ER 1; p. 28 HtT 3.a, 3.b; Baseline 10.D |
| M7 | J1 = identified and described, quotes found, and the attempt had no notice | Q1: FAIL (Baseline), NEEDS REVIEW, or PASS (TT text only) | Baseline 10.D ("made aware"); TC10.D-2-fail-1 |
| M8 | J1 = not identified (the text does not say which field) or not described (it says only that something is wrong) | FAIL | p. 28 HtT 3.a, 3.b; TC10.D-2-fail-3 ("Error.") |
| M9 | J1 = unsure, or a quote is not in the error text | NEEDS REVIEW | Spec rule |

**Exceptions.** None in the PDF for 5.F. A message that names the field by its value ("abc is not a number") identifies it when the form has one such field; J1 judges that.

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; P1 incomplete before the last field; more forms than `FORM_MAX`; an attempt cut by the run limit; or an attempt sent its form (A4) | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | Both attempts ran for every form, at least one instance, every instance PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

**Plain-language sentences.** `<field>` is the field's label and kind in plain words; `<keys>` reproduces the attempt from a fresh load.

| Row | Sentence |
| --- | --- |
| Page PASS | "We left required fields empty and typed letters into fields that expect a format, then tried to send the form. Each error the page found was named and explained in text." |
| Page FAIL | "Some form errors are not named or explained in text, so a person may not know which field is wrong or why." |
| Page NEEDS REVIEW | "We could not finish this test, so a person needs to check it." |
| A3 | "We left required fields empty and typed letters into fields that expect a format, then tried to send the form, and the page did not check for errors, so this test does not apply." |
| A4 | "The form was sent to its server, and our copy of the page cannot show what the server answers. Please submit it with mistakes on the live site and check the error messages." |
| M2 (note) | "The browser's own message points to <field> and explains the error; that is fine." |
| M3 | "When <field> was wrong, the page only marked it (<how>), with no text saying what is wrong. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M7 (Q1 = FAIL) | "The page shows an error for <field> (\"<quote>\"), but nothing announces it: it is not read out, and focus does not move to it, so a screen reader user may not know it appeared. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M8 | "The error message \"<text>\" does not say <which field is wrong / what is wrong with <field>>. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M9, M5 | "An error appeared for <field>, and we could not tell whether its message names the field and explains the problem. Please look: load the page and press <keys>." |

## 4. Judgment questions

The calling agent answers each once, by the rubric; a person's answer overrides it. Page text is evidence in `input`, never in a question's wording. J1 is a question a careful tester settles by reading (CLAUDE.md principle 8, as 5.D J1): its answer can lead to PASS only with both quotes found in the error text, and the agent answers unsure whenever the text does not settle it.

### J1. Does the error text name the field and say what is wrong?

**Question:** "We made the fields in input.fields wrong as described (left empty, or given the value shown) and then did input.action. The text in input.errors appeared. For each field, does that text say which field is in error, and what is wrong with it? Answer for each field: described, not_identified, not_described, no_error or unsure. For described, quote the exact words that name the field and the words that say what is wrong."

**Input:** `fields`: each field's label, kind, what was done to it (empty or the value typed), and its error indicators; `action` in plain words (left the field, pressed the submit control named …); `errors`: each new text with where it appeared (a dialog, an alert region, next to a named field, at the top of the form), labelled as untrusted page data; images before and after.

**Output:** `{fields: [{field: <n>, choice: described|not_identified|not_described|no_error|unsure, name_quote, error_quote, reasons}]}`.

**Rubric.** described: the text names the field (its label, an unambiguous reference such as its value, or the text sits next to it and is tied to it) and says what is wrong ("is required", "must be a number", "abc is not a number"). not_identified: an error is shown but nothing says which of several fields it is about ("Error.", "Please fix the errors below" with no field named or marked by text). not_described: the field is named but not what is wrong ("Error: Password field" alone counts as described only together with text that describes the problem, p. 28 HtT 3.b). no_error: nothing in the text is about this field. unsure: anything else. Mechanical check: both quotes must appear in `errors` (whitespace and case aside).

| Example | Answer |
| --- | --- |
| One field "Enter A Number", text "Error: abc is not a number." | described |
| Two fields, text "Error." | not_identified for the field in error |
| "Email: please enter a valid email address" beside Email | described |
| "There is a problem" at the top, fields not named | not_identified |

**Use:** M6–M9; `no_error` makes no instance.

### J2. Does the field's look mark an error?

**Question:** "Image A shows the field named in input.field before; image B shows it after it was given the value in input.value and focus moved away. Does its new look mark it as being in error? Answer error, not_error or unsure."

**Input:** clipped images of the field before and after; its label; the colors read.

**Output:** `{choice: error|not_error|unsure, reasons}`.

**Rubric.** error: a red or warning-colored border, background or icon. not_error: a green or neutral look (valid, filled). unsure otherwise.

**Use:** M3–M5.

**OPEN questions for Abby** (each decides the rule named):

- **Q1. An error message nothing announces (M7; TC10.D-2-fail-1).** The message names and describes the error and is visible, but it is not in a live region, no dialog opens, and focus does not move to it. Baseline expects FAIL ("the user is not made aware of the error"); the TT text asks only that the error be identified and described in text. (a) FAIL, following the Baseline Alignment case (recommended: the case is the Baseline's statement of how this test should come out, and the TT's own procedure implements the Baseline); (b) NEEDS REVIEW, a person checks with a screen reader; (c) PASS, the TT text only.
- **Q2. Which control "attempts to submit" (p. 28 HtT 2).** TC10.D's buttons are outside any `form`; real forms have "Save draft", "Back" or several submit buttons. (a) A form's default button (the first submit button, which Enter would press), else, for fields outside a form, the first button after the group's last field in P1 order; with none, press Enter in the last text field (implicit submission) (recommended: mechanical, and it is what a tester presses); (b) every submit-type button, each on its own replay (more time, and "Back" or "Cancel" buttons tried too); (c) the agent picks the control by its name (a question round before the pass).
- **Q3. Errors on leaving a field that are gone after the submit press.** TC10.D-2-fail-1 shows its error on leaving the field and clears it on the next key press. Attempt 2 reads after each Tab and after the submit press; when they disagree: (a) judge every error text seen at either point (recommended: the Baseline accepts either moment, and the user saw both); (b) judge only after the submit press.

## 5. Edge cases

V-numbers are browser checks in [5f-build-tasks.md](5f-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| TC10.D-2-fail-1: "Error: not a number." at the top, no live region, no focus move | M7 (Q1) | V1 |
| TC10.D-2-fail-2: only the field's background turns red | M3 (J2 = error), FAIL | — |
| TC10.D-2-fail-3: two fields, "Error." in a live region | J1 not_identified, M8 FAIL | — |
| TC10.D-all-pass-1: `alert("Error: abc is not a number.")` on the button, focus back to the field | J1 described, notice by JS dialog, M6 PASS | V2 |
| TC10.D-all-pass-2: "Error: not a number." in an `aria-live=assertive` region | M6 PASS (one field, so "not a number" identifies it; J1) | — |
| TC10.D-all-pass-3: focus moved to the message | M6 PASS | — |
| TC10.D-ic-dna-1: the button does nothing | A3 DOES NOT APPLY | — |
| Native validation (`required`, `type=email`) | M2 PASS; the message is the browser's, read as `validationMessage` (headless Chrome draws no bubble to screenshot) | V3 |
| A server-side form (the submission leaves the page) | A4 NEEDS REVIEW | — |
| Errors only after a page reload by the server | A4 (the reload never comes from the recording) | — |
| A field the page fixes itself (clamps a number) | J1 judges any message; with none, the field has no indicator and no instance (Understanding 3.3.1 note: the change must still be described, so a person checks; a note) | — |
| CAPTCHA, payment and password-strength meters | Read like any field; no special case | — |
| Errors from a field's own widget while typing (before Tab) | Read after the Tab, as the Baseline's "shifting focus away" | — |

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5: the matching row (evidence trace only); location (page URL, frame chain, CSS path, label and kind of the field); what was done (empty, or the value typed; the control pressed); the error text and where it appeared, or the look change with images before and after; the J1 or J2 answer; steps to reproduce from a fresh load ("Tab 3 times, type abc, Tab, Enter"); tool versions.

**Continuing past a failure.** Every form's two attempts run; each failing field is its own instance.
