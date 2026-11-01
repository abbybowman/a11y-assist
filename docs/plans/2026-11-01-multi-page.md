# Plan: multi-page tests (9.A, 9.B, 9.C) (2026-11-01, not started)

A later batch. These tests need to know what repeats across a site's pages,
which one page cannot show, and page content must never choose a URL to
visit (CLAUDE.md principle 5). Build them together, after the form tests,
around one new piece: a way to test several pages of a site in one run.
9.A comes first; 9.B (consistent navigation) and 9.C (consistent
identification) are researched and planned here when the batch starts,
following CLAUDE.md's research rule (TT text, W3C Understanding and
techniques, ACT and DHS, the ICT Testing Baseline and its Baseline Alignment
cases).

## Sources read for 9.A (2026-11-01)

| Source | 9.A (2.4.1) |
| --- | --- |
| TT 5.1.3 | pp. 42–43 |
| W3C Understanding | [Bypass Blocks](https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html) |
| W3C techniques | [G1](https://www.w3.org/WAI/WCAG22/Techniques/general/G1), [G123](https://www.w3.org/WAI/WCAG22/Techniques/general/G123), [G124](https://www.w3.org/WAI/WCAG22/Techniques/general/G124), [ARIA11](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA11), [H69](https://www.w3.org/WAI/WCAG22/Techniques/html/H69), [H64](https://www.w3.org/WAI/WCAG22/Techniques/html/H64) |
| W3C ACT | [cf77f2](https://www.w3.org/WAI/standards-guidelines/act/rules/cf77f2/), a composite of 3e12e1 (collapsible block), ye5d6e (instrument moves focus), b40fd1 (landmark), 047fe0 (heading) |
| DHS ACT report ([page](https://www.w3.org/WAI/standards-guidelines/act/implementations/trusted-tester/), [data](https://raw.githubusercontent.com/Section508Coordinators/act-tt/main/act-trusted-tester.json); TT 5.1, May 2023) | none of the five bypass rules scored |
| ICT Testing Baseline 3.1 | [4.A-BypassBlocks](https://ictbaseline.access-board.gov/web-baselines/04RepetitiveContent/) |
| Baseline Alignment cases | none for 2.4.1 |

## 9.A Bypass (2.4.1; Repetitive Content, pp. 42–43)

**What the PDF asks.** Identify blocks repeated on other pages (navigation,
headers, tabs, banners; need not be identical; small sections and single
links excluded; a block at the bottom may need no bypass). From the top,
navigate forward to the repeated blocks (a bypass may appear only on focus),
find a keyboard method to bypass them (skip links, hotkeys, scripted
elements; frames in some browsers) and activate it (HtT 1–3). Several blocks
may need several methods; with nothing focusable after the block, the move
may not show (HtT 3.a, 3.b). PASS if a keyboard method exists and, when
activated, bypasses the block (ER 1, 2), without skipping content that is
not repetitive (Note 2). DNA if no block repeats on other pages.

**Settled by the sources.**
- *Landmarks and headings alone are not a bypass method.* The Baseline
  excludes ARIA11 and H69 because they "require additional assistive tools
  to function as bypass methods"; the TT text lists only keyboard methods.
  W3C's ACT composite (cf77f2) accepts them (b40fd1, 047fe0), but maps a
  pass only to "needs further testing", and DHS scored none of these rules.
  The tool follows the TT text and the Baseline: a page whose only bypass
  is a landmark or heading FAILS 9.A. ACT cases that pass that way are
  vendored with our expected outcome and the difference noted (as the
  Baseline manifest's `differs`).
- *Accepted methods.* Same-page links (G1, G123, G124), and "a hide menu
  option and a navigation tree" (Baseline), which ACT's 3e12e1
  (collapsible block) also covers; hotkeys and scripted elements (TT).
- *What working means.* The Baseline: "the block of repeated content is
  hidden, closed or skipped", and a skip moves "focus ... past the
  repetitive content only". G1: activating the link moves focus to the main
  content. So the landing must be past every stop of the block and not past
  the start of the main content.
- *Visible on focus is enough* (G1; Understanding 2.4.1 does not require a
  bypass to be visible without focus). A bypass that never becomes visible
  on focus is a 4.D matter (the Baseline points to its Focus test), not a
  9.A failure on its own.
- *Small repeated items* (a single link, words, phrases) are not blocks
  (Understanding, TT, Baseline).
- *Where the bypass sits.* G1 checks the link is "the first focusable
  control"; the TT asks only that a method exists and works. Record its
  position as a note; do not fail a working bypass for being second.
- *Repetition cannot be read from one page.* ACT defines a repeated block by
  following an instrument to another page and finding an equivalent block
  there; Understanding implies a set of pages and gives no single-page
  method. That is Q1.

**Reuse.**
- Candidates from the walk: in-page links (`#id`) among the stops before the
  main content, and disclosure buttons (`aria-expanded`, `aria-controls`)
  whose controlled element holds the block's stops; 4.D's F03 skip-link
  fixture and `budget/agency-home.html` are ready pages.
- `ctx.replay` to the candidate, Enter, then Tab once. For a link, where the
  next stop falls in P1's order shows what was skipped (Chrome moves the
  sequential focus starting point to a non-focusable target; checked in
  Linux headless Chromium 2026-11-01 with a skip link to a `div` holding an
  `h1`; Windows Chrome is a build-task check). For a hide control, the
  block's stops must be gone from the Tab order afterwards (4.F's pass R
  already presses Enter on disclosure buttons and reads their container).
- The start of the main content: the `main` element or landmark, else the
  first `h1` (4.F's region information).

**Open points for Abby.**
- Q1. How the tool knows a block repeats on other pages: (a) the agent
  judges by looking: the question shows the stops before the main content
  with their landmarks (banner, navigation) and asks whether they form a
  block repeated across the site; the spec marks it as a question a careful
  tester settles by looking (like 4.E J1), and "unsure" goes to a person
  (recommended now: how testers work on one page); (b) an optional input of
  other pages of the same site (each allowlisted), recorded and compared
  mechanically (exact, and the base for 9.B and 9.C, but new pipeline work);
  (c) (a) now and (b) with 9.B/9.C, reusing the same input. Page content
  never picks the other pages (principle 5).
- Q2. No `main` and no `h1`, so the start of the main content is unknown:
  (a) an open question naming the landing stop and the stops skipped
  ("are all of these part of the repeated block?") (recommended); (b) NEEDS
  REVIEW.
- Q3. Hotkeys and scripted methods: (a) tried only when the page text
  documents a key, as 4.C's documented keys (the agent names the key, the
  tool presses it) (recommended); (b) not tried, NEEDS REVIEW when no skip
  link or hide control works.

**Draft rules.** DNA when Q1 finds no repeated block. A candidate works when
the block is hidden (its stops leave the Tab order) or skipped (the next Tab
lands past every stop of the block and not past the start of the main
content). PASS when every repeated block before the main content has a
working method. FAIL when a block has no keyboard method, or every method
for it is broken (target missing, focus not moved, lands past the main
content). NEEDS REVIEW when the tool could not judge (Q1 unsure, frames,
time).

**Fixtures.** No Baseline Alignment cases for 2.4.1. Vendor ACT cases (base
`https://www.w3.org/WAI/content-assets/wcag-act-rules/testcases/<rule>/`):
ye5d6e (instrument moves focus; 8 pass, 3 fail) and 3e12e1 (collapsible;
4 pass, 3 fail) as the cases that match the TT methods; cf77f2's landmark-
only (9eb0cf41…) and heading-only (36f679b6…) passes as cases where our 9.A
outcome differs (FAIL). DHS scored none of them, so the manifest records
ACT's expectation and ours, no DHS verdict. Custom pages for gaps: a skip
link to a non-focusable target, to a missing id, one that lands past the
main heading, one visible only on focus (4.D F03), two blocks needing two
links, a "hide menu" button, nothing before main (DNA under Q1).

**Time.** One replay per candidate, usually one or two: a few seconds.

## Order of work (when the batch starts)

1. Abby's answers to Q1–Q3; research and plan 9.B and 9.C here.
2. If Q1 is (b) or (c): the input for other pages of the same site (each
   allowlisted and recorded), shared by 9.A, 9.B and 9.C.
3. 9.A: spec 0.1.0 from `_template.md`, fixtures, check, judge eval, 1.0.0,
   as `checks/base.py` describes; then 9.B and 9.C.
