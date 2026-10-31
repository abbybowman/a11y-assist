# Build tasks: 4.A

Spec [4a-keyboard-access.md](4a-keyboard-access.md) 1.0.0 is built (`checks/t4a.py`, `tests/test_fixtures_4a.py`: 19 W3C ACT cases for akn7bn and 0ssw9k, 2 Section 508 Baseline Alignment cases, 12 custom fixtures for gaps). DHS publishes no TT results for the 2.1.1 ACT rules. Our outcomes differ from ACT's on 7 cases, by design: Chrome tabs to scroll containers (5d06e083, 5fa34d0a, 731acbc2); a page with a working link or dialog is PASS for the page where ACT's rule is inapplicable (997b49af, d7f9b0ca, c88fcaf4); a link only a mouse can reach is a FAIL (aa153f67). Left to do:

- Calibrate `HOVER_MAX`, `CLICK_MAX`, `EXECUTE_MAX` and the time budget on real government pages, together with 4.C–4.F (ROADMAP "Time budget").
- Controls inside content that opens only on click or Enter are not scanned (ER Note 1 covers them); reading 4.F's pass R would add them.

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | Hit-testing through frames: inert, hidden and 1 × 1 px frames are not pointer targets (covered by ACT 17a371c4, 033e04cc, 63cd20ec); cross-origin frames are counted as unreadable (no fixture) | Pointer scan, M16 |
| V2 | Chrome shows no title tooltip on keyboard focus (assumed from the PDF's note and Baseline's advisory; headless screenshots cannot show native tooltips) | Title check |
| V3 | Delegated click handlers (`document` listeners, React roots) are found by the cursor rule; one without a pointer cursor is missed (no fixture) | Pointer scan |
| V4 | Headed Chrome on Windows: every fixture gives the same outcome | All rows |
