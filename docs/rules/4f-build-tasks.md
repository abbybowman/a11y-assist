# Build tasks: 4.F

Spec [4f-focus-order-meaning.md](4f-focus-order-meaning.md) 1.0.0 is built (`checks/t4f.py`, `tests/test_fixtures_4f.py`: 15 custom fixtures; no ACT rule covers 2.4.3). Judge eval (2026-10-31): 8/8 after 1.1.0; f15's expected result changed from NEEDS REVIEW to FAIL (focus reads Step 3, 4, 1, 2; the agent was right), and `test_unsure_goes_to_a_person` keeps M9 covered. Left to do:

- Let 4.C read pass R (traps inside revealed content), as 4.C 1.5.0 anticipates.
- Rerun 4.C f32-two-traps-injection for 4.F (expected NEEDS REVIEW: the forward order past a trap is unknown).

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | Right-to-left pages: S3 mirrored (no rtl fixture yet) | S3 |
| V3 | Document order across frames and shadow roots (S2 compares only stops in the same frame; positions use the walk's top-level box, checked on no_trap.html's same-origin frame) | S2, S3 |
| V4 | The order image's badges line up with the stops on long, scrolled pages | Order image |
| V5 | Headed Chrome on Windows: F01–F15 give the same outcomes | All rows |
