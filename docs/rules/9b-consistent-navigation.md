---
tt_test: 9.B
tt_name: 3.2.3-consistent-navigation
spec_version: 0.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 9.B (3.2.3-consistent-navigation)

The tool gives each page one 9.B outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED (p. 6). It compares the tested page with the other pages the caller gives; without them the test is not performed. It asks no questions.

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/9.B`). Identify Content, p. 43: "all navigational elements that are repeated on multiple pages"; navigational elements "provide a user the ability to locate specific information or functionality across the website", "static or interactive", and "groupings of components"; none: DNA. Applicability, p. 43: DNA to a page that "does not contain components that are repeated on other web pages". HtT 1 ("Review multiple web pages ... Do not initiate changes to the content"), HtT 2 (compare the order with the other pages; ANDI's tab order and reading order may help), p. 43. ER 1, p. 43: "Each repeated component occurs in the same relative order with regard to other repeated components on each web page where it appears." Note, p. 44: same relative order is "same position relative to other items", even "if other items are inserted or removed" (expanded menus, a secondary navigation).

**Other sources.** [Understanding 3.2.3](https://www.w3.org/WAI/WCAG22/Understanding/consistent-navigation.html): consistent "visual layout and source order"; examples: a search field, a navigation menu, a skip link; insertions and removals allowed; a change "initiated by the user" (preferences, adaptive user agents) is excepted. Sufficient [G61](https://www.w3.org/WAI/WCAG22/Techniques/general/G61) (list the repeated components; check each is in the same relative order "with regard to other repeated components", and each navigational component's links "in the same relative order"). Failure [F66](https://www.w3.org/WAI/WCAG22/Techniques/failures/F66): "check the default presentation of the navigation mechanism on each page to see if the list of links are in the same relative order"; "secondary navigation items may be in between". No ACT rule; no DHS ACT data. ICT Testing Baseline 3.1 4.B-ConsistentNavigation: "Review multiple Web pages. Do not initiate changes to the content"; navigational mechanisms are "both interactive and non-interactive" and "may or may not be contained within a block of content". No Baseline Alignment cases.

**Terms.** *Other pages*, *unit*, *region* and the site read: [9a-bypass.md](9a-bypass.md) Terms and section 2. A *component* is a control unit (link, button, field) or a region. Components *match* across two pages when they have the same kind, the same region role, the same name (lower case, spaces collapsed) and, for links, the same destination (absolute, without the fragment unless it is a same-page link); several equal ones pair in order. A component inside the `main` landmark of either page is content, not navigation, and is left out. Order is checked two ways: *source order* (reading order) and *visual order* (a comes before b when a's box ends above b's box, or they share a line and a is to the left; pairs with neither relation are not compared).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | No other pages were given | NEEDS REVIEW, not performed: "it needs other pages of the same site to compare" | Abby, 2026-11-02 (Q1); p. 43 HtT 1 |
| A2 | A page could not be read | NEEDS REVIEW, not performed, naming the page | Spec rule |
| A3 | No component of the tested page matches one on any other page | DOES NOT APPLY | p. 43 Applicability |
| A4 | Otherwise | Applies; go to section 3 | |

## 2. Evidence to collect

Nothing of its own: the site read (fresh loads, no interaction: HtT 1 "Do not initiate changes"). For each other page: the matched components (both CSS paths, boxes), the pairs out of source order, the pairs out of visual order, and the regions found on only one page.

**Time budget:** comparisons only (milliseconds); the site read is shared with 9.A and 9.C.

## 3. Mechanical checks

Each other page is an *instance* (the tested page compared with it).

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| N1 | That page's read is incomplete (cap) | NEEDS REVIEW | Spec rule |
| N2 | No component matches between the two pages | Not compared (no instance) | p. 43 Applicability ("where it appears") |
| N3 | Two matched components are in the opposite source order | FAIL | p. 43 ER 1; F66; Understanding 3.2.3 ("source order") |
| N4 | Two matched components are in the opposite visual order | FAIL | F66 ("default presentation"); Understanding 3.2.3 ("visual layout") |
| N5 | Only one component matches | NEEDS REVIEW: no order to compare, and repeated items whose names changed are not matched (9.C) | Spec rule |
| N6 | Otherwise | PASS | p. 43 ER 1, Note (insertions and removals allowed) |

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing each pair out of order and the page it differs on |
| G3 | Any instance is NEEDS REVIEW | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | Every instance is PASS | PASS |

**Notes (no outcome).** Regions on the tested page that no other page has, and the reverse (a person may want to look; insertions are allowed).

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| Page PASS | "The navigation this page shares with the other pages you gave appears in the same order on each of them." |
| Page FAIL | "Some navigation appears in a different order on another page: "<a>" comes before "<b>" here but after it on <page>. Keep repeated navigation in the same order on every page." |
| A1 | "This test could not be performed: it needs other pages of the same site to compare. Run it again with other_pages." |
| A3 | "No navigation on this page appears on the other pages you gave, so this test does not apply." |
| N5 | "Only one link or control is shared with <page>, so there is no order to compare. A person should check the navigation." |

## 4. Judgment questions

None. Which items are navigation is decided by matching and by leaving out the main content; order is mechanical.

## 5. Edge cases

| Case | Rule | Verify |
| --- | --- | --- |
| A secondary menu or an expanded submenu on one page only | Unmatched items are ignored: insertions are allowed | p. 44 Note |
| The same link in the header and the footer | Pairs within the same region role, so they are not mixed | Spec rule |
| Items reordered with CSS (`order`, `flex-direction: row-reverse`) | Visual order catches it (N4) | Fixture |
| A mobile and a desktop copy of the menu, one hidden | Hidden units are not read | Spec rule |
| Menus that open on hover or click | Not opened (HtT 1): their hidden items are not compared | p. 43 HtT 1 |
| No `main` landmark on a page | Nothing is left out as content on that page | Spec rule |

## 6. What a FAIL records

The other page; each pair out of order (names, CSS paths on both pages, source or visual); the matched components in order on both pages.
