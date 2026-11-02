---
tt_test: 5.F
tt_name: 3.3.1-error-identification
spec_version: 1.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 5.F (3.3.1-error-identification)

The tool gives each page one 5.F outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 5.F does not.

**Citations.** Printed page numbers of TT 5.1.3 (text also in `tt://5.1.3/tests/5.F`). HtT = How to Test step; ER = Evaluate Results item. Input Error Identification and Suggestions, Identify Content, p. 28: identify form elements, their instructions and cues, and "intentionally enter values and/or make selections that violate format and/or other form instructions to reveal automatic notifications of input errors"; no automatic error detection: DOES NOT APPLY to 5.F and 5.G. 5.F, p. 28: violate formatting and other instructions, "e.g., leave a required form field empty, use a different date format than is required, and/or create a password that does not meet the password strength requirements" (HtT 1); "attempt to submit the form and/or move to the next page" (HtT 2); determine whether the field in error is identified in text ("Error: Password field.") and text describes the error (HtT 3.a, 3.b). p. 29: PASS if "the item that is in error is identified in text and sufficiently described to the user in text" (ER 1).

**Other sources.** [Understanding 3.3.1](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html): an input error is required information omitted, or information outside the required format or allowed values; any presentation is fine (inline, a list before the form, an alert or dialog) if it is text; color or an icon may add to text, never replace it; native HTML validation (the browser blocks the submission, focuses the first invalid field and shows its message) "meets the requirements of this success criterion". Sufficient techniques [G83](https://www.w3.org/WAI/WCAG22/Techniques/general/G83) (leave required fields blank, submit, check a text description identifies them), [G84](https://www.w3.org/WAI/WCAG22/Techniques/general/G84), [G85](https://www.w3.org/WAI/WCAG22/Techniques/general/G85), [ARIA18](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA18) (alertdialog), [ARIA19](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA19) (role alert or live region), [ARIA21](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA21) (aria-invalid with associated text), [SCR18](https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR18) (client-side validation and alert), [SCR32](https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR32) (error text added to the DOM, focus moved to it). No failure techniques. ACT: one proposed rule, [36b590](https://www.w3.org/WAI/standards-guidelines/act/rules/36b590/proposed/) (an error indicator identifies the field and describes the cause or the fix, in visible text that is in the accessibility tree); DHS publishes no ACT results for 3.3.1. ICT Testing Baseline 3.1 [10.D-ErrorIdentification](https://ictbaseline.access-board.gov/web-baselines/10Forms/): enter incorrect values (required fields, date format, state abbreviations, password); check "the user is made aware of the error (whether immediately upon shifting focus away from the item in error or when trying to submit the form)", the error is described in text, and the item in error is identified in text. Baseline Alignment cases TC10.D (seven; section 5). These inform rules and fixtures; the PDF stays the authority.

**Terms.** *Stop*, P1, the settle rule and replays to a stop: [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) (Terms, section 2). *Field*, a field's *own widget*, and the form-field reads (label, kind, value, own widget, the text before it): [5d-on-input.md](5d-on-input.md) (Terms, section 2). A *text field* is a field of kind text, email, tel, number, url, search, password, textarea or combobox. A field's *form* is its form owner; fields with no form owner in a document form one group (TC10.D's fields are not in a `form`). A form's *submit control* is chosen in section 2 (Submit control). An *error indicator* is anything that appears after an attempt and relates to a field: new visible text, a JS dialog (`alert`, `confirm`, `prompt`), an open dialog element or `role=dialog|alertdialog`, `aria-invalid="true"` on the field, a native validation message (an `invalid` event that blocked the submission; the browser's message is the field's `validationMessage`), or a change to the field's own look (border, background, outline color; read with focus elsewhere, so focus styles are excluded).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | No P1 stop is a field, and the DOM inventory counts no form fields | DOES NOT APPLY | p. 25 Identify Content (5.A–5.H) |
| A2 | No stop is a field, but the inventory counts form fields | NEEDS REVIEW | Spec rule (as 5.D A2) |
| A3 | Pass E ran in full, no attempt sent a form to a server, and no field is an instance (section 3: no error indicator, or J1 and J2 found none) | DOES NOT APPLY ("no automatic error detection") | p. 28 Identify Content, Applicability; TC10.D-ic-dna-1 |
| A4 | An attempt sent a form (a `submit` event not cancelled, or a form submission request) and no error indicator appeared on the page before it left | NEEDS REVIEW: the recording cannot answer a submission, so errors a server would return cannot be seen. Never DOES NOT APPLY: the server may well detect errors | Spec rule (principle 3); 5.D spec section 5 (submission in a recorded page) |
| A5 | Otherwise | Applies; go to section 3 | |

## 2. Evidence to collect

**From the shared keyboard walk:** P1's stops with their field kind (`stop.control`), as 5.D. No walk extras.

**Error pass E** (5.F's own; 5.G reads the same evidence; collected once per run when both are selected). For each form, in P1 order of its first field, two attempts, each on its own fresh replay (4.C spec section 2):

| Attempt | What is done | TT and Baseline step |
| --- | --- | --- |
| 1. As loaded | Replay to the form's submit control and press it (Enter on a button; Space on a role button); with no button, replay to the form's last text field and press Enter there (1.1.0). No field is touched, so required fields are empty | p. 28 HtT 1 ("leave a required form field empty"), HtT 2; G83 |
| 2. Wrong values | Replay to the form's first text or date field. For each text field and each native `type=date` field of the form in P1 order: arrive (as 5.D section 2 step 1); a text field: select all, type `WRONG_VALUE`; a date field: type the digits of `WRONG_DATE` in the field's order (as 5.D); press Tab (for a date, again while focus is still on the input's own parts, at most 5 times); read. Selects, checkboxes, radios, other date and time kinds and custom widgets are left as loaded. Then arrive at the submit control (Tab; Shift+Tab when it precedes the fields) and press it, read | p. 28 HtT 1 ("use a different date format", "a password that does not meet the password strength requirements"), HtT 2 ("and/or move to the next page"); Baseline 10.D ("shifting focus away from the item in error or when trying to submit"); Understanding 3.3.1 ("a birth date 2 years in the future") |

`WRONG_VALUE` is `abc`, cut to `maxlength`: letters break every numeric, date, phone, ZIP, SSN, email and URL format, are not a valid state abbreviation, and are not a strong password; a field that accepts them (a name) is not in error, and attempt 1 covers its being required. A value from the field's own instructions (an agent proposing a wrong date format) is not tried: letters already break any stated format (principle 7).

`WRONG_DATE` is a date outside the field's range: a year after its `max`, else a year before its `min`, else 1 January 2999. A native date input cannot take a wrong format (the browser enforces it), but it can take a date the page must refuse (Understanding 3.3.1's example: a birth date in the future). A date field is read through its input: the walk's stop is its first part, inside the input's own shadow root (5.D V3).

**Submit control** (p. 28 HtT 2, "attempt to submit the form and/or move to the next page"). The form's buttons are its submit buttons (`button` without a type or `type=submit`, `input type=submit|image`), or, for fields with no form owner, the buttons after the group's last field in P1 order up to the next field or heading. Skip any whose accessible name matches `SKIP_WORDS` (draft, later, progress, exit, back, previous, cancel, reset, clear, delete, remove, sign out, log out, print; whole words, any case): this test checks sending, not saving a draft or going back. A plain "Save" is not skipped: it often sends the form, and "Save draft", "Save for later" and "Save and exit" are caught by their other words (Abby, 2026-11-01). Of the rest, the first one whose name matches `SUBMIT_WORDS` (submit, send, continue, next, apply, sign in, log in, register, search, validate, check, verify, save, done, finish, go), else the first one. With no button at all, press Enter in the form's last text field (implicit submission). When the attempt shows no error indicator and sends nothing, J0 asks the agent which control on the form sends it (input: every button of the form with its name, in order); a control it names that was not pressed gets both attempts on fresh replays. J0 = none or unsure leaves the attempts as they are.

**What is read.** Error text seen after a Tab or after the submit press both count, even when the next key press clears it (Baseline 10.D: "whether immediately upon shifting focus away from the item in error or when trying to submit the form"; TC10.D-2-fail-1 clears its message on the next key press; no source requires an error message to persist). On the fresh load before any key (tabbing past a field can already show its error: TC10.D-2-fail-1 validates on leaving), and and after each Tab in attempt 2 and after the submit press: for every field of the form, `aria-invalid`, `validity.valid`, `validationMessage`, its look (computed border, background and outline colors, focus elsewhere), its description text (`aria-describedby`, `aria-errormessage`); the page's new visible text: the read on the fresh load notes every visible piece of text (its element's path and its words) and keeps the list in the browser's isolated world, and each later read returns only pieces not on that list (the fresh-load read also returns the first 200, which 5.H reads as the page's text), so an error message is found wherever it appears and however long the page is (1.1.0); JS dialog messages (recorded and dismissed); open dialogs; where focus is; whether a form was sent (`submit` event and request attempts, 5.D) and whether an `invalid` event fired and whether the page cancelled it (1.1.0). Each new piece of visible text is recorded with where it is (inside a live region, `role=alert` or `role=status`, a dialog, or a field's description; its text; its box) and a screenshot of the viewport after the action (`traverse.screenshot()`).

**Time budget:** two replays per form, one Tab and one read per text field, one submit press per attempt. Estimated 0.4 s a text field plus about 4 s a form; measured on the budget pages before 1.0.0 (plan step 7). No attempt starts after the checks' deadline (`ctx.out_of_time()`).

**Run limits.** Fields inside frames are not checked yet, and a field the page reads cannot find is not checked either: both are a NEEDS REVIEW note, never DOES NOT APPLY. Fields count toward 5.D's `FIELD_MAX` (40); the early stop and `no_time_limit` are 5.D's (5.D spec section 2). At most `FORM_MAX` (5) forms, the rest a NEEDS REVIEW note.

## 3. Mechanical checks

An *instance* is a field an attempt showed in error. A field gets its own error indicator from `aria-invalid`, a native validation message, a change of look, or new text in its description. When an attempt showed new text or a JS dialog and no field has an indicator of its own (a message at the top of the form, an alert box), every field the attempt made wrong is a candidate and J1 says which the message is about (`no_error`: not an instance). When some fields have their own indicator, only those are instances. Attempt 1 makes every field of the form wrong (empty); attempt 2 the text fields it typed into.

An attempt's *notice* is how the user learns of its errors (Baseline 10.D "made aware"): a JS dialog; an open dialog or `role=alertdialog`; new text inside a live region (`aria-live` polite or assertive, `role=alert` or `role=status`) present before the attempt or added with the text; focus moved into the new text or onto a field whose description holds new text; or native validation the page did not cancel (the browser shows its message and focuses the field; a page that cancels the `invalid` event hides the message, 1.1.0). An attempt with none of these fails (M7): Baseline 10.D ("the user is made aware of the error"; TC10.D-2-fail-1) and Understanding 3.3.1 for WCAG 2.0, which Section 508 incorporates ("users are aware that an error has occurred"; screen reader users "will not know there was an error until they encounter one of the indicators"). The TT text itself asks only for text (p. 29 ER 1); announcing text without a focus move is otherwise WCAG 2.1's 4.1.3, outside Section 508.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | The replay did not reach the field or the submit control, or a read was unsettled or unresolved | NEEDS REVIEW | Spec rule |
| M2 | The error came from native validation (the `invalid` event blocked the submission, the page did not cancel it, and the field has a `validationMessage`). A cancelled `invalid` event shows no message (pages cancel it to draw their own errors), so the field falls to the rows below (1.1.0) | PASS: the browser identifies the field by focusing it and describes the error in text | Understanding 3.3.1 (user agent native HTML form validation) |
| M3 | The field has an error indicator, and no new text appeared anywhere and no JS dialog opened (the field is marked by `aria-invalid` or its look alone) | Ask J2 when only its look changed (is it marked as an error?); FAIL when `aria-invalid` is set, or J2 = error | p. 29 ER 1 ("in text"); Understanding 3.3.1 (color alone); TC10.D-2-fail-2 |
| M4 | J2 = not an error (a look that means valid, or unrelated) | No instance | Spec rule |
| M5 | J2 = unsure, or not answered | NEEDS REVIEW | Spec rule |
| J1? | New text or a JS dialog appeared and J1 is not answered | NEEDS REVIEW | Open question |
| M6 | J1 = described, its quote found in the error text, and the attempt had a notice | PASS | p. 29 ER 1; p. 28 HtT 3.a, 3.b; Baseline 10.D |
| M7 | J1 = described, quote found, and the attempt had no notice | FAIL | Baseline 10.D ("made aware"); TC10.D-2-fail-1 |
| M8 | J1 = not identified (the text does not say which field) or not described (it says only that something is wrong) | FAIL | p. 28 HtT 3.a, 3.b; TC10.D-2-fail-3 ("Error.") |
| M9 | J1 = unsure, or its quote is not in the error text | NEEDS REVIEW | Spec rule |

**Exceptions.** None in the PDF for 5.F. A message that names the field by its value ("abc is not a number") identifies it when the form has one such field; J1 judges that.

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; P1 incomplete before the last field; more forms than `FORM_MAX`; an attempt cut by the run limit; the page could not be read before an attempt (1.1.0); more than 200 new pieces of text appeared after one action, or the list from the fresh load was lost, so new text may not all have been read (1.1.0); or an attempt sent its form (A4) | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | Both attempts ran for every form (attempt 2 only for a form with a text or date field: with none there is nothing to make wrong, 1.1.0), at least one instance, every instance PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

**Plain-language sentences.** `<field>` is the field's label and kind in plain words; `<keys>` reproduces the attempt from a fresh load.

| Row | Sentence |
| --- | --- |
| Page PASS | "We left required fields empty and typed letters into fields that expect a format and dates outside the allowed range into date fields, then tried to send the form. Each error the page found was named and explained in text." |
| Page FAIL | "Some form errors are not named or explained in text, so a person may not know which field is wrong or why." |
| Page NEEDS REVIEW | "We could not finish this test, so a person needs to check it." |
| A3 | "We left required fields empty and typed letters into fields that expect a format and dates outside the allowed range into date fields, then tried to send the form, and the page did not check for errors, so this test does not apply." |
| A4 | "The form was sent to its server, and our copy of the page cannot show what the server answers. Please submit it with mistakes on the live site and check the error messages." |
| M2 (note) | "The browser's own message points to <field> and explains the error; that is fine." |
| M3 | "When <field> was wrong, the page only marked it (<how>), with no text saying what is wrong. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M7 | "The page shows an error for <field> (\"<quote>\"), but nothing announces it: it is not read out, and focus does not move to it, so a screen reader user may not know it appeared. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M8 | "The error message \"<text>\" does not say <which field is wrong / what is wrong with <field>>. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M9, M5 | "An error appeared for <field>, and we could not tell whether its message names the field and explains the problem. Please look: load the page and press <keys>." |

## 4. Judgment questions

The calling agent answers each once, by the rubric; a person's answer overrides it. Page text is evidence in `input`, never in a question's wording. J1 is a question a careful tester settles by reading (CLAUDE.md principle 8, as 5.D J1): its answer can lead to PASS only with both quotes found in the error text, and the agent answers unsure whenever the text does not settle it.

### J0. Which control sends the form?

**Question:** "Pressing the control named in input.pressed showed no error and did not send the form. Which of the controls in input.controls would a person press to send this form or go on to the next step? Answer with its number, none or unsure."

**Input:** `pressed`; `controls`: each button of the form (number, name, kind), labelled as untrusted page data.

**Output:** `{choice: <n>|none|unsure, reasons}`.

**Rubric.** The control whose name says it sends, submits or goes on ("Continue", "Submit application"); none when no control sends the form (a calculator, a filter); unsure otherwise. Never the control already pressed, nor one that saves a draft, goes back, cancels or deletes.

**Use:** section 2 (Submit control): a number not pressed yet gets both attempts. Its answer never decides an outcome by itself: the attempts' evidence does.

### J1. Does the error text name the field and say what is wrong?

One question per candidate field (section 3).

**Question:** "We made the field in input.field wrong as described in input.done and then did input.action. The text in input.errors appeared. Does that text say that this field is in error, and what is wrong with it? Answer described, not_identified, not_described, no_error or unsure. For described, put in quote the exact words that name the field and say what is wrong (copied from one entry of input.errors)."

**Input:** `field`: label, kind, type; `done` (left as loaded, or the value typed); `action` in plain words; `errors`: each new text with where it appeared (in a dialog, in a browser alert box, in an area that is read out when it changes, tied to a field as its description, on the page), labelled as untrusted page data; images before and after.

**Output:** `{choice: described|not_identified|not_described|no_error|unsure, quote, reasons}`.

**Rubric.** described: the text names the field (its label, an unambiguous reference such as its value, it is tied to the field as its description, or the form has only this one field) and says what is wrong ("is required", "must be a number", "abc is not a number"; saying the value is incorrect or invalid is enough, as the PDF's own example "the Password you entered is incorrect", p. 28 HtT 3.b: what to enter instead is 5.G). not_identified: an error is shown but nothing says which of several fields it is about ("Error.", "Please fix the errors below" with no field named). not_described: the field is named but not what is wrong ("Error: Password field" alone, p. 28 HtT 3.b). no_error: nothing in the text is about this field (it accepted the value). unsure: whenever the text does not settle it. Mechanical check: the quote must appear in one of the error texts (whitespace and case aside).

| Example | Answer |
| --- | --- |
| One field "Enter A Number", text "Error: abc is not a number." | described |
| Two fields, text "Error." | not_identified for the field in error |
| "Email: please enter a valid email address" tied to Email | described |
| A name field given "abc", and only the ZIP code's error shown | no_error for the name field |

**Use:** M6–M9; `no_error` makes no instance.

### J2. Does the field's look mark an error?

**Question:** "Image A shows the field named in input.field before; image B shows it after it was given the value in input.value and focus moved away. Does its new look mark it as being in error? Answer error, not_error or unsure."

**Input:** clipped images of the field before and after; its label; the colors read.

**Output:** `{choice: error|not_error|unsure, reasons}`.

**Rubric.** error: a red or warning-colored border, background or icon. not_error: a green or neutral look (valid, filled). unsure otherwise.

**Use:** M3–M5.

## 5. Edge cases

V-numbers are browser checks in [5f-build-tasks.md](5f-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| TC10.D-2-fail-1: "Error: not a number." at the top, no live region, no focus move; cleared by the next key press | M7 FAIL; text seen after the Tab counts | V1 |
| TC10.D-2-fail-2: only the field's background turns red | M3 (J2 = error), FAIL | — |
| TC10.D-2-fail-3: two fields, "Error." in a live region | J1 not_identified, M8 FAIL | — |
| TC10.D-all-pass-1: `alert("Error: abc is not a number.")` on the button, focus back to the field | J1 described, notice by JS dialog, M6 PASS | V2 |
| TC10.D-all-pass-2: "Error: not a number." in an `aria-live=assertive` region | M6 PASS (one field, so "not a number" identifies it; J1) | — |
| TC10.D-all-pass-3: focus moved to the message | M6 PASS | — |
| TC10.D-ic-dna-1: the button does nothing | A3 DOES NOT APPLY | — |
| Native validation (`required`, `type=email`) | M2 PASS; the message is the browser's, read as `validationMessage` (headless Chrome draws no bubble to screenshot) | V3 |
| The page cancels the `invalid` event and only sets `aria-invalid` (custom error display with no text) | Not M2: the browser shows nothing. M3 FAIL (fixture f15; 1.1.0) | — |
| A form with no button (one text field) | Both attempts press Enter in the field (fixture f16; 1.1.0) | — |
| A long page (1,200 paragraphs) with its form in the footer | Only text new after each action is read, so the error is found (fixture f17; 1.1.0) | — |
| A server-side form (the submission leaves the page) | A4 NEEDS REVIEW | — |
| Errors only after a page reload by the server | A4 (the reload never comes from the recording) | — |
| A field the page fixes itself (clamps a number) | J1 judges any message; with none, the field has no indicator and no instance (Understanding 3.3.1 note: the change must still be described, so a person checks; a note) | — |
| CAPTCHA, payment and password-strength meters | Read like any field; no special case | — |
| Errors from a field's own widget while typing (before Tab) | Read after the Tab, as the Baseline's "shifting focus away" | — |

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5: the matching row (evidence trace only); location (page URL, frame chain, CSS path, label and kind of the field); what was done (empty, or the value typed; the control pressed); the error text and where it appeared, or the look change with images before and after; the J1 or J2 answer; steps to reproduce from a fresh load ("Tab 3 times, type abc, Tab, Enter"); tool versions.

**Continuing past a failure.** Every form's two attempts run; each failing field is its own instance.
