# Build tasks: 4.D

Spec [4d-focus-visible.md](4d-focus-visible.md) 1.2.0 is built (`checks/t4d.py`, `tests/test_fixtures_4d.py`: the 7 approved ACT oj04fd cases, all matching DHS, and 14 custom fixtures; 1.2.0's moved-element rule has a unit test on recorded evidence, since a layout shift between a measure and a picture is hard to time on a fixture). Left to do:

- Post-round 1 fix 11, second cause: an element whose focus style draws an outline or shadow that the pictures do not show where it is (NASA's card titles, a video player's controls). Record the changed styles' on and off values first (plan 2026-11-04, fix 11).

- Share one replay per widget between widget pass W and 4.C's P4.
- Rerun 4.C pages f19 (cross-origin frame), f24 (open shadow root) and f32 (two traps) for 4.D.

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V4 | Whether Chrome makes a frame or iframe element itself a Tab stop (F08 passes, but through which row is not asserted) | M2 |
| V5 | A top-level clip over a cross-origin iframe shows the frame's content, and the walk's box matches it | Frame edge case |
| V6 | Off images by page coordinates when Chrome scrolled between steps; regions larger than the viewport | Section 2, M4 |
| V8 | Cost per stop on Windows headed Chrome; a 100-stop page within the budget together with 4.C | Time budget |
| V11 | Headed Chrome on Windows: ACT cases and F01–F14 give the same outcomes | All rows |
