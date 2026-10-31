# Build tasks: 4.E

Spec [4e-on-focus.md](4e-on-focus.md) 1.0.0 is built (`checks/t4e.py`, `tests/test_fixtures_4e.py`). Left to do:

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V2 | `relatedTarget` and `isTrusted` on focus events across shadow roots and frames (the top frame is covered by F03 and F04) | Section 3, M1, M6, M7 |
| V4 | Headed Chrome on Windows: F01–F08 give the same outcomes | All rows |
