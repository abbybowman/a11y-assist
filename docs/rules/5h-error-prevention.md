---
tt_test: 5.H
tt_name: 3.3.4-error-prevention
spec_version: 0.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 5.H (3.3.4-error-prevention)

The tool gives each page one 5.H outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED (p. 6).

**Citations.** Printed pages 30–31 of TT 5.1.3 (text also in `tt://5.1.3/tests/5.H`). Identify Content, p. 30: "multi-page forms" that result in legal commitments or financial transactions, modify or delete user-controllable data in a data storage system, or submit user test responses; none: DNA. Applicability: DNA "if the form is only on one page OR does not do any of the following upon submission" (legal or financial obligations; modify or delete user-controlled data; submit test responses). HtT 1: "Complete the required form fields with intentional errors and submit the content." ER (any): the user can reverse the submission (1); is presented with an option to review, confirm and correct before finalizing (2); the page checks data for input errors and allows correction (3). Notes: "Because the user can review a one-page form before pressing the submit button on the page, another review mechanism is not required"; user-controllable data per Understanding 3.3.4 (mass loss such as deleting a record; not each save).

**Other sources.** [Understanding 3.3.4](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html): legal commitments are "transactions where the person incurs a legally binding obligation or benefit" (marriage license, stock trade, will, loan, contract); input errors include information "omitted by the user" or outside "the required data format or values"; examples: an order summary to inspect and confirm or change; a stock sale alert with cancel or confirm. [G98](https://www.w3.org/WAI/WCAG22/Techniques/general/G98) (review and confirm; return to previous steps; a summary before committing), [G99](https://www.w3.org/WAI/WCAG22/Techniques/general/G99) (deleted data can be recovered), [G164](https://www.w3.org/WAI/WCAG22/Techniques/general/G164) (a stated period to cancel or change an order). No ACT rule; no DHS data. ICT Testing Baseline 3.1 10.G-ErrorPrevention: "Complete the form components necessary to submit. Include errors"; at least one of reversible, checked, confirmed; advisory: a simple one-page form needs no other review. Baseline Alignment TC10.G (six one-page scripted order forms): Baseline expects PASS or FAIL on them; the TT makes a one-page form DNA, and the TT governs (Abby, 2026-11-02), so ours are DNA except where the page itself shows a step (TC10.G-2.c: "Add to Cart" shows a cart to review before "Submit Payment").

**Terms.** *Error pass E*: [5f-error-identification.md](5f-error-identification.md) section 2 (HtT 1 exactly: attempt 1 presses the submit control as loaded, attempt 2 with wrong values; reads before and after). 5.H reads it from the run cache; it presses nothing of its own. A *consequence hint*: the tested page's text, a form's button names or field labels contain pay, payment, purchase, order, checkout, cart, buy, donate, transfer, credit card, card number, agree, terms, sign and submit, delete, remove, exam, quiz, test answers, legal, contract, or application. A form *shows a step* when submitting it shows another stage before the end (a summary or review with a further submit control, "Step 2 of 3", a "Next" or "Continue" control), or the page says it is one step of several. *Checked*: an attempt of pass E was not sent and the page showed an error (new error text, a JS alert, or native validation messages).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | Pass E found no form with a submit control | DOES NOT APPLY | p. 30 Identify Content |
| A2 | Pass E did not run or could not read the forms | NEEDS REVIEW | Spec rule |
| A3 | No consequence hint | DOES NOT APPLY, with a note naming what was looked for | p. 30 Applicability (Spec rule: no sign of legal, financial, data or test consequences) |
| J1? | A hint, J1 not answered | NEEDS REVIEW | Open question |
| A4 | J1 = not_consequential or one_page | DOES NOT APPLY | p. 30 Applicability (Abby, 2026-11-02: the TT governs over Baseline TC10.G) |
| A5 | J1 = unsure | NEEDS REVIEW | Spec rule |
| A6 | J1 = multi_step | Applies; go to section 3 | |

## 2. Evidence to collect

Nothing of its own: error pass E (5.F; cached; run by 5.H if 5.F is not selected). For J1 and J2: the page's visible text (first 60 strings), each form's fields and buttons, and per attempt what appeared after submitting (new text, alerts, whether it was sent, where focus went), with pass E's before and after images.

**Time budget:** none beyond pass E.

## 3. Mechanical checks

The instance is the form J1 named (or every hinted form).

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | Checked | PASS | p. 31 ER 3 |
| J2? | J2 not answered | NEEDS REVIEW | Open question |
| M2 | J2 = review_step or reversible | PASS | p. 31 ER 1, 2 |
| M3 | J2 = none | FAIL | p. 31 ER |
| M4 | Anything else (J2 unsure, the page left on submit and nothing could be seen) | NEEDS REVIEW | Spec rule |

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL |
| G3 | Any instance is NEEDS REVIEW | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | Every instance is PASS | PASS |

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| A1 | "This page has no form to submit, so this test does not apply." |
| A3 | "No form on this page looks like it makes a payment, a legal agreement, a change to saved data or a test submission, so this test does not apply." |
| A4 | "This form either has no such consequences or is completed on one page, where people can review it before submitting, so this test does not apply." |
| M1 | "The form checks what was entered and lets people fix mistakes before it is sent." |
| M2 | "People can review and change their answers before the final submission (or undo it afterwards)." |
| M3 | "After submitting, the form neither lets people review their answers first, nor undo the submission, nor checks for mistakes." |

## 4. Judgment questions

J1 and J2 are settled by looking (CLAUDE.md principle 8); the agent answers unsure whenever the evidence does not settle it.

### J1. Does this form have consequences, and is it more than one step?

**Question:** "input.page_text is the page's text; input.forms lists its forms with their fields and buttons and what appeared after the tool submitted each one with wrong or empty values (after_submit). Does a form make a payment or purchase, create a legal agreement, change or delete saved account data, or submit test answers? If so, does completing it take more than one step (a review or summary stage, 'Step 1 of 3', a Next or Continue button), or is it all on one page and sent at once? Answer multi_step, one_page, not_consequential or unsure, and put the form's number in element."

**Output:** `{choice: multi_step|one_page|not_consequential|unsure, element, reasons}`.

**Rubric.** not_consequential: search, newsletter sign-up, contact or feedback forms, filters, logins. one_page: a consequential form whose submit button finishes it, with no stage in between. multi_step: a summary or review stage appears after the first button, or the page says it is one step of several. unsure: whenever the evidence does not settle it.

### J2. After submitting, can people review or undo?

Asked when J1 = multi_step and the form was not checked.

**Question:** "For form input.form, input.after_submit is what appeared after the tool submitted it. Does it show a review stage with a way to change the answers before the final submission (review_step), or a way to cancel or undo the submission afterwards, or a stated period to cancel (reversible), or neither (none)? Answer review_step, reversible, none or unsure."

**Output:** `{choice: review_step|reversible|none|unsure, reasons}`.

**Rubric.** review_step: a summary of the entries with a Change, Edit or Back control and a separate final submit. reversible: a Cancel order or Undo control, a refund or cancellation period stated on the page. none: a final confirmation only ("non-refundable", "your card has been charged"). unsure: whenever it does not settle it.

## 5. Edge cases

| Case | Rule |
| --- | --- |
| Submitting leaves the page (a server step not in the recording) | The after-submit view is empty: J2 unsure, NEEDS REVIEW (M4) |
| Checked on one attempt, not the other | M1: checked is enough (ER 3) |
| Several hinted forms | J1 names the form; the others are not tested |

## 6. What a FAIL records

The form (fields, buttons), J1 and J2 with reasons, pass E's attempts (values, what appeared, sent), images.
