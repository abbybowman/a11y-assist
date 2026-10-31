# Build tasks: 4.C

Work [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) needs done during the build. Delete each row once it exists in the repo: fixtures under `tests/fixtures/4c/`, browser checks under `tests/browser/`. Delete this file when both tables are empty.

## Fixtures to build

All built: F01–F35 in `tests/fixtures/4c/`, expected outcomes in `tests/test_fixtures_4c.py`. F35 (aria-modal dialog that only Escape closes) was added to cover M4, because a native modal (F10) lets Tab leave the page.

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
