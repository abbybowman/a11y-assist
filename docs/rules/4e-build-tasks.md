# Build tasks: 4.E

Work [4e-on-focus.md](4e-on-focus.md) (spec 0.1.0) needs done during the build, once Abby approves the spec. Delete each row once it exists in the repo. Delete this file when every table is empty.

## Walk changes

Uses the walk extras hook that 4.D needs (see [4d-build-tasks.md](4d-build-tasks.md)): build it once. 4.E's extras: the richer focus log (trusted flag, CSS path, `relatedTarget` containment on focus-out) and dialog visibility after each step. The focus log change helps 4.C and 4.D too.

## Fixtures to build

No ACT rule covers 3.2.1 and DHS published no 4.E results, so all pages are custom, in `tests/fixtures/4e/`. Expected outcomes live in the test file, never in a page. Existing 4.C pages are rerun for 4.E where they prove a "not an instance" rule.

| ID | Page | Expected | Proves |
| --- | --- | --- | --- |
| F01 | Link that opens a new window when it receives focus | FAIL | M5 |
| F02 | Field that navigates to another (recorded) page on focus | FAIL | M4; navigation in the frozen page (V1) |
| F03 | Field whose focus opens a help panel and moves focus into it (Understanding 3.2.1 failure example) | FAIL | M6 |
| F04 | Button with `onfocus="this.blur()"` (F55 Example 1) | FAIL | M7 |
| F05 | Listbox container (tabindex=0) that hands focus to its selected option | PASS | Focus moved into the target is not an instance |
| F06 | Menu that expands on focus; tooltip on focus | PASS | Change of content, not context |
| F07 | Page that redirects after 3 s, no focus handlers | NEEDS REVIEW (pass incomplete) | M2 control replay; note for 8.A |
| F08 | Dialog appears on focus, focus stays on the field | NEEDS REVIEW | M8 |
| 4.C f04-field-swallows-tab, ACT f5ea9fd3 | Refocus on blur / field swallowing Tab | PASS for 4.E | O2: pulled back, not an instance |
| no_trap.html | General page | PASS | G4 |

M3 (signal not reproduced) and M1 are covered by rules unit tests on recorded evidence: no page makes them happen reliably.

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | In the HAR replay, a navigation to an unrecorded URL changes `page.url` (and the NavigationGuard still blocks hosts outside the allowlist) | M4 |
| V2 | `relatedTarget` on focus-out is set for script `focus()`, for `blur()` (null) and across shadow roots and frames; and `isTrusted` is false for synthetic focus events | Section 3, M1, M6, M7 |
| V3 | A window opened by `window.open` on focus shows up in the context's page count before the step settles | M5 |
