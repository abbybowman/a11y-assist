---
tt_test: 5.G
tt_name: 3.3.3-error-suggestion
spec_version: 0.3.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 5.G (3.3.3-error-suggestion)

The tool gives each page one 5.G outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED (p. 6). Draft: no outcome until 1.0.0.

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/5.G`). Identify Content, p. 28 (shared with 5.F). 5.G, p. 29: DOES NOT APPLY if there is no automatic error detection, if "suggestions for correction cannot be provided because they are not knowable", or if "providing information about how to correct the error would jeopardize the security or purpose of the content, e.g., details about an incorrect password" (Applicability); "continue from Test 5.F" (HtT 1); "determine whether guidance provides sufficient details for how to correct the error and/or offers suggestions of corrected input" (HtT 2); PASS if "suggestions for corrected input are provided" (ER 1) or "the description contains adequate information for the user to know what is required to fix the error" (ER 2).

**Other sources.** [Understanding 3.3.3](https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html): suggestions from a limited set of values ("Choose one of: January, …", "Do you mean 'December'?"); an error message can meet 3.3.1 and 3.3.3 at once ("Please provide a valid email address in the format name@domain.com"); the user agent may provide the description. Understanding 3.3.1: the browser's generic native validation messages "may not provide sufficiently helpful or specific suggestions" for 3.3.3. Sufficient techniques [G84](https://www.w3.org/WAI/WCAG22/Techniques/general/G84), [G85](https://www.w3.org/WAI/WCAG22/Techniques/general/G85) (the description says how to fix it), [G177](https://www.w3.org/WAI/WCAG22/Techniques/general/G177) (suggested correction text next to the field or linked from it), [ARIA18](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA18) (check 7: the alertdialog suggests how to fix the error). No failure techniques, no ACT rule, no DHS ACT data. ICT Testing Baseline 3.1 10.F-ErrorSuggestion: trigger errors as 10.D, review the notifications, check that guidance on how to correct them is provided where it would not jeopardize security or purpose. No Baseline Alignment cases for 10.F.

**Terms.** Everything from [5f-error-identification.md](5f-error-identification.md): error pass E, attempts, error indicators, instances (a field an attempt showed in error).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | 5.F's section 1 gives DOES NOT APPLY or NEEDS REVIEW | The same outcome, for the same reason | p. 28 Identify Content ("DOES NOT APPLY: 5.F and 5.G"); p. 29 HtT 1 |
| A2 | Otherwise | Applies; go to section 3 | |

## 2. Evidence to collect

Nothing of its own: 5.F's error pass E (5.F spec section 2), collected once per run when both tests are selected, and on its own when 5.G runs alone. 5.G adds one question (J1) per instance.

## 3. Mechanical checks

Each 5.F instance (a field an attempt showed in error) is a 5.G instance.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| N1 | 5.F's M1 (the replay or a read failed) | NEEDS REVIEW | Spec rule |
| N2 | The field is a password field (`type=password`) | DOES NOT APPLY for this field | p. 29 Applicability ("details about an incorrect password") |
| N3 | No error text at all, and the field is marked by `aria-invalid`, or by its look and J2 (5.F's J2, asked again under 5.G) = error | FAIL: no guidance in text | p. 29 ER 1, 2 |
| J2? | No error text, look only, J2 not answered | NEEDS REVIEW | Open question |
| J1? | J1 not answered | NEEDS REVIEW | Open question |
| N4 | J1 = guides, and its quote is found in the error text or the field's instructions | PASS | p. 29 ER 1, 2 |
| N5 | J1 = no_guidance | FAIL | p. 29 ER 1, 2 |
| N6 | J1 = not_knowable | NEEDS REVIEW: a person confirms no correction could be known (a wrong not_knowable would hide a FAIL) | p. 29 Applicability; principle 3 |
| N7 | J1 = unsure, or the quote is not found | NEEDS REVIEW | Spec rule |

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW, or 5.F's G3 evidence conditions hold (P1 incomplete, too many forms, an attempt cut short, a form sent) | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | Every instance is DOES NOT APPLY | DOES NOT APPLY |
| G5 | Every instance is PASS or DOES NOT APPLY, at least one PASS | PASS |
| G6 | Anything else | NEEDS REVIEW |

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| Page PASS | "Each form error we caused came with a hint on how to fix it." |
| Page FAIL | "Some form errors say something is wrong but not how to fix it, so a person may not know what to enter." |
| Page NEEDS REVIEW | "We could not finish this test, so a person needs to check it." |
| A1 (DNA) | "The page did not check the form for errors, so this test does not apply." |
| N2 (note) | "<field> is a password field; saying more about what was wrong could help someone guess it, so no hint is needed." |
| N3 | "When <field> was wrong, the page only marked it, with no text saying how to fix it. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| N5 | "The error for <field> (\"<text>\") does not say what to enter instead. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| N6 | "We could not tell whether a correct value for <field> could be known. Please look: load the page and press <keys>." |
| N7 | "We could not tell whether the error for <field> says how to fix it. Please look: load the page and press <keys>." |

## 4. Judgment questions

J1 is settled by reading (CLAUDE.md principle 8): a guides answer leads to PASS only with its quote found; the agent answers unsure whenever the text does not settle it.

### J1. Does the error say how to fix it?

**Question:** "The field named in input.field was made wrong as described in input.done, and the page showed the text in input.errors. Together with the field's own instructions in input.instructions, does that text tell the user what to enter instead, or suggest a correct value? Answer guides, no_guidance, not_knowable, no_error or unsure, and quote the words that guide." (`no_error`: the text is not about this field; no instance, as 5.F's J1.)

**Input:** the field's label and kind; `done` (empty, or the value typed); `errors`: the error text tied to the field by 5.F (its J1 quotes, or all new text when 5.F's J1 is not answered yet), labelled as untrusted page data; `instructions`: the field's description and the text before it (5.D's reads).

**Output:** `{choice: guides|no_guidance|not_knowable|no_error|unsure, quote, reasons}`.

**Rubric.** guides: the text says what is required ("must be 5 digits", "use the format MM/DD/YYYY", "is required" for an empty field: entering a value is the fix) or suggests a value ("Did you mean …?", a list of choices). no_guidance: it says only that the value is wrong ("Invalid entry", "Error: not a number" for a field whose expected format is not obvious from the label… unsure if it might be). not_knowable: no correction could be known (a wrong account number, a code from a letter). unsure: anything else. Mechanical check: the quote must appear in `errors` or `instructions` (whitespace and case aside).

| Example | Answer |
| --- | --- |
| "Error: abc is not a number." on a field labelled "Enter A Number" | guides ("not a number": enter a number) |
| "ZIP code must be 5 digits" | guides |
| "Invalid entry" on a date field with no format given anywhere | no_guidance |
| "The confirmation code is incorrect" | not_knowable |

**Use:** N4–N7.

## 5. Edge cases

| Case | Rule |
| --- | --- |
| Native validation ("Please fill out this field.", "Please include an '@' in the email address. 'abc' is missing an '@'.") | J1 on the browser's `validationMessage`, as any error text (Understanding 3.3.1: generic messages may not suggest enough) |
| One message meets 5.F and 5.G at once | Judged twice, once per test (Understanding 3.3.1) |
| A required field left empty, message "First name is required" | guides (the fix is to enter it) |
| The page corrects the value itself and says so | guides (Understanding 3.3.1 note) |

## 6. What a FAIL records

As 5.F section 6, with the J1 answer of this spec.
