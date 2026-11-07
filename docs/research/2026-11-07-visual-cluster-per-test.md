# The visual-versus-code cluster, test by test: what ANDI, axe-core and our own code already give

Research note, 2026-11-07. It goes deeper than section 3 of [2026-11-07-visual-judgment-and-apijudge.md](2026-11-07-visual-judgment-and-apijudge.md). It covers 10.B, 10.C, 10.D, 13.C, 14.A, 14.B, 14.C, 15.A, 18.A and 7.E.

This is research, not an authority. The TT PDF is the authority, and TT text comes from `tt.json`. Page numbers are the PDF's printed pages.

**Sources read.**
- **ANDI:** the vendored ANDI 29.2.2 (`third_party/andi/*.js`).
- **axe-core:** 4.14.0, from npm. I listed its rules with `axe.getRules()` in Chromium.
- **Our code:** the files cited below.
- **Two experiments**, recorded in their sections: contrast maths (13.C) and browser zoom (18.A).

## Cross-cutting facts (they apply to every test below)

### ANDI as we run it today

- **Only ANDI's focusable-elements module runs.** `andi.inject_andi` loads `andi.js`, which launches its default module, `f` (andi.js:45, 132). Nothing in `src/` launches the structures (`s`), tables (`t`), contrast (`c`) or graphics (`g`) modules.
  - **They work offline.** Our route serves every file under `third_party/andi/` (andi.py:43-55), so `AndiModule.launchModule("s"|"t"|"c"|"g")` loads them from local files.
- **`andi_output` reads only part of what ANDI stores.**
  - **What it reads:** each element's name, description, group, dangers and warnings (andi.py:88-125).
  - **What it does not read:**
    - ANDI's *cautions*;
    - the contrast module's per-element data (`$(el).data("candi508")`);
    - the tables module's cell indexes (`data-tandi508-*`);
    - page-level alerts, such as "Ensure that background images are decorative." Those go only to ANDI's alert list in the DOM (andi.js:3691-3698).
  - **Extending it is small work.** Each test below needs one more field read.
- **ANDI only analyses the top document.** It wraps the page in `#ANDI508-testPage`.
- **ANDI's tables module analyses one table per launch.** It defaults to the first table and uses its next/prev buttons for the others (tandi.js:148-149). It computes the header text a cell is announced with only when a cell is inspected (hover or focus, tandi.js:349-567).

### axe-core 4.14.0 (not vendored yet)

- **Licence:** MPL-2.0. Unmodified files place no terms on our code.
- **It tags some rules with TT v5 test IDs itself:**
  - `color-contrast` → TT13.c;
  - `td-headers-attr`, `th-has-data-cells` and `td-has-header` → TT14.b;
  - `image-alt`, `role-img-alt`, `svg-img-alt` and `input-image-alt` → TT7.a;
  - `link-in-text-block` → TT13.a.
- **Rules for this cluster that carry no TT tag:**
  - `p-as-heading` (experimental, wcag131);
  - `list`, `listitem`, `definition-list`, `dlitem` (wcag131);
  - `table-fake-caption` (experimental);
  - `meta-viewport` (wcag144);
  - best-practice only: `heading-order`, `empty-heading`, `empty-table-header`, `scope-attr-valid`.
- **Running it.** The roadmap's plan is to run axe on its own fresh load after the walk (`docs/solutions/scanners-after-the-walk.md`). Its results are evidence for spec rows, never a PASS by themselves.

### Our own code that the cluster can reuse

| What | Where | Gives |
| --- | --- | --- |
| Page units in DOM order | `site.UNITS_FN` (site.py:28-179); cached per run and by HAR SHA (site.py:271-292) | text, heading, image-with-alt, control and frame units, each with a page box and region chain. Skips hidden content and images without alt |
| Visual-order comparator | `site.before(a, b)` (site.py:325-335) | whether one box comes before another as people read (same line when overlap ≥ 50%) |
| Units with iframes inline | `motion.read_elements` (motion.py:537-579) | the same list, iframes spliced in, `aria-hidden` and label duplicates removed |
| Image bytes from the recording | `capture.media_body(har, url)` (capture.py:208-225); HARs are recorded with full bodies (capture.py:54-55) | the exact image files the page loaded, with no network |
| Animated images | `motion._long_images` and `_IMAGE_JS` (motion.py:1220-1287) | GIF/WebP/PNG type, frame count, play-through time and loop count (not frame hashes) |
| Per-element look hashes | `M.snap` (motion.py:171-213) | hashes of text, image source, background image, colours and transforms (hashes only, not values) |
| Screenshots | traverse.py:777-785; full page in t4a.py:466 and t4f.py:476; field clips in labels.py:384-386 | PNGs; Pillow is already a dependency |
| Keyboard stops | `walk.walk_page`; each stop has CSS path, AX role and name, box, widget and frame (traverse.py:656-705) | the walk's stops at 100% (needed again at 200% for 18.A) |
| Cross-call cache | `pagecache.keep_read(kind, har_sha, …)` (pagecache.py) | any new read ("andi-s", "andi-t", "andi-c", "contrast", "ocr") is cached per recording, as "site" and "andi" are now |

**A gap found on the way.** `site.UNITS_FN` takes an `h1`-`h6` element's level from its tag and ignores `aria-level` (site.py:146), so `<h2 aria-level="1">` is level 2.
- **Today:** only 9.A and 19.A use the level, to find the page's level-1 heading.
- **For 10.C:** it must read the exposed level (the accessibility tree, or ANDI's structures module) instead.

## 10.B Heading determinable (p. 46)

**What a tester does** (identify content p. 46; HtT pp. 46-47). Find every visual heading (larger, bold, set apart) and compare it with ANDI's headings in both directions:
- each programmatic heading looks like a heading;
- each visual heading is a programmatic heading.

**ANDI: structures module, headings mode** (default).
- **Headings.** It lists `h1`-`h6` and `role=heading`, with a valid role winning over the tag, and skips `aria-hidden` ones (sandi.js:41-52).
- **Fake headings.** `sANDI.isFakeHeading` (sandi.js:184-228) gives warning `alert_0190`, "Element visually conveys heading meaning but not using semantic heading markup." The heuristic:
  - **Elements checked:** `p, div, span, strong, em` with fewer than 30 characters.
  - **Size:** font-size over 22 px, or bold over 15 px.
  - **Next element:** the next visible sibling has text and is smaller, or not bold.
  - **Limitation:** it only checks content *before the first real heading* in DOM order (sandi.js:134). A page with an `h1` in its header gets almost no fake-heading checks.

**axe:** `p-as-heading`. It is experimental, checks `p` elements only, and compares bold, italic and font size with the following paragraphs.

**IBM Equal Access:** `text_block_heading`, a "needs review" rule (from the earlier research; not vendored).

**Our code:** `site.UNITS_FN` gives headings and text units in DOM order with boxes. It reads no font size, weight or spacing.

**What to add.** Read computed font size, weight and the space above and below for each text unit (one more `getComputedStyle` per unit), then find candidates both ways:
- **Visual-not-programmatic:** styled like a heading, short, followed by smaller text. This is ANDI's heuristic, applied to the whole page and to any element.
- **Programmatic-not-visual:** a heading styled like body text, or `display:none`-like small text.

**Mechanical outcomes.**
- **DNA** when there are no programmatic headings and no candidates on a page with text (the Applicability wording, p. 46).
- **A FAIL needs a person or a look.** A short bold line is often a lead-in, not a heading (TT Note: "heading markup should not be used for emphasis").
- **The person's question** is "does this act as a heading for the content after it?", one per candidate, with the text and a crop.

**False PASS risk.** Missed candidates; any heuristic misses some. A PASS needs the candidate search to have covered the whole page. The "no candidates found" logic decides only DNA, as above.

**Fixtures.**
- TC13.B-1.c-fail-1…4: visual heading not marked up;
- TC13.C-1-fail-1/2: a non-visual heading, menu items as headings;
- TC13.B-all-pass-1…3, and the ic-dna cases.

## 10.C Heading level (p. 47)

**What a tester does.** Compare ANDI's outline levels with the visual hierarchy. ARIA levels win over HTML (HtT 2.a). With one heading, any level is fine (HtT 3.a). The most important heading has the highest level (3.b).

**ANDI: structures module.** It builds the outline list and has three alerts:
- `alert_0191`, "Heading element level <N> conflicts with [aria-level=M]";
- `alert_0193`, a bad `aria-level`;
- `alert_0192` (caution), `role=heading` without `aria-level`.

The conflict alert fires only when the element also has a `role` attribute, because ANDI's `role` field is set only then (andi.js:2208-2219, sandi.js:54-72). So `<h2 aria-level="3">` alone gets no alert, though the outline uses 3.

**axe:** `heading-order` (best-practice, skipped levels), `page-has-heading-one` and `empty-heading`. None of them compares level with appearance.

**Our code:** heading units with level and box (the level has the gap described above).

**What to add.**
- **The exposed level:** from the accessibility tree (CDP `Accessibility.getFullAXTree`, which has `level`), or ANDI's outline.
- **Computed font size and weight per heading.**

**Mechanical outcomes.**
- **PASS when there is one heading** (HtT 3.a).
- **Inconsistencies to flag:** a higher-level heading (smaller number) rendered clearly smaller than a lower-level one in the same region. Skipped levels are not a TT failure in themselves, since the TT asks for "logically match", so a skip is at most a note.
- **The rest is a question:** does the hierarchy shown match the levels? Ask once per page, with an outline (level, text, size), not per heading.

**False PASS risk.** Size alone can mislead: a card title styled small but at a correct level. The outline question with sizes is cheap, and it is text, not a picture.

**Fixtures.** TC13.B-1.a-fail-1/2, TC13.B-1.b-fail-1, TC13.C-1-pass-1.

## 10.D List type (p. 48)

**What a tester does.** For each visible list (not navigation, unless it shows bullets or numbers), check:
- ANDI's lists output for its type (ordered, unordered, description);
- its nesting.

**ANDI: structures module, lists mode** (not the default: a button and a relaunch, sandi.js:311-318).
- **Counts:** ul, ol, dl and role=list.
- **Alerts:**
  - `alert_0079`: a list item outside a list;
  - `alert_0194`: an item whose container has an overriding role;
  - `alert_007A`: `dt`/`dd` outside `dl`.
- **It does not look for visual lists without markup.**

**axe:** `list`, `listitem`, `definition-list` and `dlitem`. These check markup validity only.

**Our code:** nothing for lists. `labels.py` reads `li` text for form components only.

**What to add.**
- **A list inventory:** type, item count, depth, box.
- **Visual-list candidates:** sibling blocks that start with a bullet glyph, "1." or "a)" (in text or `::before` content), `display:list-item` outside lists, or a `ul` styled with numbers.
  - **Number markers.** Computed `list-style-type` on `li` tells "numbered" (decimal, alpha, roman) from "bulleted". That covers the common failure, an `ul` showing numbers or an `ol` showing bullets.

**Mechanical outcomes.**
- **FAIL:** an `ol` whose items show bullets; a `ul` showing sequential numbers; text-only bullets (`•`, `-`) starting three or more sibling lines with no list markup. These are clear cases.
- **Ordered or unordered depends on meaning** ("used where sequence … is important", HtT 2). A numbered list of steps marked `ul` with CSS numbers is a FAIL. A `ul` with `list-style:none` is fine.
- **The remaining question** is whether a candidate is a list or a sentence (TT Note).

**False PASS risk.** Lists drawn with images or in a CSS grid. The candidate search should include `::before` content and repeated small images.

**Fixtures.** TC13.D-1/2/3 fail and pass cases, TC13.D-ic-dna-1.

## 13.C Contrast (p. 57)

**What a tester does.**
1. Run ANDI's contrast module and read its alerts.
2. For "manual test needed" cases (text over images, opacity) and images of text, use the Colour Contrast Analyser on the lowest-contrast pixels (HtT 3).
3. Pass when the ratio is ≥ the minimum "identified in the ANDI Contrast Ratio output" (ER 1).

**ANDI: contrast module.**
- **Data per text element:** `$(el).data("candi508")` = `{fgColor, bgColor, ratio, minReq, result, bgImage, opacity, semiTransparency, size, weight, disabled}` (candi.js:462-476).
- **Alerts:**
  - `alert_0240`, ratio below the minimum;
  - `alert_0230`, background image: manual test;
  - `alert_0232`, opacity under 100%: manual test;
  - `alert_0231` (page), images may contain text;
  - `alert_0251` (page), disabled elements are exempt.
- **Large text:** ≥ 24 px, or ≥ 18.66 px and bold (candi.js:494-497).

### Experiment: is ANDI's maths right?

**Method.** 444 colour pairs: 400 random, 4 classics (`#777`/`#fff` and others), and 40 pairs chosen with exact ratios just under 4.5 or 3.0. ANDI's contrast module ran in Chromium on a page of them. Its ratios were compared with an independent Python implementation of the WCAG 2.x formula (0.04045 threshold, unrounded). Script: the session scratchpad, `contrast/probe.py`.

**What it showed.**
- **ANDI's ratio equals the exact WCAG ratio rounded to 2 decimals on all 444 pairs** (maximum difference 0).
- **The linearisation threshold makes no difference.** ANDI uses 0.03928 (WCAG 2.0's text), not 0.04045 (2.1+), but no 8-bit channel value falls between them, so both give identical ratios on every pair. This is arithmetic, and the experiment confirms it.
- **ANDI rounds before comparing** (candi.js:938, 501). So a true ratio of 4.495-4.4999 is reported as 4.5 and PASS. Four of the 444 pairs did this: for example `rgb(227,33,100)` on white, exact 4.49896.
  - **WCAG says ratios are not rounded.** Understanding 1.4.3 uses 4.499:1 as a ratio that does *not* meet 4.5:1, and the ICT Baseline says the same.
  - **The TT says** to use "the minimum required contrast ratio identified in the ANDI Contrast Ratio output".
  - **So, for the 13.C spec:** a careful tester using ANDI would PASS these; WCAG would FAIL them. Principle 3 points to NEEDS REVIEW for an ANDI PASS whose unrounded ratio is below the minimum. It is rare: 4 of 444 random-ish pairs, and those were chosen to be near the boundary.
- **axe-core 4.14's `color-contrast` on the same 444 pairs:** no PASS below 4.5 (it compares unrounded). It marked 5 pairs with ratios of about 1.00 as "incomplete", not as violations. So axe never gave a false PASS here.

**What this means.**
- **No contrast maths needs to be written, and no model ever does arithmetic.** Read ANDI's `candi508` data (its own colours and ratio). Recompute the unrounded ratio from ANDI's own `Color` objects in the page (`fgColor.luminance`, `bgColor.luminance`) for the boundary check.
- **A test pins it.** A fixture page with the four boundary pairs and a few known ratios (`#777`/`#fff` = 4.48, `#767676`/`#fff` = 4.54), with expected values in the test file. Any future change to ANDI, Chromium or our reading of it is then caught.

**What ANDI leaves to the tester.**
- Text over background images or gradients (the walk up the page stops at the first `background-image`, which includes gradients);
- opacity;
- `text-shadow` (shown, not used);
- text positioned over other elements, since it walks DOM ancestors, not what is painted behind;
- images of text.

**Pixels for those.** From the element's screenshot crop:
- the darkest and lightest pixels of the glyphs, against the background pixels next to them;
- the same measurement a tester makes with the Colour Contrast Analyser (HtT 3.b-c: "choose a pixel that provides the least contrast").

This is mechanical, but anti-aliased glyph edges make "the text's colour" fuzzy. Rules:
- take the text colour ANDI read when it is known, and only the background from pixels;
- if the result clearly passes or clearly fails, take that outcome;
- otherwise, NEEDS REVIEW.

**False PASS risk.**
- The rounding band above.
- Background images with busy areas: take the lowest-contrast background pixel next to the text, as the TT says.
- Hover and focus states (Baseline has cases for contrast on hover and focus).

**Fixtures.** Baseline TC08.A-2-fail-1…4 (including text in an image), TC08.A-2-pass-1, TC08.A-3-fail-1/2, TC08.A-3-pass-1/2. ACT afw4f7 (12 passed, 11 failed, 11 inapplicable). DHS publishes no verdicts for 1.4.3.

## 14.A Table identification (p. 60; identify content p. 60)

**What a tester does.**
- **Identify content:** find every data table, *including images of data tables*, where cells need headers to be understood. ANDI's "reading order" helps, because a data table does not make sense read in that order (Note).
- **Then:** each data table can be reached in ANDI's tables module, has no `role=presentation`, and has no ANDI table alerts for wrong ARIA (ER 1-3).

**ANDI: tables module.**
- **Classification:** `role=presentation/none` is a presentation table; `table`, `grid` or `treegrid` (role or element) is a data table; anything else is presentation, "non-typical role" (tandi.js:101-117). **There is no data-versus-layout judgement.**
- **Alerts:**
  - `alert_0041`, "Presentation table has data table markup (…); Is this a data table?";
  - `alert_004I`, a table with a role that makes it not a data table;
  - the ARIA grid alerts `alert_004H`, `004F`, `004G`, `004J`, `004K`.

**axe:** `table-fake-caption` (experimental) and `presentation-role-conflict`. **No axe rule finds a visual table built from divs.**

**Our code:** text units with boxes include each table cell's text (site.py). There is no table inventory.

**What to add.**
- **A table inventory:** each `table` / `role=table|grid` with rows, columns, `th` count, scope and headers use, role, nesting and box.
- **The DOM grid detector** from the token-free section of the earlier note: aligned rows and columns of short text blocks outside table markup, plus `display: table|table-row|table-cell` and `grid-template-columns` on non-table elements.
- **For images:** ruling lines and OCR words in columns (section 5b of the earlier note).

**Mechanical outcomes.**
- **FAIL:** a `table` with `th` cells or a caption and `role=presentation` (this is ANDI's `alert_0041` case, made a FAIL only when header cells make it data-like: Baseline TC12.A-2-fail-1/2).
- **FAIL:** a div grid with a header row (bold or `th`-like styling) and columns of values.
- **The person's question:** for other div grids, "do these cells need their row or column headers to be understood?". That is the TT's own test for a data table, so it stays a judgment. Ask it with the reading-order text, the way ANDI shows a tester.
- **DNA** only when the page has no table markup and no grid candidates (and no images of tables).

**False PASS risk.** A detector that misses a grid gives DNA wrongly. Keep the detector broad, accept extra candidates, and let the question filter them.

**Fixtures.** TC12.A-2-fail-1/2, TC12.A-3-fail-1, TC12.A-all-pass-1. Custom pages are needed for div tables (none exist in ACT or Baseline).

## 14.B Cell header association (p. 61)

**What a tester does.** Navigate every data cell in ANDI's tables module and check that its announced headers are the relevant ones (HtT 2-3), including tables that change on interaction (Note).

**ANDI: tables module.**
- **Per cell (scope mode):** a `th` in the same column (not scope row) or in the same row (not scope col), matched by row and column index across row and col spans.
- **Per cell (headers/id mode):** the referenced cells.
- **Alerts:**
  - `alert_0046`, no `th`;
  - `alert_0048`, no scope;
  - `alert_004A/B/C`, the headers/id and scope mode mismatches;
  - `alert_0049`, both scope and headers;
  - `alert_0047`, a scope needed where row and column headers cross;
  - `alert_0062/0066/0067/0068`, wrong `headers` references;
  - `alert_0132`, an empty header cell.
- **The header text is computed only on inspect.**

**axe:** `td-headers-attr`, `th-has-data-cells` and `td-has-header` (experimental: tables larger than 3×3), all tagged TT14.b; `scope-attr-valid` and `empty-table-header` (best-practice).

**Our code:** `labels.headers()` (labels.py:84-101) handles only cells holding a form component, and ignores spans and scope.

**What to add.** The header text for every cell, computed the way ANDI does it. Two routes:
- **Script ANDI's inspect per cell.** Exact, since it is ANDI's own code, but slow on big tables.
- **Read the accessibility tree.** Chromium exposes each cell's column and row headers (CDP `Accessibility.getFullAXTree` gives `cell` nodes; their header relationships are what screen readers get). This is closer to what is announced, and fast.

  Use ANDI for cases where they disagree. ANDI is what the TT names.

**Mechanical outcomes.**
- **FAIL:** a cell with no header in a table with header cells; a cell whose header is empty or wrong by markup (the ANDI dangers above).
- **The person's question:** whether the headers given are the *relevant* ones, such as a visually second header row with no markup. Ask once per table, with a small grid of cell → headers.

**False PASS risk.** Header rows that look like headers but are `td` cells: every cell then "has headers" from the first row only. Compare styled-header rows (bold, background) with the `th` markup.

**Fixtures.** TC12.A-4-fail-1…6; ACT a25f45 and d0f69e.

## 14.C Layout table structure (p. 62)

**What a tester does.** For layout tables: no `role=table`, and no `th`, `scope`, `headers`, `caption` or `summary` (ER 3).

**ANDI.** The tables module's `alert_0041` for presentation tables with data markup, and the "Element" output.

**axe:** `presentation-role-conflict` (best-practice).

**What to add.** The table inventory from 14.A.

**Mechanical outcomes.** Once a table is known to be layout, every check is markup. That makes this the most mechanical test in the cluster. The hard part is the data-versus-layout decision, shared with 14.A.
- A table with `role=presentation`: PASS here (ER 2), and checked as data by 14.A.
- A plain `table` with no header markup that people would read as layout (one row of columns, nested page structure): a question, then mechanical.

**False PASS risk.** Low. A wrong layout call moves the case to 14.A, which asks.

**Fixtures.** No Baseline or ACT cases. Custom pages are needed.

## 15.A Content order without CSS positioning (p. 64; identify content p. 64)

**What a tester does.**
- **Identify content:** ANDI's "linearize page" setting removes CSS positioning; positioned content is highlighted in blue.
- **Then:** judge whether the reading order is still understandable (HtT 1-2). Overlap after linearizing is not a failure.

**ANDI.**
- **Linearize** (andi.js:1464-1498; andi.css:555-559) sets two classes:
  - position:static on elements positioned absolute, fixed, relative or sticky with any offset;
  - float:none on floats.

  It does **not** touch flexbox or grid `order`, grid placement, `flex-direction: row-reverse`, transforms or multi-column layout. Those reorder content visually too, and a TT tester using ANDI would not see them as "positioned with CSS".
- **The structures module's "reading order"** numbers every text node and form field in DOM order (sandi.js:669-725).

**axe and IBM:** nothing for meaningful sequence. IBM's `table_layout_linearized` covers layout tables (F49).

**Our code:**
- `site.UNITS_FN` is the DOM-order list with boxes, so it is the reading order ANDI numbers.
- `site.before` compares visual order.
- 4.F's order signals already compare focus order with visual order. The same logic, applied to all units rather than focus stops, gives "where DOM order departs from visual order".

**What to add.**
1. **The applicability check:** apply ANDI's linearize (or the same two class rules) and record which elements changed. None means **DNA**, mechanically and exactly as the TT defines it ("no content positioned using CSS").
2. **The departures:** DOM order against visual order for those elements, as 4.F does for stops.
3. **A question per departure group,** like 4.F J1: "Read in this order, does it still make sense?", with the linearized text in order. It is mostly text: the units' text in DOM order with the positioned ones marked. No picture is required, because the TT itself judges the linearized order, not the visual one.

**Scope note (principle 7).** Flex and grid reordering is outside what ANDI's linearize shows a tester. Listing it is a note for a person at most, not a FAIL.

**False PASS risk.** A positioned element whose DOM position is far from its meaning (F1: a price or label placed visually next to its item but far away in the DOM). The departures list catches it, and the question judges it.

**Fixtures.** No ACT or Baseline cases. Custom pages are needed (F1, C27).

## 18.A Resize text (p. 74)

**What a tester does.** Zoom to 200% with the browser's own zoom (HtT 1); otherwise use another non-AT mechanism (HtT 2). Pass when (ER 1-4):
- text is not clipped, cut off or covered;
- all functionality is available;
- all content is available.

**ANDI:** nothing (no zoom, no resize alerts).

**axe:** `meta-viewport` (wcag144; zoom disabled by the viewport tag) and `meta-viewport-large` (best-practice). `avoid-inline-spacing` is 1.4.12, not 1.4.4.

**ACT:** 59br37, "Zoomed text node is not clipped with CSS overflow", and b4f0c3, "Meta viewport allows for zoom". No Baseline Alignment cases.

### Experiment: real browser zoom against our half-width stand-in

The question came from Playwright issue #2497 and the `playwright-zoom` package.

**What the thread says** (read in full, 2026-11-07, except four comments hidden as off-topic):
- **Status:** opened 2020-06-08; closed "not planned" 2026-10-31, when Playwright retired its P3 label. Pavel Feldman: "This doesn't mean the request is wrong."
- **Joel Einbinder (2020):** zoom is "doable today with setting the device pixel ratio. But its not a great api"; real Chromium zoom is also remembered per origin.
- **Jeff Witt (2026-08-25):** compared the engines.
  - **Chromium:** CDP has no zoom command, only `Emulation.setPageScaleFactor` (pinch: no reflow, `innerWidth` unchanged) and `setEmulatedOSTextScale`.
  - **The stand-in:** viewport w/z × h/z at DPR × z reflows and re-evaluates media queries, but is "not identical to real zoom, e.g. scrollbar sizing".
  - **The rejected Playwright fix:** a PR using `setPageScaleFactor` was closed because "zoom and scale are not the same".
  - **Proposed fix:** a Chromium `Emulation.setPageZoomOverride` (Chromium issue 551970393).
- **Ron Au (2021):** keyboard Ctrl+ in Playwright "isn't able to emulate zoom".

**`playwright-zoom` (npm 1.1.0, MIT, 2025-04; github.com/dszendrei/playwright-zoom).** I downloaded the npm tarball and read its source.
- **How it works:**
  - A Manifest V3 Chrome extension with `tabs` permission.
  - Its service worker calls **`chrome.tabs.setZoom(tabId, zoom)`**, the browser's real zoom (the same as Ctrl+).
  - The test library launches a *persistent* Chromium context with `--load-extension` and `headless: false`.
- **Limits:**
  - Chromium only.
  - Node and `@playwright/test` only (we are Python).
  - Headed in its code.
  - **A security problem for us:** its content script runs on every http(s) page and listens to `window.postMessage`. Any page script can post `{type: "setTabZoom"}` and change the zoom, which breaks principle 5. We should not use the package. Its mechanism is fine.

**Our experiment** (2026-11-07, Linux container, Playwright 1.63 Python, Chromium `channel="chromium"`, headless). Scripts: the session scratchpad, `zoom/probe.py`, `zoom/probe3.py`.

The mechanism is ours: a two-file extension with **no content script**, only `tabs` permission. We drive it from Playwright through the extension's service worker (`context.service_workers[0].evaluate(...)` calling `chrome.tabs.setZoomSettings(tab, {scope: 'per-tab'})` then `chrome.tabs.setZoom(tab, 2.0)`), so the page cannot reach it.

| Arm | `innerWidth` | DPR | `(max-width: 800px)` media query | Grid columns | `2vw` text |
| --- | --- | --- | --- | --- | --- |
| 100%, 1280 px window | 1280 | 1 | no | 4 | 25.6 px |
| Stand-in: 640 px viewport, DPR 2 | 640 | 2 | yes | 2 | 12.8 px |
| **Real zoom 200%** (`chrome.tabs.setZoom`), 1280 px window, **headless** | 640 | 2 | yes | 2 | 12.8 px |

**Results.**
- **Real zoom works headless here.** New-headless Chromium (`channel="chromium"`, which we already use for cross-site iframes) loads the extension, and `getZoom()` returns 2.
- **The stand-in matches real zoom on everything WCAG 1.4.4 cares about** on a synthetic page and on three of our realistic budget fixtures:
  - viewport width 640 on every page;
  - DPR 2;
  - document width the same;
  - box x and width within 1 CSS px for 207 of 230 elements on the agency page, and 92 of 125 on the benefits form.
- **Not identical, and the difference is in form controls.**
  - **The cause:** native text inputs are **180×22** CSS px under real zoom and **185×21** under the stand-in. Buttons next to them shift by 5-6 px.
  - **The effect:** the 1 px height difference accumulates, so content lower on the page sits 4-14 px lower under real zoom (median 4-6 px).
  - **Why it matters:** F80 (form controls that do not resize) is about exactly these elements. A clipping check near a form control could differ between the two.
- **Per-tab zoom resets on navigation.** Set the zoom after each load (this cost me one wrong run).
- **What it costs us:**
  - **A persistent context** for the zoomed load (extensions need one). The run's HAR replay can be routed into it as into any context; *not yet tested*.
  - **Our own extension** in `third_party/` with SHA-256 hashes (two tiny files, our code).

**Recommendation for 18.A.** Use **real browser zoom through our own extension (no content script)** on the replay. That is what the TT says ("built-in browser zoom functions"), and it removes the assumption the ROADMAP flagged. Keep the half-width stand-in only as a fallback if extensions ever cannot load (it is close, except for native form controls).

**Still to check:**
- Real zoom on Windows Chrome;
- HAR replay in a persistent context;
- whether Chrome's `--load-extension` works in the hosted image (the same Chromium, so expected yes).

**What to measure at 200%,** all from the browser:
- **Clipped text (ACT 59br37, F69):** text nodes inside `overflow: hidden|clip` ancestors whose content box is smaller than the text's scroll size; `text-overflow: ellipsis` that is now active; fixed `height` with overflowing text.
- **Covered text:** `elementFromPoint` at sample points of each text box, returning a different, non-ancestor element (sticky headers count).
- **Viewport units (F94):** font sizes that did not grow (font size at 200% against 100%, in CSS px, is unchanged under zoom; text sized with `vw` shrinks, as the table shows).
- **Form controls (F80):** the box height of text inputs against their font size.
- **Functionality (ER 3):** the walk's stops at 100% against 200%. A stop that disappears with no replacement (a menu item now behind a "Menu" button is still available) needs the hamburger question; ROADMAP has the time cost.
- **Content (ER 4):** text units at 100% missing at 200% (hidden by a media query, not moved).

**Mechanical outcomes.**
- **FAIL:** zoom blocked by `meta viewport` (b4f0c3); clipped text with no way to scroll to it; text covered by a sticky element.
- **PASS:** only when every text unit and every stop is accounted for.
- **The person's question:** content gone with a possible replacement ("is this the same menu?"), with names, not pictures.

**Decisions still open (ROADMAP):** which window sizes, and whether a failure only in the smaller window is a FAIL. Neither the TT nor the ICT Baseline names a window size. WCAG Understanding 1.4.4 applies the criterion to each layout variation.

## 7.E Images of text (p. 38; identify content p. 37)

**What a tester does.**
- **Identify content:** find images of text, leaving out text inside pictures that carry other significant content (CAPTCHA, graphs, screenshots, diagrams).
- **For each one:** could real text give the same effect (logotypes and branding cannot be replaced)? Can it be customised (HtT 1-2)?

**ANDI: graphics module.**
- **Images:** `img`, `input[type=image]`, `svg`, `canvas`, `role=img`.
- **Decorative:** `aria-hidden`, presentation roles or empty `alt`.
- **Alt-text alerts:**
  - `alert_0174`, a redundant phrase;
  - `alert_0175`, the file name;
  - `alert_0176`, not descriptive.
- **Background images:** marked, with a page-level caution only (`alert_0177`).
- **Font icons:** detected (`alert_0179`).
- **Nothing detects images of text.** The contrast module only cautions "Page has images; if images contain meaningful text, perform manual contrast test" (`alert_0231`).

**axe:** the alt rules (`image-alt` and others, tagged TT7.a), not 1.4.5.

**ACT:** 0va7u6, "HTML images contain no text". DHS verdicts exist: they agree on 11 cases and call 4 of ACT's "passed" cases *inapplicable*.

**Our code.**
- The image bytes are in the HAR (`capture.media_body`).
- `motion.py` already sniffs image types and decodes animated images in a tool page.
- Units do not include images without alt, backgrounds, `svg` or `canvas`.

**What to add.**
- **An image inventory:** element, box, source URL, alt or name, nearby text, decorative or not, background or not.
- **OCR on the recorded bytes:** tesseract.js in the browser, or Tesseract or RapidOCR on the server.
- **The comparison by rule** (section 5b of the earlier note).

**Mechanical outcomes.**
- **DNA** when the page has no images larger than icon size.
- **Logo signals** (in the header, links home, alt holds the site name, file name "logo") mark *likely logotype* for the person's question.
- **The question:** for an image whose OCR finds words, "is this a logotype or brand text, a picture where the text is minor, or text that could be real text?". Ask once per image hash per site.
- **No text found by OCR is not DNA** when there are content images: OCR misses stylised text. The result is NEEDS REVIEW, with the images listed. This is where answer-once-per-site saves the most.

**False PASS risk.** OCR misses (script fonts, text over photos), and banner images that are mostly text but artistic. Never infer "no images of text" from OCR silence alone.

**Fixtures.** Baseline TC06.D-1-fail-1, TC06.D-ic-dna-1; ACT 0va7u6 (15 cases with DHS verdicts).

## Summary: where each test's evidence comes from

| Test | ANDI module (launch needed) | axe rules | Our code to reuse | New evidence | Left for a person or model |
| --- | --- | --- | --- | --- | --- |
| 10.B | structures (headings), `alert_0190` (limited) | `p-as-heading` (experimental) | site units, boxes | computed font size, weight, spacing per text unit | "does this act as a heading?" per candidate |
| 10.C | structures, `alert_0191-0193`, outline | `heading-order` (best practice) | heading units (fix `aria-level`) | exposed level (AX tree), sizes | one outline question per page |
| 10.D | structures (lists mode) | `list`, `listitem`, `definition-list`, `dlitem` | none | list inventory, glyph and `list-style-type` candidates | "list or sentence?" |
| 13.C | contrast (`candi508`) | `color-contrast` (TT13.c) | screenshots, Pillow | read ANDI's data; unrounded check; pixel sampling for images and gradients | unclear pixel cases only |
| 14.A | tables, `alert_0041`, `004I` | none for div tables | text units with boxes | table inventory, DOM grid detector | "do cells need headers?" |
| 14.B | tables (header text on inspect) | `td-headers-attr`, `th-has-data-cells`, `td-has-header` (TT14.b) | `labels.headers` (form cells only) | headers for every cell (AX tree or ANDI inspect) | "are these the relevant headers?" per table |
| 14.C | tables, `alert_0041` | `presentation-role-conflict` | none | table inventory | data vs layout (shared with 14.A) |
| 15.A | linearize (andi.js), reading order (structures) | none | site units, `site.before`, 4.F's order signals | linearize diff (applicability), departures | "does the order still make sense?" (text) |
| 18.A | none | `meta-viewport` | walk stops, units, screenshots | real zoom via our extension; clipping, covering, viewport-unit and form-control checks | "is this the same function?" |
| 7.E | graphics (inventory, no text detection) | alt rules only | HAR image bytes, motion's image decoding | image inventory, OCR, alt comparison | "logo, minor text, or replaceable text?" (once per image per site) |

## Verified vs assumed

**Verified (command or experiment, this session):**
- ANDI facts from reading `third_party/andi/*.js`, with line numbers.
- Our code facts from reading `src/tobi508/`.
- axe-core 4.14.0's rule list and TT tags (`axe.getRules()` in Chromium).
- The contrast comparison: ANDI and axe against exact WCAG maths, 444 pairs.
- The zoom comparison: real `chrome.tabs.setZoom` against the stand-in, in headless Chromium on Linux, one synthetic page plus three budget fixtures.
- `playwright-zoom`'s mechanism, from its npm tarball.
- The issue #2497 thread, read in full, apart from four comments hidden as off-topic.

**Assumed, not tested:**
- HAR replay in a persistent context;
- real zoom on Windows Chrome;
- CDP's AX tree giving every cell's headers as screen readers get them;
- the font-size candidate heuristics for 10.B and 10.D;
- OCR quality on real agency images.
