# Trusted Tester 5.1.3: scanner coverage, ANDI use and automation ranking

Research prepared 2026-10-31 for choosing which TT tests to build next.
Added to the repo 2026-11-01. It is research, not an authority: the TT PDF
(`docs/sources/`) is the authority, and each test's names, conditions and
WCAG/508 mapping are read from `docs/sources/tt-5.1.3/tt.json` (Appendix A),
never from this file. Human time and judgment ratings are estimates from the
How-to-Test steps and still need checking with certified Trusted Testers.

**Bottom line.** Of the 60 active TT test conditions, standard scanners
reliably cover 3, partly cover 21 (they catch the obvious failure; a person
still makes the call), and give no meaningful coverage to 36. The best
automation targets are the keyboard and focus tests, multi-page consistency,
and the visual-versus-code comparisons: slow and repetitive for people,
mechanical steps, and no scanner touches them. ANDI's output is the core
evidence for 20 tests, mostly the visual-versus-code ones.

## Tools and versions

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

## Excluded or special tests

| Test | Status in 5.1.3 |
| --- | --- |
| 5.E | Removed (no longer required as of ICT Testing Baseline 3.1) |
| 6.B | Removed |
| 20.A | Always NOT TESTED (WCAG 2.2 made 4.1.1 obsolete) |
| 3.A | Only DOES NOT APPLY (no flashing) or NOT TESTED (flashing found); never PASS or FAIL |

## Coverage by test

| Coverage | Count | Tests |
| --- | --- | --- |
| Reliable | 3 | 11.A, 12.A, 12.C |
| Partial | 21 | 2.A, 2.B, 4.A, 5.A, 5.C, 6.A, 7.A, 7.B, 8.A, 9.A, 10.B, 10.D, 11.B, 12.D, 13.A, 13.C, 14.B, 14.C, 16.A, 17.A, 18.A |
| None | 36 | 1.A, 1.B, 1.C, 1.D, 2.C, 2.D, 3.A, 4.B, 4.C, 4.D, 4.E, 4.F, 5.B, 5.D, 5.F, 5.G, 5.H, 7.C, 7.D, 7.E, 9.B, 9.C, 10.A, 10.C, 12.B, 13.B, 14.A, 15.A, 16.B, 17.B, 17.C, 17.D, 17.E, 17.F, 17.G, 19.A |

Rules per test (the WCAG/508 column of the original is left out: read it
from `tt.json`):

| Test | axe-core 4.14.0 rules | pa11y (HTMLCS errors) | Coverage |
| --- | --- | --- | --- |
| 1.A–1.D | none | none | None |
| 2.A | no-autoplay-audio | none (notice only) | Partial |
| 2.B | blink, marquee | blink element | Partial |
| 2.C | none | none | None |
| 2.D | none | none | None |
| 3.A | none | none (notice only) | None |
| 4.A | scrollable-region-focusable, frame-focusable-content, server-side-image-map | none (warnings only) | Partial |
| 4.B | none | none | None |
| 4.C | none | none (warning only) | None |
| 4.D | none | none (notice only) | None |
| 4.E | none | none (notice only) | None |
| 4.F | none (tabindex is a best-practice hint) | none (notice only) | None |
| 5.A | form-field-multiple-labels; label (programmatic, not visual, label) | none (notice only) | Partial |
| 5.B | none | none (notice only) | None |
| 5.C | label, aria-input-field-name, select-name, aria-toggle-field-name | missing-label errors | Partial |
| 5.D | none | form with no submit button (tangential) | None |
| 5.F, 5.G, 5.H | none | none (notice only) | None |
| 6.A | link-name, area-alt | empty link name | Partial |
| 7.A | image-alt, role-img-alt, svg-img-alt, input-image-alt, object-alt | missing-alt errors | Partial |
| 7.B | presentation-role-conflict, image-redundant-alt (best-practice hints) | some alt checks | Partial |
| 7.C, 7.D, 7.E | none | none (7.D, 7.E notice only) | None |
| 8.A | meta-refresh | meta-refresh errors | Partial |
| 9.A | bypass (a mechanism exists, not that it works) | broken skip-link target errors | Partial |
| 9.B, 9.C | none | none (notice only) | None |
| 10.A | none (empty-heading is a hint) | none (notice only) | None |
| 10.B | p-as-heading (experimental) | heading-like markup warnings only | Partial |
| 10.C | none (heading-order is a hint) | none | None |
| 10.D | list, listitem, definition-list, dlitem | list markup errors | Partial |
| 11.A | html-has-lang, html-lang-valid, html-xml-lang-mismatch | missing/invalid lang errors | **Reliable** |
| 11.B | valid-lang (values only) | invalid lang errors | Partial |
| 12.A | document-title | missing/empty title errors | **Reliable** |
| 12.B | none | none (notice only) | None |
| 12.C | frame-title, frame-title-unique | frame title errors | **Reliable** (presence; frames are rare) |
| 12.D | frame-title, frame-title-unique | iframe title errors | Partial |
| 13.A | link-in-text-block | none (notice only) | Partial |
| 13.B | none | none (notice only) | None |
| 13.C | color-contrast | contrast errors | Partial (strong for plain text; text over images and gradients is "needs review") |
| 14.A | none (cannot see a visual table built from divs) | none | None |
| 14.B | td-headers-attr, th-has-data-cells, td-has-header (experimental) | header association errors | Partial |
| 14.C | none | layout table with header markup | Partial |
| 15.A | none | none (notice only) | None |
| 16.A | audio-caption (presence only) | none (notice only) | Partial |
| 16.B | none | none (notice only) | None |
| 17.A | video-caption (track presence only) | none (notice only) | Partial |
| 17.B–17.G | none | none | None |
| 18.A | meta-viewport (only blocked zoom) | none (notice only) | Partial |
| 19.A | none | none (notice only) | None |

## Automation ranking

Human time and judgment are L/M/H estimates; high time and low judgment rank
first. For partial tests, what is ranked is the part scanners miss.

**Tier 1: mechanical, time-consuming, no scanner coverage.**

| Rank | Test | Time | Judgment | Approach |
| --- | --- | --- | --- | --- |
| 1 | 4.C No keyboard trap | H | L | Tab and Shift+Tab through everything; can focus leave. **Built.** |
| 2 | 4.A Keyboard access | H | L | Every mouse-operable control reached and operated by keyboard. **Built.** |
| 3 | 4.D Focus visible | H | L/M | Before/after images per stop. **Built.** |
| 4 | 4.E On focus | M | L | Watch for URL change, new window, focus moving. **Built.** |
| 5 | 5.D On input | M | L | Change each field; watch for the same context-change signals. |
| 6 | 4.F Focus order | H | M | Focus sequence against layout; modal containment. **Built.** |
| 7 | 9.B Consistent navigation | H | L | Order of repeated navigation across pages. |
| 8 | 9.C Consistent identification | H | L/M | Same-function components across pages, compare names. |
| 9 | 18.A Resize text | M | L | Zoom to 200%; clipped, overlapping or lost content. |
| 10 | 9.A Bypass | L/M | L | Activate the skip link; does focus land past the repeated block. |
| 11 | 2.D Change notify (auto) | M | L | Mutations over time; are changes announced. |
| 12 | 2.B / 2.C Moving and auto-updating | M | L/M | Motion and updates over time; a working pause or stop. |
| 13 | 2.A Audio control | L/M | L | Audio past 3 s on load; a keyboard pause or volume control. |
| 14 | 10.B / 10.C Headings vs presentation | M | M | Computed styles against heading markup and levels. |
| 15 | 10.D List type | M | M | Visual bullets or numbers without list markup. |
| 16 | 14.A–14.C Tables | M/H | M | Visual grids, header associations, layout tables. |
| 17 | 13.C Contrast leftovers | M | L | Text over images and gradients (axe's "needs review"). |
| 18 | 15.A Order without CSS | M | M | Linearize; compare content order to visual order. |
| 19 | 3.A Flashing (detection) | L/M | L | Frame capture can confirm DOES NOT APPLY. |

**Tier 2: mechanical core with real judgment, or practical risks.**
5.F / 5.G error identification and suggestion (submitting bad data; a
recorded replay never reaches a real server, but evidence of server-side
errors is then missing), 5.C and 5.A leftovers (visible instructions against
accessible names), 11.B language of parts, 19.A multiple ways, 12.D iframe
name wording, 8.A timing adjustable (waiting out timeouts), 4.B keystroke
timing (**built**), 17.D–17.G media player controls.

**Tier 3: judgment-heavy, quick for people** (the hypothesis test, not the
time saver): 6.A link purpose, 10.A heading purpose, 12.B page title, 5.B
label descriptive, 13.A color meaning, 13.B sensory information, 7.B / 7.C
decorative images, 7.E image of text, 7.D CAPTCHA, 5.H error prevention, 7.A
meaningful image name (excluded for now: alt-text equivalence is
high-judgment and models get it wrong).

**Tier 4: out of scope for now.** 1.A–1.D alternate versions (a scoping
decision, not a page test; 1.D rolls up 2.A, 2.B, 2.C, 3.A, 4.C). 16.A,
16.B, 17.A–17.C media accuracy (17.A caption accuracy could later use
speech-to-text).

## ANDI in the How-to-Test steps

The 5.1.3 steps name an ANDI module for 34 of the 60 active tests.

| Level | Count | Tests (ANDI module) |
| --- | --- | --- |
| Core: ANDI's output is the evidence | 20 | 5.C (focusable elements); 6.A (links/buttons); 7.A–7.D (graphics/images, incl. "find background"); 9.C (focusable elements, compared across pages); 10.B, 10.C (structures: headings); 11.A, 11.B, 12.A, 12.B (structures: lang, page title); 12.C (frames); 12.D (iframes); 13.C (color contrast); 14.A–14.C (tables); 15.A ("linearize page", reading order) |
| Inventory: ANDI finds the items, the test is something else | 12 | 2.D (live regions); 4.A (focusable elements); 5.A, 5.B, 5.D, 5.F, 5.G, 5.H (form fields); 7.E (images); 9.A (focusable elements, links list for skip links); 10.A (headings); 10.D (lists, programmatic side only: the PDF says to identify lists visually) |
| Hint: optional help | 2 | 4.F (tab order; the PDF warns it can differ from real keyboard order); 9.B (tab order, reading order) |
| None | 26 | 1.A–1.D, 2.A–2.C, 3.A, 4.B–4.E, 8.A, 13.A, 13.B, 16.A, 16.B, 17.A–17.G, 18.A, 19.A |

What this means for the build:

- **ANDI and the behavioral tests barely overlap.** The keyboard, timing and
  zoom tests need something that presses keys, waits and watches; that is
  the walk and its replays. Where ANDI is only an inventory (4.A, 5.x, 9.A),
  the walk's stops and the DOM inventory serve, from real key presses.
- **ANDI is the head start for visual versus code** (headings, tables,
  reading order, contrast leftovers): screenshots and computed styles
  compared with ANDI's programmatic view. That needs ANDI's per-element data,
  not only its alerts (andi-cli extracts alerts only): the roadmap's ANDI
  spike.

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

## Takeaways

- The keyboard and focus group took ranks 1 to 6 with 5.D: no scanner
  coverage, high human time, mostly binary outcomes. Built.
- Next natural groups: 5.D and 9.A (single page, reuse the walk and 4.A's
  and 4.E's observers); multi-page 9.B and 9.C; then visual versus code
  (10.B–10.D, 14.x, 15.A, 18.A), after the ANDI spike.
- Let scanners own the 3 reliable tests and the scanned half of the 21
  partial ones; import their results as evidence, never as a PASS on their
  own.
- Coverage ratings reflect default configurations; enabling pa11y warnings
  and notices adds reminders, not checks.
