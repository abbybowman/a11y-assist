# Build tasks: 4.B

Spec [4b-no-keystroke-timing.md](4b-no-keystroke-timing.md) 1.2.0 is built (`checks/t4b.py`, `tests/test_fixtures_4b.py`: 4 custom fixtures, `no_trap.html`, 2 Section 508 Baseline Alignment cases; no ACT rule covers keystroke timing). Baseline's own 4.B case (TC01.A-2-fail-1) expects FAIL; we give NEEDS REVIEW because the published page is broken in Chrome (its jQuery integrity hash is wrong, so holding Space does nothing). Left to do:

- Timing that the page does not describe in words is not found (proportionate: a tester finds it while operating; 4.A's Enter and Space presses cover custom controls).
- The timing words are English only; other languages give no matches (M1).

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | A held key in headed Chrome sends repeated keydown events (Playwright's `keyboard.down` sends one); pages that count repeats may behave differently | Timing proof |
| V2 | Headed Chrome on Windows: every fixture gives the same outcome | All rows |
