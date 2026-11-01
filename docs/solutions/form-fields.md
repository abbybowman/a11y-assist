# Form fields: completing them and seeing what changes

Lessons from building 5.D (On input). The next form tests (5.F, 5.G, 5.A
and 5.C leftovers) can reuse its pieces: `checks/t5d.py`'s `FIELD_FN`
(label, kind, value, own widget, the text before the field), `SIG_FN` (what
is visible outside the field), `_arrive` and `_fill`.

**Read the vendored cases before writing rules.** The five Baseline
Alignment TC10.C pages changed the draft spec twice: TC10.C-3-fail-2 opens
a window only when focus leaves the *last* radio option, so one ArrowDown
would have given a false PASS (now every option of a group is chosen);
TC10.C-3-fail-3 moves focus when the select changes, so completing and
leaving are observed separately. TC10.C-3-fail-1 never submits: it replaces
the form with "Form Submitted" on blur.

**One control kind per stop.** `stop.control` (text, select, listbox,
checkbox, switch, radio, combobox, slider, spinbutton, date) is computed
once by the walk; 4.C's J2 (a section that needs input) and 5.D both read
it. Read-only and disabled stops carry flags and are not fields; a field
"revealed" by a change is one that was not a P1 stop at all.

**Chrome focuses a date input's parts one by one** (month, day, year, then
the picker button), inside the input's own shadow root, each with role
spinbutton. Treated as separate stops they looked like focus jumping on its
own. Stops inside a date or time input are now control "date" with the
input as their `group`; reads go to the host input (`_on_host`), typing
digits fills the parts in order, and the value reads back in ISO form
(`2026-01-15`), so compare emptiness, not the typed string. Leaving means
Tab until focus is off the field's own widget.

**Where the page changed.** The mutation log only counts. To tell "only
the field's own widget changed" (an autocomplete list, its error message,
a radio group's other buttons, anything it names in `aria-controls`,
`aria-owns`, `list`, `aria-describedby` or `aria-errormessage`) from a
change elsewhere, 5.D compares a signature of the visible text and dialogs
outside the own widget before and after.

**Submissions.** `form.submit()` fires no `submit` event, so the init script
wraps `submit()` and `requestSubmit()` as well as listening for the event
(`traverse.submissions`). The log lives on the page: a submission that
navigates away loses it, and the change then reads as navigation (both are
M4 in 5.D). Submission tracking is opt-in in `observe(submits=True)`, so 4.A
and 4.B evidence did not change.

**Keys pressed outside `Traversal.press`:** call `traversal.resync()`
before the next `press`, or it waits the settle rule's 1 s re-read
(docs/solutions/time-budget.md).

**Draft checks stay out of the registry.** A 0.y.z spec gives no outcome,
so `checks/t5d.py` lived in `tests/drafts.py` (registered per test, and by
`evals/judge_eval.py` and `evals/time_budget.py --drafts`) until 1.0.0.
