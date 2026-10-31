# Element paths must be unique; positions must be top-level

**Paths.** A path built from tag names alone (`form > fieldset`) is the same
for two sibling fieldsets or eight `<details>`, so groups merged and the
wrong container was checked (4.F F02, F13). Paths now add
`:nth-of-type(n)` where a tag repeats and stop at an id (escaped with
`CSS.escape`). Stop identity across loads still uses the CDP reader's
`Stop.path_key`.

**Coordinates.** `getBoundingClientRect()` inside an iframe is relative to the
frame. Positions for comparing order (4.F) must come from the walk's
`Stop.bounding_box`, which the reader already converts to top-level viewport
coordinates, plus the top page's scroll. Using the frame's own coordinates
made a button inside a frame look like it sat above the page.
