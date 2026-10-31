# Build tasks: 4.D

Work [4d-focus-visible.md](4d-focus-visible.md) (spec 0.4.0) needs done during the build, once Abby approves the spec. Delete each row once it exists in the repo: ACT fixtures under `tests/fixtures/act/`, custom fixtures under `tests/fixtures/4d/`, browser checks under `tests/browser/`. Delete this file when every table is empty.

## Walk changes

The shared walk has no extras hook yet (`walk_page` takes none, and `Check` declares no evidence needs). 4.D needs one: a check declares the per-step extras it wants, the walk collects the union, and running 4.C alone collects none. The extras are the on and off images and the focus-style reads in spec section 2. 4.E and 4.F use the same hook (dialog visibility, scroll offsets, richer focus log), so build it once for all three.

## Fixtures to build

**ACT cases first.** Add `"4.D": ["oj04fd"]` to `RULES` in `tests/fixtures/act/sync_act.py`, with the expected outcomes below, and run it. Join DHS results by testcase hash. Skip the 2 unapproved oj04fd cases (8f296b7a, eb4f387b): they are near-copies of approved ones. Expected outcomes live in the manifest, never in a page.

| ID | ACT example | ACT expected | DHS TT 5.1 | 4.D expected | Proves |
| --- | --- | --- | --- | --- | --- |
| 52be6331 | Passed 1: link, default ring | passed | PASS | PASS | M6 with the default ring |
| 95cf4fdf | Passed 2: span with tabindex=0, default ring | passed | PASS | PASS | Non-interactive stops are tested |
| b44aa294 | Passed 3: script sets a border on the link's parent | passed | PASS | PASS | M6 through the parent's style |
| dd9628d8 | Passed 4: square marker before each link | passed | PASS | PASS | M6 through ::before, or J1 |
| f1c9efb4 | Failed 1: outline removed | failed | FAIL | FAIL | M8 |
| 90789ad8 | Inapplicable 1: nothing focusable | inapplicable | DNA | DNA | A1 |
| b12f1f45 | Inapplicable 2: links with tabindex=-1 only | inapplicable | DNA | DNA | A1 |

**Existing 4.C pages rerun for 4.D** (expectations in the 4.D test file):

| Page | 4.D expected | Proves |
| --- | --- | --- |
| 4.C f19-cross-origin-iframe-loop | PASS | Regions inside a cross-origin frame; off images inside a loop |
| 4.C f24-open-shadow-loop | PASS | Stops inside an open shadow root |
| 4.C f32-two-traps-injection | NEEDS REVIEW | G3 (the middle link sits between two traps); page text claiming a PASS changes nothing |
| 4.C f34-600-links | NEEDS REVIEW | Time limit, G3 reason |

**Custom pages (gaps no ACT case covers)**, in `tests/fixtures/4d/`. 10 pages; with the cases above, 15 of 21 should PASS or get DNA.

| ID | Page | Expected | Proves |
| --- | --- | --- | --- |
| F01 | Links with outline:none whose background color changes on focus | PASS | M6 on a fill change |
| F02 | Text input with outline:none and no value (caret only) | PASS | M5 |
| F03 | Off-screen skip link that appears on focus, no ring | PASS | M6, box moved |
| F04 | Visible radio buttons, outline:none; the adjacent label is highlighted on focus (C15 Example 2) | PASS | Labels in the region and style reads |
| F05 | 300 ms outline transition | PASS | V1: the image catches the finished ring |
| F06 | Autoplaying slideshow behind links with outline:none (scripted J1 answer: no) | FAIL | No style signal, so pixel noise goes to J1, never straight to PASS |
| F07 | Sticky header covers the focused link | FAIL | M8: hidden behind other content |
| F08 | Focusable iframe element with no ring; links inside with rings | PASS | M2 (no frame stop if V4 shows Chrome never makes one) |
| F09 | 1 px very light gray outline on white (scripted J1 answer: unsure) | NEEDS REVIEW | M7, M11 |
| F10 | 100 links with the default ring | PASS within budget | Time budget on a typical page (V8) |

F11: a button that calls blur() on focus (F55 Example 1), expected FAIL (M3).

## Browser behavior to verify in code

Each needs a small test in headed Chrome on Windows through Playwright before the rule that depends on it ships. "Seen on Linux" means checked once by hand on Chromium headless shell with Playwright 1.63, not yet a test in the repo.

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | A screenshot with animations disabled captures the end state of focus transitions, and a style read after it gives end-state styles (seen on Linux: a 300 ms outline-color transition read as transparent before the shot and red after it) | Section 2, F05 |
| V2 | After a Playwright Tab, Chrome's default ring is drawn and reads as computed outline-style auto (seen on Linux) | M6, every default-ring case |
| V3 | Screenshots hide the caret by default; a text field with a value shows a selection highlight when tabbed into (seen on Linux) | M5, F02 |
| V4 | Whether Chrome makes a frame or iframe element itself a Tab stop (with and without tabindex), and whether the next Tab lands inside it | M2, F08 |
| V5 | A top-level clip over a cross-origin iframe shows the frame's content, and the walk's box matches it | Frame edge case, f19 |
| V6 | Off images by page coordinates when Chrome scrolled between steps; regions larger than the viewport clip correctly | Section 2, M4 |
| V7 | Focus styles read through CDP for the stop, its parent, its labels and ::before/::after, in a way page script cannot spoof | M6 |
| V8 | Cost per stop (2 clips plus style reads) on Windows headed Chrome, and a 100-stop page within the budget together with 4.C | Time budget, F10 |
| V9 | Taking the on image fires no focus or blur events and doesn't change where focus is | Section 2 |
