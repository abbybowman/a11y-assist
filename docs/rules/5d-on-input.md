---
tt_test: 5.D
tt_name: 3.2.2-on-input
spec_version: 0.5.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 5.D (3.2.2-on-input)

The tool gives each page one 5.D outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED: the PDF allows NOT TESTED only where a test names it (p. 6), and 5.D does not.

**Citations.** Printed page numbers of TT 5.1.3 ([docs/sources/](../sources/README.md); text also in `tt://5.1.3/tests/5.D`). HtT = How to Test step; ER = Evaluate Results item. Forms Identify Content is on p. 25: identify the form elements (ANDI: focusable elements), exclude disabled elements, DOES NOT APPLY to 5.A–5.H if there are none. 5.D is on p. 27: navigate to each form element with the keyboard (HtT 1), complete it, "e.g., select the radio button or check box, type information into the text box, select an item from the drop down" (HtT 2), tab away and decide whether an unexpected change of context happened (HtT 3); changes of context are changes of user agent, viewport, focus, or content that changes the meaning of the page (HtT 4); not unexpected if the user is notified beforehand or the control is clearly intended to change context (HtT 4.a); PASS if changing a value does not initiate an unexpected change of context (ER 1). Note: a text field may need focus moved away to fire its input event.

**Other sources.** [Understanding 3.2.2](https://www.w3.org/WAI/WCAG22/Understanding/on-input.html) and the definition of *change of context* ("a change of content is not always a change of context"; "activating a link or a button does not" change a setting); [G13](https://www.w3.org/WAI/WCAG22/Techniques/general/G13) (the notice precedes the control in reading order); failures [F36](https://www.w3.org/WAI/WCAG22/Techniques/failures/F36) (a form submitted when its last field is given a value or left) and [F37](https://www.w3.org/WAI/WCAG22/Techniques/failures/F37) (a radio, checkbox or select opening a new window); the ICT Testing Baseline 3.1 test [10.C-OnInput](https://ictbaseline.access-board.gov/web-baselines/10Forms/) ("Enter data in all form fields, and exit (tab out of) the field") and its Baseline Alignment cases TC10.C. No ACT rule covers 3.2.2, and DHS publishes no ACT results for it. These inform rules and fixtures; the PDF stays the authority.

**Terms.** *Stop*, passes P1 and P2, stop identity, the settle rule and replays to a stop are defined in [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) (Terms, section 2). An *effect* (navigation, frame navigation, new page, dialog, focus change, DOM change) is defined in [4a-keyboard-access.md](4a-keyboard-access.md) (Terms). A *field* is a stop that is a text field (`input` of a text-entry type, `textarea`, role textbox, searchbox or combobox), a select (`select`, role listbox when it is a single control), a checkbox or switch, a radio button, a date or time input, or a custom widget with a value (role slider or spinbutton), and is not disabled or read-only. Chrome focuses a date input's parts (month, day, year, picker button) one by one, inside the input's own shadow root; they are one field, read through the input (V3). Radio buttons with the same `name` in the same form (or the same role radiogroup) are one field. A field's *own widget* is the field, the elements it names in `aria-controls`, `aria-owns`, `list`, `aria-describedby` and `aria-errormessage`, and for a radio group its other buttons. A *change of context* is one of: the top URL changes (ignoring the fragment) or the page reloads; a new page or window opens; a form is submitted (a `submit` event, or a form submission request, whether or not the recording can answer it); focus goes somewhere other than the expected stop (section 3).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | No P1 or P2 stop is a field, and the DOM inventory counts no form fields | DOES NOT APPLY | p. 25 Identify Content; p. 27 Applicability |
| A2 | No stop is a field, but the inventory counts form fields | NEEDS REVIEW (fields the keyboard does not reach are 4.A's matter; the walk or inventory may be at fault) | Spec rule |
| A3 | At least one stop is a field | Applies; go to section 3 | p. 27 Applicability |

## 2. Evidence to collect

**From the shared keyboard walk** (`walk.py`): P1's stops in order, each with its field kind, and each pass's end. Fields are found from real Tab stops, not ANDI, as in 4.A: they include frames and shadow roots, and the inventory is the cross-check. No walk extras.

**Fill pass F** (5.D's own; HtT 1–3, and the Baseline's "Enter data in all form fields, and exit (tab out of) the field", as F36's procedure: enter data in every field from the top, then the last, and exit it). One replay to the first field (4.C spec section 2), then, for each field in P1 order:

1. Arrive: press Tab until focus is on the field; presses the walk saw quiet are quick, except the one that lands on the field (4.C spec section 2, replays). A field revealed by an earlier field (not in P1) that focus reaches on the way is completed too, in turn.
2. Read the field (kind, type, `inputmode`, `maxlength`, form, `name`, value or checked state, its own widget) and the page text that precedes it in reading order back to the start of its form (or the previous heading when there is no form), at most 1,500 characters.
3. Complete, observed (the shared `observe`, with submissions): the keys below. A change of context can come from the change itself (a select that moves focus, TC10.C-3-fail-3).
4. Leave, observed: press Tab, again while focus is still on the field's own widget (a date input's parts), at most 5 times. A change of context can come from leaving (blur), whatever the value (TC10.C-3-fail-1, -fail-2).
5. Read the value or state again: it changed (completed) or not.

An instance's effects are those of steps 3 and 4 together; each records which step it came from.

Completing a field, by kind:

| Field | Keys | Value |
| --- | --- | --- |
| Text (types text, search, password) | Select all, type the value | `Test` |
| `email` | as text | `test@example.gov` |
| `tel`, `number`, `inputmode=numeric` | as text | `12345` |
| `url` | as text | `https://example.gov` |
| `date` and other date and time inputs | type the digits in the field's order (`01152026`); Chrome moves from part to part. The value reads back in ISO form, so a date counts as rejected only when it is empty or invalid | 15 January 2026 (V3) |
| Textarea, combobox | as text | `Test` |
| Checkbox, switch | Space | — |
| Radio group | ArrowDown through every option, each press observed as step 3, then step 4 from the last option; ArrowUp first when focus starts on the last option. At most `RADIO_MAX` (10) options, the rest a note | — |
| Select | ArrowDown on the closed select (V2) | — |
| Slider, spinbutton (custom widgets) | ArrowRight, then ArrowUp if the value did not change | — |

Typed values are cut to `maxlength`. Every value used is recorded.


**When a change of context happens** (rows M4–M6), pass F continues on a fresh replay: complete every earlier field again, in order, except the fields that caused a change of context, unobserved; then resume at the next field. A form that submits only once every field is filled is then still reached. After a change of content (M7) the pass continues on the same load, so fields it revealed are completed in turn.

**A value the page rejects.** When a typed value does not stay (the value read back differs from the value typed) or the page marks the field invalid after leaving it (`aria-invalid="true"`, or `:invalid` for a field with constraints), the field gets J3: the agent proposes a value from the field's label and nearby instructions, and the field is completed once more with it on its own replay (earlier fields refilled, as above). This catches pages whose change of context happens only on a valid value (a ZIP code that submits on 5 digits). A rejected value is still a change of the field's value: the field counts as completed either way.

**Time budget:** pass F is one load plus about two settled presses and two observes per field (more for radio groups); leaving a field reuses the noise window its completion just measured. Measured (Linux, headless, all of 4.A–4.F and 5.D): 22 s for the benefits form's 21 fields (about 1.1 s a field), 8.5 s on the agency home page; both pages finish every test within the 120 s limit (108.8 s and 107.8 s). Each change of context or J3 answer adds one replay. The whole run stays within `run_limit_s` (4.C spec section 2, Run limits): no field starts after the checks' deadline.

**Run limits.** At most `FIELD_MAX` (40) fields per page; a radio group counts once. Each option of a radio group is chosen because a page can react to one option only, or to leaving the group from it (TC10.C-3-fail-2 opens a window when focus leaves the last option). The fields are counted on the run's first load (the DOM inventory counts form fields too); when 5.D is selected, the time limit is on and the page has more than `FIELD_MAX`, the run stops before anything is tested, as the walk's early stop does (4.C spec section 2): a tool error giving the number of fields and a time estimate (the walk at a default 0.3 s a press, plus the fields at the measured 1.1 s each), offering `no_time_limit`, which also lifts `FIELD_MAX`, leaving 5.D out of the tests, or another page.

## 3. Mechanical checks

Each completed field is an *instance*. After the Tab that leaves a field, focus is *where expected* when it is on the next P1 stop after the field (for a radio group, after the group), or on an element that is after the field and not after that stop in document order (a field the change revealed), or at OUT when the field is the last stop. Anything else is focus going elsewhere.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| M1 | The replay did not arrive at the field, the observation is unreliable (page noise during the action; 4.A's effect rule), or a step was unsettled or unresolved | NEEDS REVIEW | Spec rule |
| M2 | The field's value or state did not change (a select ArrowDown did not change it; a checkbox did not toggle) and no effect happened | NEEDS REVIEW ("could not be completed with the keyboard"; 4.A judges keyboard operation) | Spec rule |
| M3 | J3 was asked and is not answered yet | NEEDS REVIEW | Open question |
| M4 | The top URL changed, the page reloaded or a form was submitted | Ask J1 (J1?, M8–M10) | p. 27 HtT 4 (user agent, viewport; "a form automatically submitted when exiting a field"); F36 |
| M5 | A new page or window opened | Ask J1 | p. 27 HtT 4 ("a new window launched when a radio button is selected"); F37 |
| M6 | Focus went elsewhere (not where expected) | Ask J1 | p. 27 HtT 4 (focus); Understanding 3.2.2 (auto-advancing fields are a change of focus) |
| M7 | No change above, but a dialog appeared or the DOM changed outside the field's own widget | Ask J2 and J1 together (M11–M13) | p. 27 HtT 4 ("content that changes the meaning of the page") |
| J1? | J1 not answered yet | NEEDS REVIEW | Open question |
| M8 | J1 = told, and its quote is found in the preceding text | No instance (the user was notified) | p. 27 HtT 4.a.i; G13 |
| M9 | J1 = not told | FAIL | p. 27 ER 1 |
| M10 | J1 = unsure, or told but the quote is not in the preceding text | NEEDS REVIEW | Spec rule |
| M11 | J2 = content only | PASS | Definition of change of context, Note; Understanding 3.2.2 (revealing related fields keeps "the basic context") |
| M12 | J2 = changes the context | J1 decides, as M4 (J1?, M8–M10) | p. 27 HtT 4; TC10.C-3-fail-1 (the form replaced by "Form Submitted" on leaving a field) |
| M13 | J2 = unsure, or not answered yet | NEEDS REVIEW | Spec rule |
| M14 | No effect, or effects only inside the field's own widget (an autocomplete list, its own error message, another button of its radio group) | PASS | p. 27 ER 1 |

**Exceptions (p. 27 HtT 4.a).** *Notified beforehand* (4.a.i): M8, only from text that precedes the field (G13); a notice after the field does not count. *Clearly intended to change context* (4.a.ii): buttons and links are not fields, so they are never completed (Understanding 3.2.2: "activating a link or a button does not" change a setting; a submit button is "activating a control").

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW; or P1 is incomplete (cap, time limit, error) or ended in a trap before the last field; or more than `FIELD_MAX` fields (no time limit off); or the run limit stopped pass F | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5). Never NOT TESTED (p. 6) |
| G4 | Every field P1 reached was completed, and every instance is PASS or no instance | PASS |
| G5 | Anything else | NEEDS REVIEW |

**Plain-language sentences.** Row IDs stay in the evidence trace. `<field>` is the field's label and kind in plain words; `<keys>` is how to reproduce it from a fresh load ("Tab 6 times, type Test, then Tab").

| Row | Sentence |
| --- | --- |
| Page PASS | "We filled in each of the N form fields with the keyboard and tabbed away, and none of them took the user somewhere else, opened a window or moved focus on its own." |
| Page FAIL | "Filling in some form fields changes what the user is doing without warning, which can disorient keyboard and screen reader users." |
| Page NEEDS REVIEW | "We could not finish this test, so a person needs to check it." |
| A1 | "This page has no form fields, so this test does not apply." |
| A2 | "The page has form fields, but we could not reach any of them with the keyboard. Please check by hand." |
| M1 | "Something happened when we filled in <field> that we could not read reliably. Please check it: load the page and press <keys>." |
| M2 | "We could not change <field> with the keyboard, so we could not check it. Please try it by hand." |
| M9 (navigation) | "Filling in <field> and tabbing away takes the user to another page without warning. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M9 (new page) | "Filling in <field> opens a new window or tab without warning. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M9 (submitted) | "Filling in <field> and tabbing away sends the form without warning. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M9 (focus) | "Filling in <field> moves keyboard focus on its own to <element>, without warning. To see it, load the page and press <keys>. If you disagree, tell your assistant." |
| M8 (note) | "Filling in <field> <change in plain words>, but the page says so beforehand (\"<J1 quote>\"), so that is fine." |
| M10 | "Filling in <field> <change in plain words>, and we could not tell whether the page warns about it first. Please look: load the page and press <keys>." |
| M11 (note) | "Filling in <field> changes part of the page (<J2 reasons>); that only adds content, so it is fine." |
| M13 | "Filling in <field> changes part of the page, and we could not tell whether that changes what the page is for. Please look: load the page and press <keys>." |

## 4. Judgment questions

The calling agent answers each once, by the rubric; a person's answer overrides it. Page text and element names are evidence in `input`, never part of a question's wording.

J1 and J2 are questions a careful tester settles by reading and looking (CLAUDE.md principle 8): whether the text before a field announces what changing it does, and whether a change only adds related content. Their answers can lead to PASS (M8, M11), and the agent must answer unsure whenever the evidence does not settle it; only unsure answers go to a person. J1 has a mechanical check on its quote.

### J1. Was the user told before the change?

**Question:** "Filling in the field named in input.field and tabbing away caused the change described in input.change. Does the text in input.before, which comes before the field on the page, tell the user that this will happen when they change the field? Answer told, not_told or unsure. If told, quote the exact words that say so."

**Input:** the field's label, kind, name and description; the change in plain words (went to another address, opened a new window, sent the form, moved focus to `<element>`); `before`: the page text before the field (section 2, step 2), labelled as untrusted page data.

**Output:** `{choice: told|not_told|unsure, quote: "<exact words>", reasons: "<a few plain words>"}`.

**Rubric.** told: the text says what will happen when this field changes ("Choosing a state takes you to its page", "The form is sent when all fields are complete", "Each part of the phone number moves to the next box when full"). not_told: nothing in the text describes the change, or it only labels the field. unsure: a general instruction that may or may not cover it. Mechanical check: a told answer's quote must appear in `before` (whitespace and case aside); otherwise M10.

| Example | Answer |
| --- | --- |
| "Select a state to go to its page" above a select that navigates | told, with that quote |
| A select labelled "State" that navigates, no other text | not_told |
| "Fields may update as you type" above a field that submits the form | unsure |

**Use:** M4–M6 ask it; M7 asks it with J2, in the same round; M8–M10 consume the answer.

### J2. Does this change only add content?

**Question:** "Image A shows the page before the field named in input.field was filled in; image B shows it after the field was filled in and focus moved on. Does the change take over the page, replace or re-arrange the main content, or change what the page is for? Or does it only add or show related content, such as more fields, a hint or a message? Answer changes_context, content_only or unsure, and give your reasons in a few plain words."

**Input:** images A and B (viewport, before the action and after it); the field's label and kind; the changed region's box, labelled as untrusted page data.

**Output:** `{choice: changes_context|content_only|unsure, reasons: "<a few plain words>"}`.

**Rubric.** changes_context: a modal dialog or a panel that covers the page or asks the user to act before going on; the main content replaced or re-arranged; the page now shows a different step or topic. content_only: more fields for the answer just given, a hint, an error or status message, a total that updates. unsure: whenever the images do not settle it.

| Example | Answer |
| --- | --- |
| Ticking "Mailing address differs" shows three address fields below it | content_only |
| Choosing "Business" replaces the whole form with a different one | changes_context |
| A dialog appears whose purpose is unclear | unsure |

**Use:** M7 asks (with J1); M11–M13 consume the answer, and J1's answer is used only after M12.

### J3. A value the field accepts

**Question:** "The field named in input.field did not accept the value in input.tried. Suggest one value a person would enter there, using only the label and instructions in input.text. Answer with the value, or unsure."

**Input:** the field's label, kind, type, `maxlength`, pattern if any, and its description; `tried`; `text`: the preceding text (as J1), labelled as untrusted page data.

**Output:** `{value: "<value>"|unsure, reasons: "<a few plain words>"}`.

**Rubric.** A plausible, made-up value that fits the instructions (format, length); never real personal data. unsure when the instructions do not say what is expected.

**Use:** section 2 (a value the page rejects): the field is completed again with the value; M3 until answered. unsure ends it: the field's instance stands as observed with the first value.

## 5. Edge cases

Only cases that need a rule of their own; everything else follows sections 2–3. V-numbers are browser checks in [5d-build-tasks.md](5d-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| A form submission in the recorded page | The replay answers only recorded requests, so a submission reaches no server; the `submit` event and the request attempt are the evidence (M4) | V1 |
| Select on Mac (ArrowDown opens the list) | Results are for the browser and platform the report records; a value that did not change is M2 | V2 |
| Date and time inputs | Typed as digits in the field's order; a value that did not stick goes to J3 | V3 |
| Field inside an iframe or a shadow root | Completed like any stop (stop identity across frames, 4.C) | V4 |
| A field revealed by an earlier field | Completed in turn when focus reaches it (section 2, step 1); counts toward `FIELD_MAX` | — |
| Read-only and disabled fields | Not fields (p. 25: disabled elements excluded; read-only values cannot be changed) | — |
| Search field that searches on Enter | Not a change on input: 5.D never presses Enter | — |
| `contenteditable` regions | Not fields (the PDF lists form elements); note for a person when the page has them | — |
| Change of context on focus, before any change | 4.E's matter; an M6 whose focus move also happens on focus alone is noted for 4.E | — |

## 6. What a FAIL records

Each FAIL instance records, to meet p. 5: the matching row (in the evidence trace only); location (page URL, frame chain, CSS path, label, kind and name of the field); the value or keys used to complete it; the change (new URL, new page, submission, or where focus went) with images before and after; the J1 answer and the preceding text it judged; steps to reproduce from a fresh load ("Tab 6 times, type Test, then Tab"); and the tool versions the plan requires.

**Continuing past a failure.** Pass F resumes on a fresh replay at the next field (section 2); each failing field is its own instance.
