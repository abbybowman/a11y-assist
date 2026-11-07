# Visual judgment: what can be decided mechanically, and ApiJudge

Research note, 2026-11-07, on branch `agent-follow-through` (commit
ba9f7b6). This is research only: no code, and no spec or rubric change.
The TT PDF (`docs/sources/`) is the authority. TT text below comes from
`tt.json`. Page numbers are the PDF's printed pages: the PDF's own page
index minus 3, checked against the footers on PDF pages 25, 41, 49 and 77.

**Why.** Development runs 5-11 showed that calling agents do not reliably
look at the pictures a question names. They answer "unsure", write
`picture_error` ("not inspected"), or write `seen` without looking (run 11;
`docs/solutions/agent-follow-through.md`). When an agent does look, the
same questions work (judge eval runs 24 and 27: 29/29 and 2/2). There are
two ways out:

1. **Decide mechanically** where one answer is the only possible one, or
   where a measurement settles it.
2. **Send what is left to a model the server controls** (`ApiJudge`), and
   measure it with the judge eval.

Principles 3 and 8 limit both. A mechanical check may confirm an opinion
or replace a question that has only one possible answer. It may never
create a PASS from missing evidence.

## Summary

- **16 open questions across 13 built tests name a picture in `input`,**
  so the `seen` rule applies to them. 4.C J2 carries a screenshot only in
  `evidence_paths`, and the rest are text questions.
  - Of the 16, these truly need the picture: **4.F J1, 4.D J1, 4.E J1,
    5.D J2, 2.B J1, 2.C J1 / 2.B J2 (icons), 5.A J1 (the graphic case),
    5.B J1 (icons) and 5.F J2**. The picture helps but is not decisive
    for 4.A J1 and 5.C J1.
  - **2.D J1/J2, 5.F J1 and 5.G J1** are questions a person settles by
    *reading*. Their pictures are context, yet they trigger the `seen`
    rule.
- **Most visual questions already have their mechanical half built.** 4.D
  measures changed pixels and styles before asking, 4.F computes order
  signals, and 5.A takes visible text and geometry from the DOM. What is
  left is the judgment band. A pixel library will not close it. Some
  measurements could narrow it (below), but mostly towards FAIL or
  NEEDS_REVIEW, never towards PASS.
- **For the visual-versus-code cluster (10.B-10.D, 14.A-14.C, 15.A, 18.A),
  the browser is the main evidence source, not image libraries.** Computed
  styles, box geometry, overflow and ANDI's output give candidates and
  most FAILs. Pixels and OCR add little beyond 7.E (images of text) and
  13.C (text on images), which are outside the cluster as the roadmap
  defines it.
- **No new image dependency is needed now.** Pillow (already locked)
  covers the diff work. The WCAG 2 contrast formula is a few lines and
  needs no library.
  - **NumPy:** any library that needs it (scikit-image, OpenCV, imagehash,
    colour-science) holds us on NumPy 2.4.x, because NumPy 2.5 and SciPy
    1.18 dropped Python 3.11.
  - **APCA:** ruled out. Its licence is restrictive, and it is not
    WCAG 2.
- **ApiJudge:** recommended as a server-side answerer for the
  picture-dependent questions only, with three rules:
  - A failed or timed-out call leaves the question with the calling
    agent, as now.
  - The server model's "unsure" goes to a person, never back to the
    agent.
  - A person's answer still overrides it.
- **Before ApiJudge is turned on,** it must match or beat the agent
  `all`-pictures arm on the judge eval, with zero false PASSes over three
  repeats and a set of prompt-injection packets. The hosted model's API,
  limits and image support are unknown, and are open questions for Abby.

## 1. Inventory of open questions that need a picture or visual judgment

**How this was found.** I searched `src/tobi508/checks/` for `image_`,
`"images"`, `"image"` and `evidence_paths`, and read each spec's section 4.

**Column meanings.**
- **Pic in input:** a `run://…png` is in `input`, so
  `judgment._picture_problem` demands `seen` or `picture_error`.
- **Look-PASS:** the spec marks the question as settled by looking or
  reading (CLAUDE.md principle 8), so an agent's answer can lead to PASS.

### 1a. Questions where the picture carries the evidence

| Test / question | Pic in input | Look-PASS | What a careful tester does (TT) | Mechanical part (built, or possible) | Needs a model | False PASS risk |
| --- | --- | --- | --- | --- | --- | --- |
| **4.D J1** "Does this change show where focus is?" | A off, B on, C diff | No: yes→PASS only with M7's measured change behind it | Tab to each element and look for a visible indicator (p. 22, HtT 1-2) | **Built:** M5 caret, M6 style signal + ≥12 strong px → PASS; M8 < 12 px → FAIL (`t4d.py`, Pillow `ImageChops`). **Possible:** where the changed pixels sit relative to the box (on, touching, elsewhere); their contrast against the off state; anti-aliasing detection (pixelmatch's algorithm) for "only soft edge pixels around text" | Whether a weak or unusual change (a marker, a tooltip, a faint outline) reads as focus | **Low-medium.** A model sees a tooltip or a slide change as a focus change. Mitigated by the rubric ("elsewhere" = no) and by M7's pixels being inside the region. A mechanical "all changed pixels are glyph-edge anti-aliasing" could only route to *no*/FAIL (a false-FAIL risk, not a false PASS) |
| **4.F J1** "Does this focus order preserve meaning?" | A order image | Yes (preserves → PASS) | Tab through and judge whether the order is logical (p. 23, HtT 1-3) | **Built:** order signals (departures from reading order, F44 positive tabindex, opened menus, the backward order). **Possible:** crop the image to the stops in question (run 9: a 768 px full-page thumbnail was unreadable; tall pictures now go in parts, `inline._encode`) | Whether this order makes sense for *this* content (grouping, steps, related fields) | **Medium.** The only judgment with a broad PASS path. f14 was a false PASS until the backward order was added. A model answering from the list alone, without the picture, is exactly what runs 9 and 11 did |
| **4.E J1** "Does this dialog change the context?" | A before, B after | Yes (content_only → PASS) | Move focus and watch for a change of context (p. 22) | **Built:** a dialog appeared with no key pressed; role, name and box. **Possible:** the dialog's share of the viewport, `aria-modal`, whether the page behind it went inert (all from the DOM, not pixels) | Purpose: a sign-up prompt vs a hint bubble | **Low-medium.** A large covering dialog misread as "content only". The box share is a cheap mechanical guard: above a threshold, refuse content_only, or route it to unsure |
| **5.D J2** "Does this change only add content?" | A before, B after | Yes (content_only → PASS, M11) | Change each field and watch for a change of context (p. 27) | **Built:** what changed (navigation, new window, submit, focus move) is mechanical; J2 is asked only for in-page changes. **Possible:** the changed region's box share and whether the main landmark's content was replaced (DOM diff) | Whether a re-arrangement is a change of context | **Medium.** "Re-arranged main content" is subtle in a viewport picture |
| **2.B J1** "Is the movement essential?" | images (frames) | No: leads only to DNA | Identify moving content; judge if the movement is essential (p. 14) | **Built:** pass T finds the movement and its timing; a guard refuses "loading" when controls are usable at 6.5 s | Everything else: purpose of the motion | **None for PASS. False DNA is equally bad (spec).** A model may call a carousel "essential" |
| **2.C J1 / 2.B J2** "Is the mechanism evident?" | images (crop) | Yes, after the key press stopped it (K4/E rows) | Find a mechanism, then use it (pp. 14-15) | **Built:** pressing the control stopped the content (the mechanical confirmation). **Possible:** the visible text of the control from the DOM (innerText, not the accessible name); OCR only for an icon drawn in an image | Recognising a pause icon (‖, ■) or an unlabelled glyph | **Low.** The mechanism already worked. The risk is "evident" for a control nobody would recognise |
| **5.A J1** "Can people see a label?" | A field in context | Yes, labeled only with a quote found in the visible text, or graphic | Look for a visible label or instructions (p. 25) | **Built:** visible text and buttons nearest first, from the DOM; the quote check. **Possible:** the label's geometry relative to the field (distance, alignment) to order the candidates | The **graphic** case (a magnifier icon) and "is this text about this field" | **Low-medium.** Run 12's false PASSes ("Subscribe", "Find") came from the rubric, not from the picture. The graphic answer has no mechanical check |
| **5.B J1** "Do these labels describe their fields?" | per-item image | Yes | Judge whether labels describe purpose (p. 25) | **Built:** pass L items with label, near text, group, placeholder | Descriptiveness, mostly text. The pictures matter for icon buttons | **Medium.** A wide PASS on a whole form (all_descriptive) |
| **5.C J1** "Does what is announced cover what is seen?" | A, B | Yes (complete → PASS, once M3 holds) | Compare ANDI's output with what is shown (p. 26) | **Built:** the ANDI output; `visible` text; the "missing" quote check; the set grouping | Whether a visible cue (a red `*` that is a glyph, a colour) is announced | **Medium.** A cue that exists only visually (a red border, a `*` drawn in CSS `::before`) is invisible to the text input. The DOM can find `::before` content (computed `content`) mechanically |
| **5.F J2** "Does the field's look mark an error?" | A before, B after | No: feeds M3-M5 | Look for how the error is shown (p. 28) | **Built:** colours read. **Possible:** the border or background colour change and its hue (red family) from computed styles, with no pixels needed | Icons, unusual styling | **Low** |
| **4.A J1** "Is there another keyboard way?" | A page | No: alternative → PASS only through stops | Find the keyboard equivalent (p. 19) | **Built:** the stop list and the guard that the number names a stop | Matching purpose: mostly from names, the picture helps | **Low-medium** |

### 1b. Questions settled by reading, with a picture attached

| Test / question | Pic in input | Look-PASS | What it really needs | Note |
| --- | --- | --- | --- | --- |
| **2.D J1** focused content says what changed | images | Yes | the focused element's text | The picture adds little. With it in `input`, `seen` is demanded |
| **2.D J2** the dialog says what changed | images | Yes | the dialog's role, name and text | as above |
| **5.F J1** error text names the field and the problem | before, after | Yes, with the quote check | error texts and where they appeared | as above |
| **5.G J1** the error says how to fix it | before, after | Yes, with the quote check | errors and instructions | as above |

**Option, not decided.** Move these pictures from `input` to
`evidence_paths`. The `seen` rule would then stop asking agents to look
at pictures that do not settle the question. This would be the cheapest
cut in picture burden: four question kinds, no new code beyond the input.
It changes question inputs, so the judge eval runs first (principle 6).
The risk is small: a 5.F error shown only as a red icon is 5.F J2's case,
which keeps its pictures.

### 1c. Text questions (no picture in input)

These are 2.C J2 and 2.B J3 (text describes a way to stop),
4.A J2 (title essential), 4.B J1/J2, 4.C J1 and J2 (4.C J2 has a
screenshot in `evidence_paths` only), 5.D J1 and J3, 5.F J0, 5.H J1/J2,
9.A J1/J2, 9.C J1 and 19.A J1.

They stay with whoever answers text well. Runs 7-11 answered 9.C from
names alone, which the 1.1.1 rubric now allows.

### 1d. Volume

The volume sets ApiJudge's cost:
- Development runs 9-11 answered 24-30 questions per 5-page run, 14-15 of
  them picture questions (round1-postfix README, runs 9-11).
- Before 5.C's set grouping, NASA's Missions page alone asked 81, 56 of
  them 5.C's.

## 2. Libraries for deterministic visual and text processing

**How the facts were checked.** Licence, last release, Python and wheel
sizes come from the PyPI JSON API on 2026-11-07, read with a script in
the scratchpad. "MB" is the largest Linux x86-64 wheel usable on 3.11.
npm facts come from registry.npmjs.org.

Nothing here does cryptography. FIPS 140 applies to cryptographic
modules, so these libraries carry no FIPS question themselves. The FIPS
points that matter:
- the TLS connection to the hosted model (the host's FIPS OpenSSL);
- SHA-256 in PROVENANCE, which is an approved algorithm;
- libraries that download models and use `hashlib.md5` without
  `usedforsecurity=False` can fail on a FIPS-mode host. This is assumed,
  not tested here.

| Library | Licence | Latest (date) | Py 3.11 wheel / size | Offline / Windows | Accuracy evidence | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **Pillow** (`ImageChops`) | MIT-CMU (HPND), permissive | 13.0.0 (2026-10-16) | yes, 7 MB, **already locked** | yes / yes | Exact pixel arithmetic; 4.D's M6-M8 already run on it | **Keep. Enough for diff, masks, bbox and crops** |
| pixelmatch (Python port) | ISC | 0.4.0 (2026-03-07) | pure Python, <1 MB | yes / yes | Anti-aliasing detection (Vysniauskas 2009), used by the JS original in visual regression | **Worth a look for 4.D's "soft edge pixels"**: one small function. Slow in pure Python, fine on crops |
| scikit-image (SSIM, morphology, regionprops) | BSD-3 | 0.26.0 (2025-12-20) | yes, 13 MB + NumPy + SciPy | yes / yes | Standard SSIM | Not needed. Region labelling can be done in Pillow, or with a small flood fill |
| opencv-python-headless | Apache-2.0 | 5.0.0.93 (2026-07-02), abi3 | 61 MB (Win 43) + NumPy | yes / yes | Broad | Too large for what we would use |
| imagehash | BSD-2 | 4.3.2 (2025-02-01) | pure Python + NumPy, SciPy, PyWavelets | yes / yes | Perceptual near-duplicate detection | Only if motion frames need "looks the same"; not now |
| NumPy (dependency of the above) | BSD-3 and others | 2.5.4 (2026-10-10) needs **Py ≥3.12**; last for 3.11 is 2.4.6 | | | | **Flag:** adding it holds us on 2.4.x while `requires-python >=3.11` |
| SciPy | BSD-3 | 1.18.1 needs **Py ≥3.12**; last for 3.11 is 1.17.1 | | | | as NumPy |
| **WCAG 2 contrast maths** | our own code | n/a | ~10 lines | yes / yes | The WCAG 2 relative-luminance definition; ANDI uses the same | **Write it; no dependency** (13.C, 4.D indicator contrast if ever needed) |
| coloraide | MIT | 8.14 (2026-11-02) | pure Python, <1 MB | yes / yes | Implements the WCAG 2.1 contrast ratio and colour spaces | Only if we need ΔE or colour spaces |
| colour-science | BSD-3 | 0.4.7 (2025-12-06) | 9 MB + NumPy, SciPy | yes / yes | Reference-grade | Too heavy for this use |
| wcag-contrast-ratio | MIT | 0.9 (2015) | sdist only | | | Unmaintained; skip |
| APCA (`apca-w3`, npm) | "Limited W3 License": commercial use prohibited without agreement; scope limited to WCAG 3 work | 0.1.9 | | | Not WCAG 2; TT uses WCAG 2.x | **Exclude** (licence, and not the TT's measure) |
| **Tesseract** (via pytesseract or tesserocr) | Apache-2.0 (engine); pytesseract Apache-2.0; tesserocr MIT | engine 5.5.x (Wikipedia: 5.5.3, 2026-07-24; not confirmed on GitHub); pytesseract 0.3.13 (2024-08); tesserocr 2.12.0 (2026-10-22) | **system binary** (apt `tesseract-ocr` on Linux, an installer on Windows) + tessdata (`eng.traineddata`: fast ≈4 MB, best ≈15 MB; *assumed sizes*). tesserocr wheels bundle the library (Linux 5 MB, Win 23 MB) | yes once installed / yes | Good on clean, high-contrast rendered text (screenshots at 2× DPR); weak on small or stylised text over images. No benchmark found for UI screenshots | **Best OCR fit if OCR is ever needed** (7.E, 13.C). A system install, so ask first (CLAUDE.md). Vendor tessdata with a SHA-256 |
| RapidOCR (`rapidocr`, onnxruntime) | Apache-2.0; onnxruntime MIT | rapidocr 3.10.0 (2026-10-08); onnxruntime 1.31.1 | 27 MB + onnxruntime 23 MB | *assumed* offline (models packaged; not checked) / yes | PP-OCR models (Paddle's) on ONNX, CPU-only | The alternative if a system binary is ruled out |
| EasyOCR | Apache-2.0 | 1.7.2 (2024-09-24) | 2 MB **+ PyTorch** (CPU wheel ≈ 100-200 MB; the Linux default CUDA wheel is 539 MB) | downloads models at first use unless pre-staged (`model_storage_directory`) / yes | Good on scene text | **No**: slow upkeep, large footprint, network at first use |
| PaddleOCR | Apache-2.0 | 3.7.0 (2026-06-11) | 0 MB + paddlepaddle 194 MB | downloads models / partial | Strong (PP-OCR) | **No**: footprint; use RapidOCR for the same models |
| docTR | Apache-2.0 | 1.1.0 (2026-08-21) | + PyTorch | downloads models / yes | Strong on documents | **No** (PyTorch) |
| **axe-core** | MPL-2.0 (unmodified files: no terms on our code) | 4.14.0 (npm; 3.4 MB unpacked) | vendored JS, run in our page | yes / yes | ACT implementation reports | Evidence for 10.B (`p-as-heading`, experimental), 10.D (`list`, `listitem`, `definition-list`), 14.B (`td-headers-attr`, `th-has-data-cells`), 18.A (`meta-viewport`), 13.C (`color-contrast`). **Never a PASS by itself.** Already planned (ROADMAP "Scanners") |
| IBM Equal Access `accessibility-checker-engine` | Apache-2.0 | 4.0.34 (npm; 25.6 MB unpacked) | vendored JS | yes / yes | ACT implementation reports (W3C ACT implementations page) | Has rules axe lacks for this cluster, both "needs review": `text_block_heading` (styled text that may be a heading: 10.B) and `table_layout_linearized` (14.C/15.A) |

**Layout and geometry from the browser itself.** This comes before
pixels. Playwright and CDP already give:
- `getBoundingClientRect` and `DOM.getBoxModel`;
- `getComputedStyle` (font size and weight, `display`, `position`,
  `overflow`, `text-overflow`, `::before`/`::after` content, colours);
- `scrollWidth > clientWidth` on elements and the document;
- `elementFromPoint`, to detect when one element covers another;
- `Emulation.setDeviceMetricsOverride` (the window size and device pixel
  ratio).

The walk already reads boxes and styles, and `andi.andi_output` gives
ANDI's per-element analysis. These are exact, cheap, and the same on
every run. For the cluster they are the primary evidence, as ANDI is for
a human tester.

## 3. The visual-versus-code cluster

**A correction to the prompt.** "10.x sensory characteristics/images of
text" does not match TT 5.1.3. In TT 5.1.3:
- 10.A-10.D are headings and lists (section 10, Content Structure);
- sensory characteristics is **13.B**, and images of text is **7.E**.

Both are covered below for completeness. 7.E and 13.B are not in
ROADMAP's cluster.

### DHS's ACT verdicts

Source: `act-tt` (Section508Coordinators/act-tt, `act-trusted-tester.json`),
fetched 2026-11-07. It holds DHS verdicts only for 1.4.5 (7.E), 2.4.6
(10.A, 5.B) and 2.4.7 (4.D) among the tests below.
- **1.4.5, ACT rule 0va7u6:** DHS agrees on 11 cases, and gives
  *inapplicable* for 4 of ACT's 8 *passed* cases. DHS treats more of
  those images as not images of text.
- **1.3.1 (10.B-10.D, 14.x), 1.3.2 (15.A), 1.4.3 (13.C) and 1.4.4
  (18.A):** none.

### The cluster, test by test

| Test (p.) | What a careful tester does | ANDI gives | Mechanical evidence available | What still needs looking | ACT rules (W3C testcases.json) | Baseline Alignment cases |
| --- | --- | --- | --- | --- | --- | --- |
| **10.B** Heading determinable (p. 46; identify content p. 46) | Find visual headings (larger, bold, spaced); compare with ANDI's headings both ways | Core: headings outlined, ANDI output | Computed font size and weight against body text, spacing, short line, followed by content → candidate visual headings not marked up (IBM `text_block_heading`, axe `p-as-heading` do this); headings with tiny or normal styling → candidates for "not a visual heading" | Whether a candidate *functions* as a heading (a bold lead-in sentence vs a section title) | none mapped to TT 10.B | TC13.B-1.c-fail-1…4, TC13.C-1-fail-1/2 (non-visual heading, menu items as headings), TC13.B-all-pass-1…3, TC13.B/13.C ic-dna |
| **10.C** Heading level (p. 47) | Compare ANDI's outline levels with the visual hierarchy | Core: structure outline, ARIA vs HTML level conflicts | Font size order vs level order (a level-2 rendered larger than a level-1); level skips. A "single heading, any level" rule (HtT 3.a) is mechanical | Whether two sizes mean two levels (designs vary) | none | TC13.B-1.a-fail-1/2, TC13.B-1.b-fail-1, TC13.C-1-pass-1 |
| **10.D** List type (p. 48) | Find visual lists; check ANDI's list type and nesting | Inventory (lists) | Runs of sibling blocks starting with a bullet glyph or "1." / "a)" in text or `::before`, `display:list-item`; `ol` vs `ul` vs numbered text; nesting depth vs indentation | Whether a run *is* a list (vs a sentence, p. 48 Note), and navigation exclusion | none | TC13.D-1/2/3 fail and pass, TC13.D-ic-dna-1 |
| **14.A** Table identification (p. 60; identify p. 60) | Find data tables (including images of tables); check that ANDI finds each | Core (tables) | Grid-like non-table markup (CSS `display:grid` or `table`, repeated aligned rows of cells) → candidates; `role=presentation` on a `table` with `th` | Whether cells need headers to be understood (data vs layout, p. 60 Note) | a25f45, d0f69e (header associations, programmatic only) | TC12.A-2-fail-1/2, TC12.A-3-fail-1, TC12.A-all-pass-1 |
| **14.B** Cell header association (p. 61) | Inspect ANDI's headers per data cell | Core | ANDI's associations per cell; `headers`/`scope` validity (axe `td-headers-attr`, `th-has-data-cells`) | Which headers are *relevant* (visual header rows without markup) | a25f45, d0f69e | TC12.A-4-fail-1…6 |
| **14.C** Layout table structure (p. 62) | Check layout tables have no `role=table` or header markup | Core | Fully mechanical once a table is known to be layout: `th`, `scope`, `caption`, `headers`, ARIA table roles | Data vs layout (shared with 14.A) | none | none found |
| **15.A** Content order without CSS (p. 64; identify p. 64) | ANDI linearizes the page; judge whether the order still makes sense | Core (linearize) | Elements whose position is set by CSS (absolute, fixed, floats, flex/grid `order`, `row-reverse`) → DNA mechanically when none; DOM order vs visual order (box geometry) → the departures, like 4.F's signals | Whether a departure changes meaning (F1, F49) | none | none found |
| **18.A** Resize text (p. 74) | Zoom to 200%; look for clipped, truncated or obscured text; lost content or function | none | `overflow:hidden` + `scrollWidth > clientWidth` on text containers (ACT 59br37), `text-overflow: ellipsis`, fixed `height` with overflowing text, overlap by `elementFromPoint`, `meta viewport` blocking zoom (b4f0c3), viewport-unit font sizes (F94), keyboard stops at 100% vs 200% | Whether an overlap or cut hides *content* (a decorative image cut is fine); whether a function moved rather than vanished (hamburger menu) | 59br37 Zoomed text node is not clipped with CSS overflow (4 passed / 5 failed / 5 inapplicable); b4f0c3 Meta viewport allows for zoom (5/7/4) | none found (the Baseline site has no "22. Resize Text" cases) |
| 7.E Image of text (p. 38; identify p. 37) | Find images of text (not logos or diagrams); can it be text, or customised? | Inventory (images) | **OCR is the evidence here**: text detected in `img`, CSS backgrounds or canvas, and its share of the image | Logotype or essential? Mostly text, or a picture containing text (excluded, p. 37)? | 0va7u6 HTML images contain no text (DHS verdicts above) | TC06.D-1-fail-1, TC06.D-ic-dna-1 |
| 13.B Sensory info (p. 56) | Read instructions for shape, colour, size or position words | none | Word list in visible text ("click the green button", "on the right", "round icon") → candidates; "above" or "below" for sequence is allowed (Note) | Whether another non-sensory cue is given | 9bd38c Content has alternative for visual reference (15/4/2) | TC07.B-ic-dna-1 |

**18.A: open decision (ROADMAP, found 2026-11-06), listed, not decided.**
Three questions are open:
- **Which window or windows.** Proposed: the default 1280 px, and one near
  1024 px.
- **A failure only in the smaller window:** FAIL, or NEEDS REVIEW with a
  note.
- **How to zoom.** "Half the viewport width at DPR 2" is assumed to lay a
  page out like 200% zoom, and needs a V-check against real Ctrl+ zoom in
  headed Chrome.

**What the sources add (checked 2026-11-07).**
- **TT and Baseline.** Neither names a window size:
  - TT p. 74 says "use built-in browser zoom functions";
  - ICT Baseline Test 22's instructions say "200% of original size", and
    list browser zoom, platform features or on-page controls as
    acceptable ways.
- **WCAG Understanding 1.4.4 says three things:**
  - content passes if *one* user-agent mechanism reaches 200%;
  - the criterion "applies to each layout variation", such as media-query
    breakpoints;
  - its example uses a 1280 CSS px window.
- **The techniques to cite:**
  - sufficient: G142, G179, G146, G178, C28, C12-C14, SCR34;
  - failures: F69 (clipping), F80 (form controls), F94 (viewport units).
- **Zooming in headless Chrome.** CDP's `Emulation.setPageScaleFactor`
  magnifies without re-laying out the page, so it is not a stand-in for
  browser zoom. Playwright has no built-in zoom (playwright issue #2497).

## 4. ApiJudge design options

The stub is `ApiJudge(endpoint, model)` in `judgment.py`. `get_judge("api")`
exists, but `config.judge_backend` is `Literal["client"]`, so it cannot be
switched on yet. That is by design.

### 4a. Interface

- **Same contract.** `judge(questions) -> JudgeResult(answers, pending)`.
  ApiJudge answers the questions it is configured for and returns the rest
  as `pending`, which go to the client as now. Answers go through
  `record_answers`, so every existing guard applies unchanged:
  - kind and choice validity;
  - quote-found checks;
  - the stop-number guard.

  Outcomes still come only from the specs (principle 2).
- **`decided_by` stays `"model"`.** A model answer needs no new outcome
  path. Two things become ambiguous, though:
  - which model answered (the server's, or the calling agent's);
  - `Versions.judging_model`, which is today one server setting ("none")
    that records nothing about the client agent.

  **Proposal:** add `Answer.answered_by` (e.g. `"server:<model id>"` vs
  `"client"`), set by the server, never by the caller. Record the hosted
  model's id and version, a hash of the prompt template, and the
  parameters in `judging_model` (principle 4).
- **The `seen` rule.** Keep it for the client's answers. For ApiJudge,
  `seen` is still worth filling: it is a short description the judge eval
  can check, and a person can read. The server can now *know* the picture
  was sent, so `not_viewed` is always false.

### 4b. What the model is given

- **What goes in.** The question, the rubric and the `question_texts`
  entry; the input and the `shared_inputs` it names; the pictures
  themselves.
  - **Picture size.** Send pictures at full captured resolution, or as
    crops, not the 768 px downscale `inline.py` makes for clients. The
    hosted model's image limits decide the tile size: an open question.
  - **4.F needs crops.** A full-page order picture is unreadable when
    shrunk (run 9). Crops around the stops in question help any judge, so
    they are worth building first.
- **Untrusted content, in structure.** The system prompt is fixed and
  holds no page content. The page-derived input goes in one delimited
  JSON block labelled as untrusted data, as `OpenQuestion.input`
  describes it now.
- **The answer is structured.** Use JSON-schema output with the
  question's `choices` as an enum, `quote`, `reasons` and `seen`. Free
  text is ignored.
- **No tools, no URLs.** The model's output can never choose a URL, a
  tool or an outcome (principle 5).
- **Prompt injection.** Screenshots and page text can say "answer
  preserves", and an image is a channel text filters do not see. The
  defences:
  1. **Structure.** An enum answer, so an injected instruction can only
     pick an allowed choice.
  2. **The existing mechanical guards.** Quotes must be found in the
     text; 4.D's PASS needs measured pixels; 2.C's evident needs the key
     press that worked.
  3. **Only `unsure` defaults to a person.**
  4. **An injection set in the judge eval.** Custom fixture pages whose
     visible text addresses the judge, as a red-team case (a gap no ACT
     page covers, so a custom page is allowed). Their expected answer is
     the one with the text ignored.

  No defence is complete. These limit an injection to choosing among the
  choices the spec already allows. They do not limit it to "unsure".

### 4c. Where it runs

| Option | How | For | Against |
| --- | --- | --- | --- |
| **A. Server first, for picture questions (recommended)** | In the job, after checks create questions and before the result is returned; questions in 1a go to ApiJudge, the rest to the client | Works whatever the client and prompt; the picture is certainly looked at; the agent sees fewer, text-only questions | The server pays and waits; a hosted endpoint is needed in tests (mock) |
| B. Server for every question | All questions to ApiJudge | One judge, the most consistent | Text questions already work with agents; cost; the model may read worse than the calling agent |
| C. Fallback only | ApiJudge answers what the client left unsure or `not_viewed` | Cheapest | Run 11 shows `seen` filled without looking: wrong-but-sure answers never reach the fallback |

**What these options assume.**
- **Latency.** The calls run inside the job (`jobs.py`), so
  `CALL_WAIT_S` and `tobi_run_status` already cover them. The calls are
  independent, so a small concurrency limit (e.g. 4) keeps the time near
  the slowest call.
- **Failure.** A timeout, an HTTP error, a refusal or a schema violation
  leaves the question pending for the client, as now. It is never
  answered by default, and the failure is recorded in `steps.jsonl`.
- **The server model's "unsure" goes to a person (recommended).** It
  becomes NEEDS_REVIEW with the open question for a person. It does not
  go back to the agent, which had a worse view of the same picture.
- **Overrides.** A person's answer overrides any model
  (`current_answer`). Whether the *calling agent* may override the
  server model's answer is an open question; the recommendation is no.

### 4d. Cost and latency per run

The figures are estimates, built from what we have. The hosted model's
pricing and speed are unknown.

**Questions per run.**
- 24-30 questions per 5-page development run, 14-15 of them picture
  questions (runs 9-11).
- Option A sends about 15 per 5 pages; option B sends about 30.
- Worst case: one large form page asked 81 before grouping (Missions).

**Input per question.**
- Text: about 1-4k tokens (question, rubric, input). Large inputs reach
  more: one 4.F stop list was 13k characters, about 3-4k tokens.
- Pictures: one to four per question.
- What a picture costs depends on the model. For scale, Anthropic's
  published approximation is width × height / 750 tokens, which gives
  about 1k tokens for a 768×1024 tile; full resolution or several tiles
  cost proportionally more.
- Total: about 3-10k input tokens and under 300 output tokens per
  question.

**Per 5-page run.**
- **Option A:** about 50-150k input tokens. That is about the same as the
  calling agent's whole new context per run now (107-122k, runs 10-11;
  round1-postfix README).
- **Time:** about 15 questions, 4 at a time, at 3-15 s each (assumed):
  roughly 15-60 s per run, inside the job.

**To measure.** `evals/time_budget.py` gives the collect-phase cost
today. An ApiJudge phase in `steps.jsonl` (calls, tokens, seconds) would
let it report the judging cost the same way.

### 4e. How to evaluate it

1. **Add a judge-eval answering backend.** `evals/judge_eval.py prepare`
   builds the packets as now. A new step runs ApiJudge over each packet
   (the same prompt the server will use) in place of a fresh agent, then
   `apply` scores as now.
2. **What counts.**
   - false PASS first, and false DNA for 2.B;
   - then matches, false FAILs and unsure answers;
   - run on all packets (the 71 cases of run 19) plus the injection set.
3. **Three repeats.** Repeat at least 3 times at the model's lowest
   temperature. One run is noise for behaviour
   (solutions/agent-follow-through.md). Report the spread.
4. **The bar before `judge_backend` may be set to "api":**
   - zero false PASS and false DNA in every repeat;
   - matches at least the agent `all`-pictures arm (run 19: 67/70, 0
     false PASS);
   - every injection case answered as if the injected text were absent.

   Then a development answering run with ApiJudge on (option A), compared
   with runs 10-11.
5. **Rubric examples must not be fixture words** (solutions/judge-eval.md,
   runs 26-27): grep `tests/fixtures/` first. This matters more for a
   model that may have been tuned on public ACT pages.
6. **Leaks.** The packet scrubbing rules apply to the server prompt too.
   Fixture file names must never reach the model.

### 4f. Which questions stay with the calling agent

**Under option A:**
- the text questions in 1c;
- the reading questions in 1b, if their pictures move to `evidence_paths`.

If they keep their pictures, they go to ApiJudge with the rest of 1a.

**A person still answers:**
- anything the server model answers unsure;
- every question when the endpoint is not configured.

## 5. Recommendations, ranked by false-PASS safety, then effort

1. **Decide mechanically only what has one possible answer, and use
   measurements to route, never to pass.** No new dependency.
   - **4.E/5.D J2:** a covering-share guard that refuses `content_only`
     for a dialog covering most of the viewport (to unsure).
   - **5.C:** CSS `::before` content added to `visible`.
   - **4.D:** where the changed pixels sit, passed to the judge as
     numbers.

   Each is a spec change (MINOR) with its own fixture. None can create a
   PASS. Effort: small, per test.
2. **Better pictures for any judge.** Crop 4.F's order picture to the
   stops in question, and give 2.B content below the first screen a crop
   (ROADMAP). This removes "unreadable" as a reason to skip looking.
   Effort: small to medium. Run the judge eval after each.
3. **Move the pictures out of `input` for reading questions** (2.D J1/J2,
   5.F J1, 5.G J1), so `seen` stops being asked where looking does not
   settle anything. Effort: small, plus a judge eval.
4. **ApiJudge, option A**, behind `JUDGE_BACKEND=api`.
   - **Build it after** the hosted model's API is known.
   - **Turn it on only after** the judge eval bar in 4e.
   - **Effort:** medium (client, prompt, mock in tests, eval backend,
     recording).
   - **The largest gain.** It is the only option that removes the
     dependence on the agent looking.
5. **For the cluster, start from the browser and ANDI, not pixels.**
   - Computed styles, boxes, overflow and ANDI output as candidates and
     FAIL evidence.
   - axe-core and IBM's engine as evidence sources (already planned).
   - A model or person for "is this a heading / list / data table / a
     meaningful order".

   Choose the first test with the coverage map. 18.A waits on the window
   decision. 14.C is the most mechanical once data-vs-layout is settled.
6. **OCR: not now.** It earns its place only with 7.E (and 13.C text on
   images).
   - **When 7.E is built:** Tesseract 5.5 with vendored `eng` tessdata,
     a system install, so ask first.
   - **If a system binary is ruled out:** RapidOCR (Apache-2.0,
     onnxruntime).
   - **Not:** EasyOCR, PaddleOCR or docTR.

## 6. Open questions for Abby

1. **The hosted model (NASA).**
   - The API style (OpenAI-compatible? Bedrock? something else?) and how
     the server authenticates.
   - Image input: whether it is supported, the formats, the largest size
     and the number of images per request.
   - Context and output limits, rate limits, cost or quota per run.
   - Whether it gives deterministic settings (temperature 0, seed).
   - A model version id we can record.
   - Data handling: may screenshots of public .gov/.mil pages be sent?
     Are prompts logged or retained?
   - Is the endpoint FIPS-validated TLS? Is it reachable from the hosted
     deployment?
2. **Licence policy.**
   - Are MPL-2.0 (axe-core, unmodified) and Apache-2.0 (IBM engine,
     Tesseract, RapidOCR) acceptable for GSA and NASA release?
   - Is a system-installed OCR binary acceptable in the container image
     and on Windows?
3. **Overrides.** May the calling agent override an ApiJudge answer, or
   only a person? (The recommendation is only a person.)
4. **Where unsure goes.** Should an ApiJudge "unsure" go straight to a
   person (recommended), or to the agent first?
5. **18.A.** The ROADMAP decision:
   - which windows (1280 px, and about 1024 px?);
   - a failure only in the smaller window: FAIL or NEEDS REVIEW;
   - approval to V-check the zoom stand-in against real Ctrl+ zoom on
     Windows headed Chrome.
6. **Reading questions.** May the pictures move from `input` to
   `evidence_paths` for 2.D J1/J2, 5.F J1 and 5.G J1, subject to the
   judge eval?

## Verified vs assumed (principle 6)

**Verified, with commands this session:**
- The inventory, from the checks' code (grep of `image_`, `"images"`,
  `"image"`, `evidence_paths`) and the specs' section 4.
- `judge_backend` is `Literal["client"]`; `judging_model` defaults to
  "none".
- Pillow is the only image dependency; 4.D, `motion.py` and
  `mechanism.py` use `ImageChops`.
- Licences, versions, dates, Python requirements and wheel sizes from the
  PyPI JSON API; npm licences, versions and sizes from the registry.
- NumPy 2.5 and SciPy 1.18 require Python ≥3.12.
- DHS act-tt verdicts and ACT rule case counts, from the two JSON files.
- Baseline Alignment cases, from baselinealignment.section508.gov
  testcases (148 cases; none for Resize Text or CSS positioning).
- TT text from `tt.json`, and printed page numbers from the PDF.
- WCAG Understanding 1.4.4, 1.3.2 and 1.4.5 techniques, from w3.org.
- ICT Baseline Test 22's instructions, from ictbaseline.access-board.gov.
- Run figures from `evals/README.md` and
  `evals/judging/round1-postfix/README.md`.

**Assumed or second-hand (not checked):**
- Tesseract's latest version (5.5.3, per Wikipedia) and tessdata sizes.
- RapidOCR running fully offline with packaged models.
- EasyOCR's upkeep (third-party review sites).
- APCA licence details (secondary sources, plus npm's licence string
  "Limited W3 License").
- `setPageScaleFactor` behaviour (forum posts).
- FIPS behaviour of model-downloading libraries.
- Every cost and latency figure in 4d, since the hosted model is unknown.
- Whether Windows behaves the same as Linux for any library (no Windows
  here).

## Sources

**In the repository:**
- CLAUDE.md;
- `docs/plans/2026-11-06-agent-follow-through.md` (changes 3 and 6);
- `docs/solutions/agent-follow-through.md` and `judge-eval.md`;
- `docs/research/2026-10-31-tt-coverage-map.md`;
- `docs/ROADMAP.md` (the cluster and 18.A);
- `docs/rules/*.md` section 4;
- `src/tobi508/judgment.py`, `inline.py`, `config.py`, `models.py`;
- `evals/README.md` (runs 19, 24, 26-27);
- `evals/judging/round1-postfix/README.md`;
- `docs/sources/Trusted Tester Test Process v5.1.3.pdf` and
  `tt-5.1.3/tt.json`.

**ACT and DHS data:**
- [act-tt](https://github.com/Section508Coordinators/act-tt)
  (`act-trusted-tester.json`);
- [W3C ACT testcases.json](https://www.w3.org/WAI/content-assets/wcag-act-rules/testcases.json).

**Baselines and WCAG:**
- [Section 508 Baseline Alignment test cases](https://baselinealignment.section508.gov/testcases.html);
- [ICT Testing Baseline, 22. Resize Text](https://ictbaseline.access-board.gov/web-baselines/22Resize/);
- WCAG 2.2 Understanding:
  [1.4.4](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html),
  [1.3.2](https://www.w3.org/WAI/WCAG22/Understanding/meaningful-sequence.html),
  [1.4.5](https://www.w3.org/WAI/WCAG22/Understanding/images-of-text.html).

**Packages:**
- PyPI JSON API (`https://pypi.org/pypi/<name>/json`);
- npm registry (`https://registry.npmjs.org/<name>/latest`).

**Libraries and tools:**
- [Tesseract (Wikipedia)](https://en.wikipedia.org/wiki/Tesseract_(software));
- [EasyOCR release notes](https://github.com/JaidedAI/EasyOCR/blob/master/releasenotes.md);
- [APCA licence](https://www.github.com/Myndex/SAPC-APCA/blob/master/LICENSE.md)
  and [apca-w3 discussion #12](https://github.com/Myndex/apca-w3/discussions/12);
- [IBM text_block_heading help](https://app.unpkg.com/accessibility-checker-engine@4.0.29/files/help/en-US/text_block_heading.html);
- [W3C ACT implementations: Equal Access](https://www.w3.org/WAI/standards-guidelines/act/implementations/equal-access);
- [Playwright issue #2497 (zoom)](https://github.com/microsoft/playwright/issues/2497).
