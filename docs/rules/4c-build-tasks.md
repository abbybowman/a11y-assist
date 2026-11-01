# Build tasks: 4.C

Work [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) (spec 1.5.0) needs done during the build. Delete each row once it exists in the repo: ACT fixtures under `tests/fixtures/act/`, custom fixtures under `tests/fixtures/4c/`, browser checks under `tests/browser/`. Delete this file when every table is empty.

## Fixtures to build

**ACT test cases come first.** W3C publishes every ACT test case in [testcases.json](https://www.w3.org/WAI/content-assets/wcag-act-rules/testcases.json), and DHS published its TT 5.1 results on them as [EARL JSON](https://raw.githubusercontent.com/Section508Coordinators/act-tt/main/act-trusted-tester.json). Rules a1b64e, ebe86a and 80af7b share 19 distinct cases; DHS scored 17 (not d26e3cbd or dcf917e0). Join DHS results on the testcase hash, not the URL: DHS filed some cases under a different rule's folder. None of these rules is approved by W3C (all are proposed), so scores are reported with that label rather than dropped. A custom fixture is built only for a rule no ACT case exercises. Expected outcomes live in a manifest outside the served pages, never in a page.

**ACT cases (rules a1b64e, ebe86a, 80af7b).** IDs are the first 8 characters of `testcaseId`; the hash changes when W3C edits a case, so the manifest pins the full hash.

| ID | ACT example | ACT expected | DHS TT 5.1 | 4.C expected | Proves |
| --- | --- | --- | --- | --- | --- |
| 96eb4b26 | a1b64e Passed 1: link and button | passed | PASS | PASS | G4 wrap |
| d26e3cbd | a1b64e Passed 2: div role=button tabindex=1 | passed | not scored | PASS | Positive tabindex |
| fb76f71a | 80af7b Passed 2: div tabindex=1 | passed | PASS | PASS | Positive tabindex |
| 4b93a866 | a1b64e Passed 3: div tabindex=-1 only | passed | PASS | DNA | A1; OPEN O4 mismatch |
| dcf917e0 | a1b64e Passed 4: aria-modal dialog with focus sentinels; Escape or Close dismisses | passed | not scored | PASS | M3, modal exception |
| f5ea9fd3 | a1b64e Failed 1: button refocuses itself on blur | failed | FAIL | FAIL | M11, settle focus check |
| d2f5325f | a1b64e Failed 2 = 80af7b Passed 7: two buttons pass focus back and forth | split | FAIL | FAIL | M12 loop in both directions (V15) |
| 0ec0e93e | a1b64e Failed 3: two self-refocusing buttons around a third | failed | FAIL | FAIL | M11; V15 |
| 16dddd8a | Inapplicable 1: heading only | inapplicable | DNA | DNA | A1 |
| 6e3dcc2f | Inapplicable 2: disabled button | inapplicable | DNA | DNA | A1, disabled excluded |
| 9d47dcc6 | Inapplicable 3: display:none button | inapplicable | DNA | DNA | A1, not rendered |
| 30ffb299 | Inapplicable 4: visibility:hidden link and button | inapplicable | DNA | DNA | A1, visibility:hidden excluded |
| ab24c77e | ebe86a Passed 1: 2-button trap; "Press Ctrl+M to Exit" before it; key works | passed | PASS | PASS | J1, M6 |
| e3902f01 | ebe86a Passed 2: same, text inside the trap | passed | PASS | PASS | J1, M6 |
| b92b5214 | ebe86a Passed 3: help link reveals the exit key in place | passed | PASS | PASS | J1 revealed text, M6 |
| 7dcc4ae0 | ebe86a Failed 1: 2-button trap, no instructions | failed | FAIL | FAIL | M12 |
| 8fba3918 | ebe86a Failed 2: "Go to the next element" only | failed | FAIL | FAIL | J1 rubric, M12 |
| 62fd24e7 | ebe86a Failed 3: documented key doesn't work | failed | FAIL | FAIL | M7, M12 |
| b20beca9 | ebe86a Inapplicable 1: no trap | inapplicable | PASS | PASS | G4 |

**Custom fixtures (gaps no ACT case covers)** live in `tests/fixtures/4c/`; expectations are in `tests/test_fixtures_4c.py`. Retired in 1.5.0: F01, F02, F07, F08 and the old F35 (ACT cases cover them), F28 (P5 removed). F06 stays as a traversal-test page only. Row references follow 1.5.0 numbering (M11 stuck FAIL, M12 loop FAIL, M10 whole-page cycle).

Still open:

- Remove the expected outcome from every fixture's HTML comment; expectations stay in the manifest and `tests/test_fixtures_4c.py`.
- A late-refocus fixture (button refocuses 600 ms after blur, no DOM change) once the xfail in `tests/test_traverse.py` is settled.

## Browser behavior to verify in code

Each needs a small test in headed Chrome on Windows through Playwright before the rule that depends on it ships. V1–V13 pass on Linux (headless and headed under Xvfb) in `tests/browser/test_v_checks.py`; Windows is still to run.

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
| V9 | Whether elements inside a tabindex=-1 iframe are in the Tab sequence | Inventory, F33 |
| V10 | What the frozen-page replay does with scroll-triggered requests it never recorded | Recording, infinite scroll rule, F29 |
| V11 | Whether Chrome consumes Escape (stop loading, exit fullscreen) before the page sees it | M3 |
| V12 | Tab sent by Playwright moves focus the same way in headed Chrome as the plan's headless sandbox showed | All passes |
| V13 | Arrow keys on a native select on Windows: change value without opening, and fire change events | P4 |
| V14 | Recording focus and blur events with targets and times across frames and shadow roots, injected before page scripts run. Top-frame log tested (`tests/test_traverse.py`); frames and shadow roots still to test | Settle rule, F35 |
| V15 | Whether script focus() pulls keyboard focus back from the browser UI (toolbar) in headed Chrome. Linux test passes: it does, so d2f5325f cycles both ways | OUT detection, d2f5325f, 0ec0e93e |
