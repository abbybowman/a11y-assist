# Trusted Tester 5.1.3: scanner coverage, ANDI use and automation ranking

Research prepared 2026-10-31 for choosing which TT tests to build next;
condensed into one table and the build status updated 2026-11-05. It is
research, not an authority: the TT PDF (`docs/sources/`) is the authority,
and each test's names, conditions and WCAG/508 mapping are read from
`docs/sources/tt-5.1.3/tt.json` (Appendix A), never from this file. Human
time and judgment ratings are estimates from the How-to-Test steps and still
need checking with certified Trusted Testers.

**Bottom line.** Of the 60 active TT test conditions, standard scanners
reliably cover 3, partly cover 21 (they catch the obvious failure; a person
still makes the call), and give no meaningful coverage to 36. The best
automation targets are the keyboard and focus tests, multi-page consistency,
and the visual-versus-code comparisons: slow and repetitive for people,
mechanical steps, and no scanner touches them. ANDI's output is the core
evidence for 20 tests, mostly the visual-versus-code ones.

**Built (2026-11-05): 21 tests.** The keyboard and focus group (4.A–4.F),
the forms group (5.A–5.D, 5.F–5.H), multi-page (9.A–9.C, 19.A) and motion
(2.A–2.D). 3.A has a draft spec (0.1.0). Status here is a convenience; the
source of truth is `checks.REGISTRY` and each spec's `spec_version`.

## What to build next

Unbuilt tests, best automation targets first (tier and rank from the table
below). **ER 3** marks the tests 2.A–2.C need before a working mechanism can
PASS (2c-auto-updating.md section 3c): each one built also unlocks PASS
there.

| Order | Test | Time / judgment | Approach | ANDI |
| --- | --- | --- | --- | --- |
| Tier 1, #9 | 18.A Resize text (ER 3) | M / L | Zoom to 200%; clipped, overlapping or lost content. | none |
| Tier 1, #14 | 10.B, 10.C Headings vs presentation | M / M | Computed styles against heading markup and levels. | Core |
| Tier 1, #15 | 10.D List type | M / M | Visual bullets or numbers without list markup. | Inventory |
| Tier 1, #16 | 14.A–14.C Tables | M/H / M | Visual grids, header associations, layout tables. | Core |
| Tier 1, #17 | 13.C Contrast leftovers (ER 3) | M / L | Text over images and gradients (axe's "needs review"). | Core |
| Tier 1, #18 | 15.A Order without CSS | M / M | Linearize; compare content order to visual order. | Core |
| Tier 1, #19 | 3.A Flashing (detection) | L/M / L | Frame capture can confirm DOES NOT APPLY; can reuse pass T's frames. Spec 0.1.0, research done. | none |
| Tier 2 | 11.B, 12.D (ER 3), 8.A, 17.D–17.G | | Language of parts; iframe name wording; timing adjustable (waiting out timeouts); media player controls. | |
| Tier 3 | 6.A (ER 3), 7.A (ER 3), 7.B–7.E (7.E: ER 3), 10.A, 12.B, 13.A (ER 3), 13.B (ER 3) | | Judgment-heavy, quick for people. 7.A is excluded for now (alt-text equivalence is high-judgment and models get it wrong). | |

Most of what is left in tier 1 is the visual-versus-code cluster (10.B–10.D,
14.x, 15.A, 18.A): screenshots and computed styles compared with ANDI's
programmatic view. That needs ANDI's per-element data beyond forms
(`andi.andi_output`, built for 5.C; ROADMAP "ANDI per-element data").

## Every test in one table

TT order. **Tier**: 1 = mechanical, time-consuming, no scanner coverage
(ranked: high time and low judgment first; for partial tests, the part
scanners miss is what is ranked); 2 = mechanical core with real judgment,
or practical risks; 3 = judgment-heavy, quick for people (the hypothesis
test, not the time saver); 4 = out of scope for now; Scanners = the
reliable three, left to scanners. **Scanners**: coverage rating (below),
then the rules that give it; an empty rule cell means none, and "notice
only" or "warnings only" means HTMLCS only reminds a person. **ANDI**: how
the 5.1.3 How-to-Test steps use it (34 of 60 tests): *Core*, its output is
the evidence; *Inventory*, it finds the items and the test is something
else; *Hint*, optional help.

| Test | Name | Status | Tier | Time / judgment | Scanners | axe-core rules | HTMLCS (pa11y) errors | ANDI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.A | Alt version conformant |  | 4 (out of scope) |  | None |  |  |  |
| 1.B | Alt version equivalent |  | 4 (out of scope) |  | None |  |  |  |
| 1.C | Alt version access |  | 4 (out of scope) |  | None |  |  |  |
| 1.D | Non interference |  | 4 (out of scope) |  | None |  |  |  |
| 2.A | Audio control | **built** | 1 (#13) | L/M / L | Partial | no-autoplay-audio | notice only |  |
| 2.B | Blinking moving scrolling | **built** | 1 (#12) | M / L/M | Partial | blink, marquee | blink element |  |
| 2.C | Auto updating | **built** | 1 (#12) | M / L/M | None |  |  |  |
| 2.D | Change notify auto | **built** | 1 (#11) | M / L | None |  |  | Inventory (live regions) |
| 3.A | Flashing | spec 0.1.0 | 1 (#19) | L/M / L | None |  | notice only |  |
| 4.A | Keyboard access | **built** | 1 (#2) | H / L | Partial | scrollable-region-focusable, frame-focusable-content, server-side-image-map | warnings only | Inventory (focusable elements) |
| 4.B | No keystroke timing | **built** | 2 |  | None |  |  |  |
| 4.C | No keyboard trap | **built** | 1 (#1) | H / L | None |  | warning only |  |
| 4.D | Focus visible | **built** | 1 (#3) | H / L/M | None |  | notice only |  |
| 4.E | On focus | **built** | 1 (#4) | M / L | None |  | notice only |  |
| 4.F | Focus order meaning | **built** | 1 (#6) | H / M | None | tabindex (best-practice hint) | notice only | Hint (tab order; can differ from real keyboard order) |
| 5.A | Label provided | **built** | 2 |  | Partial | form-field-multiple-labels; label (programmatic, not visual) | notice only | Inventory (form fields) |
| 5.B | Label descriptive | **built** | 3 |  | None |  | notice only | Inventory (form fields) |
| 5.C | Programmatic label | **built** | 2 |  | Partial | label, aria-input-field-name, select-name, aria-toggle-field-name | missing-label errors | Core (focusable elements) |
| 5.D | On input | **built** | 1 (#5) | M / L | None |  | form with no submit button (tangential) | Inventory (form fields) |
| 5.F | Error identification | **built** | 2 |  | None |  | notice only | Inventory (form fields) |
| 5.G | Error suggestion | **built** | 2 |  | None |  | notice only | Inventory (form fields) |
| 5.H | Error prevention | **built** | 3 |  | None |  | notice only | Inventory (form fields) |
| 6.A | Link purpose |  | 3 |  | Partial | link-name, area-alt | empty link name | Core (links/buttons) |
| 7.A | Meaningful image name |  | 3 (excluded for now) |  | Partial | image-alt, role-img-alt, svg-img-alt, input-image-alt, object-alt | missing-alt errors | Core (graphics/images) |
| 7.B | Decorative image |  | 3 |  | Partial | presentation-role-conflict, image-redundant-alt (best-practice hints) | some alt checks | Core (graphics/images) |
| 7.C | Decorative background image |  | 3 |  | None |  |  | Core (graphics/images, find background) |
| 7.D | Captcha alternative |  | 3 |  | None |  | notice only | Core (graphics/images) |
| 7.E | Image of text |  | 3 |  | None |  | notice only | Inventory (images) |
| 8.A | Timing adjustable |  | 2 |  | Partial | meta-refresh | meta-refresh errors |  |
| 9.A | Bypass function | **built** | 1 (#10) | L/M / L | Partial | bypass (a mechanism exists, not that it works) | broken skip-link target errors | Inventory (focusable elements, links list) |
| 9.B | Consistent navigation | **built** | 1 (#7) | H / L | None |  | notice only | Hint (tab order, reading order) |
| 9.C | Consistent identification | **built** | 1 (#8) | H / L/M | None |  | notice only | Core (focusable elements, across pages) |
| 10.A | Heading purpose |  | 3 |  | None | empty-heading (hint) | notice only | Inventory (headings) |
| 10.B | Heading determinable |  | 1 (#14) | M / M | Partial | p-as-heading (experimental) | heading-like markup warnings only | Core (structures: headings) |
| 10.C | Heading level |  | 1 (#14) | M / M | None | heading-order (hint) |  | Core (structures: headings) |
| 10.D | List type |  | 1 (#15) | M / M | Partial | list, listitem, definition-list, dlitem | list markup errors | Inventory (lists, programmatic side only) |
| 11.A | Page language defined |  | Scanners |  | **Reliable** | html-has-lang, html-lang-valid, html-xml-lang-mismatch | missing/invalid lang errors | Core (structures: lang) |
| 11.B | Part language defined |  | 2 |  | Partial | valid-lang (values only) | invalid lang errors | Core (structures: lang) |
| 12.A | Page title defined |  | Scanners |  | **Reliable** | document-title | missing/empty title errors | Core (structures: page title) |
| 12.B | Page title purpose |  | 3 |  | None |  | notice only | Core (structures: page title) |
| 12.C | Frame title |  | Scanners |  | **Reliable** (presence; frames are rare) | frame-title, frame-title-unique | frame title errors | Core (frames) |
| 12.D | Iframe name |  | 2 |  | Partial | frame-title, frame-title-unique | iframe title errors | Core (iframes) |
| 13.A | Color meaning |  | 3 |  | Partial | link-in-text-block | notice only |  |
| 13.B | Sensory info |  | 3 |  | None |  | notice only |  |
| 13.C | Contrast |  | 1 (#17) | M / L | Partial (strong for plain text; text over images and gradients is "needs review") | color-contrast | contrast errors | Core (color contrast) |
| 14.A | Table identification |  | 1 (#16) | M/H / M | None | (cannot see a visual table built from divs) |  | Core (tables) |
| 14.B | Cell header association |  | 1 (#16) | M/H / M | Partial | td-headers-attr, th-has-data-cells, td-has-header (experimental) | header association errors | Core (tables) |
| 14.C | Layout table structure |  | 1 (#16) | M/H / M | Partial |  | layout table with header markup | Core (tables) |
| 15.A | Content order meaning css position |  | 1 (#18) | M / M | None |  | notice only | Core (linearize page) |
| 16.A | Audio transcript text |  | 4 (out of scope) |  | Partial | audio-caption (presence only) | notice only |  |
| 16.B | Video alternative equivalent |  | 4 (out of scope) |  | None |  | notice only |  |
| 17.A | Captions equivalent |  | 4 (out of scope) |  | Partial | video-caption (track presence only) | notice only |  |
| 17.B | Audio description equivalent |  | 4 (out of scope) |  | None |  |  |  |
| 17.C | Captions live equivalent |  | 4 (out of scope) |  | None |  |  |  |
| 17.D | Caption controls |  | 2 |  | None |  |  |  |
| 17.E | Description controls |  | 2 |  | None |  |  |  |
| 17.F | Caption control level |  | 2 |  | None |  |  |  |
| 17.G | Description control level |  | 2 |  | None |  |  |  |
| 18.A | Resize text |  | 1 (#9) | M / L | Partial | meta-viewport (only blocked zoom) | notice only |  |
| 19.A | Multiple ways | **built** | 2 |  | None |  | notice only |  |

## Notes on the tiers

- **Tier 2 risks.** 5.F and 5.G submit bad data, and a recorded replay never
  reaches a real server, so evidence of server-side errors is missing (5.F
  A4, built).
- **Tier 4.** 1.A–1.D alternate versions are a scoping decision, not a page
  test (1.D rolls up 2.A, 2.B, 2.C, 3.A, 4.C). 16.A, 16.B and 17.A–17.C are
  media accuracy (17.A caption accuracy could later use speech-to-text).
- **Excluded or special.** 5.E is obsolete (no longer required as of ICT
  Testing Baseline 3.1); 6.B is removed; 20.A is always NOT TESTED (WCAG 2.2
  made 4.1.1 obsolete); 3.A gives only DOES NOT APPLY (no flashing) or NOT
  TESTED (flashing found), never PASS or FAIL.

## ANDI and the build

- **ANDI and the behavioral tests barely overlap.** The keyboard, timing and
  zoom tests need something that presses keys, waits and watches; that is
  the walk and its replays. Where ANDI is only an inventory (4.A, 5.x, 9.A),
  the walk's stops and the DOM inventory serve, from real key presses.
- **ANDI is the head start for visual versus code** (headings, tables,
  reading order, contrast leftovers). andi-cli extracts alerts only; the
  per-element data comes from `andi.andi_output`. Which modules exist and what we read from them: [ANDI modules as vendored](#andi-modules-as-vendored-added-2026-11-07) below.
- **Scanners own the 3 reliable tests and the scanned half of the 21
  partial ones,** imported as evidence, never as a PASS on their own (not
  vendored yet; ROADMAP "Scanners"). Coverage ratings reflect default
  configurations; enabling pa11y warnings and notices adds reminders, not
  checks.

## ANDI modules as vendored (added 2026-11-07)

The ANDI column above says how the TT's How-to-Test steps use ANDI. This section says what each module of the vendored ANDI 29.2.2 actually outputs, and how much of it we read today. Facts are from reading `third_party/andi/*.js` and `src/tobi508/andi.py`. Per-test detail, with file and line references, is in [2026-11-07-visual-cluster-per-test.md](2026-11-07-visual-cluster-per-test.md).

**What we run today.** Only the default module, focusable elements (`f`). `andi.inject_andi` loads `andi.js`, which launches `f` (andi.js:45, 132). Nothing launches the other modules, though our route serves them from local files (andi.py:43-55), so `AndiModule.launchModule("<letter>")` works offline.

**What we read today.** `andi.andi_output` returns each analysed element's name, description, group label, dangers and warnings (andi.py:88-125). Used by 5.A/5.C (pass L) and 9.C. It does not read:
- cautions;
- module-specific data (the contrast module's `candi508`, the tables module's `data-tandi508-*` cell indexes);
- page-level alerts, which go only to ANDI's alert list (andi.js:3691-3698).

| Module | Letter | TT tests that name it | What it gives | Limits found |
| --- | --- | --- | --- | --- |
| Focusable elements | f | 4.x (hint), 5.C core, 9.C core | names, descriptions, group labels, alerts per focusable element | the only module we run |
| Graphics/images | g | 7.A-7.E | images (`img`, `svg`, `canvas`, `role=img`); decorative or not; alt-text alerts (redundant phrase, file name, not descriptive); background images marked; font icons | no image-of-text detection; background images get a page-level caution only, not per-element data; gradients are not counted |
| Links/buttons | l | 6.A | link and button names and purpose alerts | not surveyed in detail (6.A not in this cluster) |
| Tables | t | 14.A-14.C | data vs presentation **by markup only** (no layout judgement); cell indexes with spans; scope and headers/id modes; about 20 table alerts | one table per launch; a cell's header text is computed only when the cell is inspected |
| Structures | s | 10.A-10.D, 11.A/B, 12.A, 15.A (reading order) | headings list and outline levels; lists mode (counts, list-item alerts); landmarks; language; page title; "reading order" numbering | fake-heading check only before the first real heading; the aria-level conflict alert needs a `role` attribute too; lists mode needs a relaunch; no visual-list detection |
| Color contrast | c | 13.C | per text element: colours, ratio, minimum, PASS/FAIL or manual test needed; disabled elements exempt | **rounds the ratio to 2 decimals before comparing** (4.495-4.499 passes; WCAG says do not round); a background image or gradient or opacity means manual test; positioned text and text-shadow not handled |
| Hidden content | h | (CSS content, hidden text) | hidden and CSS-generated content | not surveyed in detail |
| Iframes | i | 12.C, 12.D | iframe titles | not surveyed in detail |
| Linearize (setting in `andi.js`) | | 15.A | removes CSS positioning: absolute, fixed, relative and sticky positioning with an offset, and floats (andi.js:1464-1498) | does not undo flexbox or grid reordering, transforms or multi-column layout |

**Checked against independent maths.** On 444 colour pairs, the contrast module's ratios equal the exact WCAG 2 ratio rounded to 2 decimals (2026-11-07; the per-test note, 13.C).

## Tools, versions and ratings

- **axe-core 4.14.0:** rule list and WCAG tags read from the library
  (`axe.getRules()`).
- **pa11y 10.0.0:** default runner HTML_CodeSniffer (HTMLCS) 2.5.1, standard
  WCAG2AA, `includeWarnings: false`, `includeNotices: false`, so by default it
  reports HTMLCS errors only. Sniffs that only raise notices (manual-check
  reminders) count as no coverage. pa11y's optional axe runner adds nothing
  beyond the axe column.
- Coverage is per test condition, not per WCAG criterion (4.1.2 alone spans
  many tests). axe "needs review" (incomplete) results are not coverage.

**Ratings.** *Reliable:* a rule checks the condition directly with few false
positives. *Partial:* a rule catches some failure modes (usually something
missing), but the real question (equivalent, descriptive, visible, logical)
still needs a person. *None:* no rule meaningfully tests it; rules not
tagged to a WCAG criterion are noted as hints, not coverage.

## Licenses

The licenses cover the code, not its output; scan results are our data.

| Tool | Version | License | For us |
| --- | --- | --- | --- |
| ANDI (SSA) | 29.2.2 vendored | Apache 2.0 | Run, modify, redistribute; keep LICENSE and NOTICE, credit SSA |
| axe-core | 4.14.0 | MPL 2.0 | Unmodified (or via @axe-core/playwright, also MPL 2.0) places no terms on our code; changed axe files stay MPL and must be shared |
| HTML_CodeSniffer | 2.5.1 | BSD 3-Clause | Keep the copyright notice; no endorsement by the authors' names |
| pa11y | 10.0.0 | LGPL 3.0 only | Fine as an unmodified dependency; changes to pa11y stay LGPL |

**Recommendation.** pa11y launches its own browser through Puppeteer. Load
the engines into our own Playwright page instead: axe (MPL) and HTMLCS
(BSD, the engine pa11y runs by default) on their own fresh load after the
walk ([solutions/scanners-after-the-walk.md](../solutions/scanners-after-the-walk.md)).
Same results as pa11y, one browser, the most permissive licenses. Not legal
advice: NASA's software release process reviews the dependency list before
open sourcing.
