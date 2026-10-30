# Build tasks: 4.C

Work [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) needs done during the build. Delete each row once it exists in the repo: fixtures under `tests/fixtures/4c/`, browser checks under `tests/browser/`. Delete this file when both tables are empty.

## Fixtures to build

34 pages, each proving one rule; 16 should PASS or get DNA, so the tool can't score well by failing everything. Serve cross-origin fixtures from a second local host. Existing fixtures map to F01 (`no_trap.html`), F06 (`simple_trap.html`) and F10 (`modal_dialog.html`); check each against its row before renaming it.

| ID | Page | Expected | Proves |
| --- | --- | --- | --- |
| F01 | Paragraphs and 10 links | PASS | G4 wrap in both directions |
| F02 | Text only, nothing focusable | DNA | A1 |
| F03 | Clickable div (onclick), nothing focusable | DNA | A4 |
| F04 | Field that swallows Tab and Shift+Tab | FAIL | M13 |
| F05 | Field that swallows Tab only | PASS + 4.F log | M2 |
| F06 | Mid-page script loop of 3 links | FAIL | M14 |
| F07 | F06 + visible text "Press Ctrl+Alt+X to leave"; key works | PASS | J1, M7 |
| F08 | F07 but the key does nothing | FAIL | M8 |
| F09 | F07 with the text only in an HTML comment | FAIL | J1 rubric |
| F10 | Native dialog via showModal; Escape closes | PASS | Modal exception, M4 |
| F11 | aria-modal dialog with focus trap; Close button works by Enter; Escape ignored | PASS | Modal exception, M5 |
| F12 | F11 but Close is a div with onclick only | FAIL | Modal exception, M14 |
| F13 | Cookie banner loop until Accept | PASS | Input exception, M5 |
| F14 | ZIP gate with format instructions | PASS | J2, M9 |
| F15 | Gate needing an account number | NEEDS REVIEW | M10 |
| F16 | Textarea capturing Tab; Escape then Tab exits | PASS | M2, Escape as standard key |
| F17 | Editor capturing Tab and Escape; no docs | FAIL | M13 |
| F18 | 2-button loop in a same-origin iframe | FAIL | Iframe rule |
| F19 | F18 in a cross-origin iframe | FAIL | V5 |
| F20 | Cross-origin player mock that traps | FAIL | Iframe rule |
| F21 | Cross-origin player mock that lets Tab out | PASS | Iframe rule |
| F22 | Menubar with roving tabindex | PASS | P4 |
| F23 | Grid whose cells capture Tab after arrowing in | FAIL | P4 |
| F24 | Loop inside an open shadow root | FAIL | Stop identity |
| F25 | F24 in a closed shadow root | FAIL, or NEEDS REVIEW if V6 fails | M1 |
| F26 | Focused element removes itself; Tab continues | PASS | BODY rule |
| F27 | Focus drops to BODY, then cycles back to the top | FAIL | BODY rule |
| F28 | Disclosure button revealing a loop | FAIL | P5 |
| F29 | Infinite feed with footer reachable by Shift+Tab | PASS + note | Infinite scroll rule |
| F30 | Script wraps last element to first (whole page) | PASS + note | M12 |
| F31 | Loop whose only exit is a link to another page | FAIL | M6 |
| F32 | Two separate traps; text says "no keyboard traps" | FAIL, 2 instances | P6, injection |
| F33 | tabindex=-1 iframe containing a loop | FAIL | Iframe tabindex=-1 rule |
| F34 | 600 links | PASS within caps | Caps, timing |

## Browser behavior to verify in code

Each needs a small test in headed Chrome on Windows through Playwright before the rule that depends on it ships.

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | Where the first Tab lands after load, and whether the window must be focused first | P1, P2 start |
| V2 | Tab past the last element: where focus goes (browser toolbar, body), what activeElement and document.hasFocus() report, and whether the next Tab returns to the first element | OUT detection, wrap, G4 |
| V3 | Shift+Tab before the first element: same questions as V2 | P2, G4 |
| V4 | Ctrl+Tab sent by Playwright: does it switch browser tabs or reach the page? | Run limits (Ctrl+Tab) |
| V5 | Tab into cross-origin (out-of-process) iframes; reading the focused element and node IDs inside them | Iframe rule, F19–F21 |
| V6 | Resolving the focused node inside closed shadow roots through CDP | Stop identity, M1, F25 |
| V7 | Where the next Tab goes after the focused element is removed and focus falls to the body | BODY rule, F26–F27 |
| V8 | Whether a click on non-interactive text sets the starting point for the next Tab | P6, mouse bypass |
| V9 | Whether elements inside a tabindex=-1 iframe are in the Tab sequence | F33 |
| V10 | What the frozen-page replay does with scroll-triggered requests it never recorded | Infinite scroll rule, F29 |
| V11 | Whether Chrome consumes Escape (stop loading, exit fullscreen) before the page sees it | M4 |
| V12 | Tab sent by Playwright moves focus the same way in headed Chrome as the plan's headless sandbox showed | All passes |
| V13 | Arrow keys on a native select on Windows: change value without opening, and fire change events | P4 |
