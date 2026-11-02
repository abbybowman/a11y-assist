---
tt_test: 19.A
tt_name: 2.4.5-multiple-ways
spec_version: 1.0.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 19.A (2.4.5-multiple-ways)

The tool gives each page one 19.A outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED (p. 6). It needs other pages of the same site; without them the test is not performed.

**Citations.** Printed page 75 of TT 5.1.3 (text also in `tt://5.1.3/tests/19.A`). Identify Content: "All web pages within a set of related web pages"; EXCLUDE pages that are "the result of, or a step in, a process, such as an order confirmation form". Applicability: DNA if the page is not within a set of related pages OR is a result of, or a step in, a process. HtT 1: two or more ways to locate the page, such as site maps, site search, tables of contents, navigation menus or dropdowns, navigation trees, links between pages (not limited to these). HtT 2: "Verify that the identified techniques correctly function and lead to the web page" (2.a links and menus lead to the pages; 2.b "The search form leads to the page(s) which contains the search term"). ER 1: "At least two techniques exist"; ER 2: they "function correctly such that they lead to the correct web page".

**Other sources.** [Understanding 2.4.5](https://www.w3.org/WAI/WCAG22/Understanding/multiple-ways.html): a *process* is a "series of user actions where each action is required in order to complete an activity" (a multi-step order, a funds-transfer confirmation, search engine results); a *set of web pages* shares a purpose and author (a checkout template without the site navigation is not part of the product pages' set). Sufficient: two or more of G125 (related links), G64 (table of contents), G63 (site map: its links lead to the pages), G161 (search: a term that occurs in the set leads to a page containing it or a list of links to such pages), G126 (a list of links to all pages), G185 (the home page links to every page). No failure technique; no ACT rule; no DHS ACT data. ICT Testing Baseline 3.1 [23.A-MultipleWays](https://ictbaseline.access-board.gov/web-baselines/23MultipleWays/): the same list, the process exception, "Additional techniques ... may be available". No Baseline Alignment cases.

**Terms.**
- *Other pages*, the site read, *units*, *regions*: [9a-bypass.md](9a-bypass.md) Terms and section 2. Other pages come from the caller (CLAUDE.md principle 5); the one exception is the live search below.
- *T*: the tested page's final URL. A link *leads to T* when its destination equals T (absolute, fragment dropped, trailing slash ignored).
- *Kinds of way* (Abby, 2026-11-02: two ways means two different kinds, from the TT's list):
  - *navigation*: a link to T on another page, inside a navigation, banner or contentinfo region (menus, dropdowns, trees, header and footer link lists; breadcrumbs);
  - *table of contents*: a link to T inside a region or list labelled "contents" or "on this page";
  - *site map*: a link to T on another page that is a site map (its title or first heading says "site map" or "sitemap", or a link named so leads to it);
  - *links between pages*: a link to T anywhere else on another page (its content);
  - *search*: the site search leads to T (below).
- *Search form*: a form with role search, a search field, or a field named `q`, `query`, `search`, `s`, `k` or `keyword`, on T or on another page.
- *Live search* (Abby, 2026-11-02: exhaust the pages first, then run the search on the live site): only when the caller's pages show fewer than two kinds and a search form exists. One search per run: the form must submit by GET; its action URL must pass the allowlist and be on T's host (the allowlist is checked on every redirect hop, the host at the end); the term is T's first `h1`, else its title; the request carries the form's own hidden fields and the term, nothing else. The results page is recorded as its own HAR and read like another page. Search counts as a way when the results page links to T (HtT 2.b; G161 step 5).
- *Suggested pages*: same-host URLs the pages link to that could show more ways and were not given: links named "site map", "sitemap" or "A-Z index"; the home page (a link to the site's root, or named "home"); breadcrumb links. At most 5. They are proposed for the calling agent to ask the user about, never visited by the tool (Abby, 2026-11-02).
- *Process hint*: T's text has "step N of M", "review your", "confirm", "confirmation", "order summary" or "thank you for", and T has a form with a submit button.

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | No other pages were given | NEEDS REVIEW, not performed: "it needs other pages of the same site; give the home page and, if the site has one, its site map" | p. 75 Identify Content; Abby, 2026-11-02 |
| A2 | A page could not be read | NEEDS REVIEW, not performed, naming the page | Spec rule |
| J1? | A process hint, J1 not answered | NEEDS REVIEW | Open question |
| A3 | J1 = process | DOES NOT APPLY | p. 75 Applicability; Understanding 2.4.5 (process) |
| A4 | J1 = unsure | NEEDS REVIEW | Spec rule |
| A5 | Otherwise | Applies; go to section 3 | |

## 2. Evidence to collect

**Site read** (shared with 9.A–9.C): adds each page's title and its search forms (action, method, the field to fill, hidden fields). **Live search**, only as in Terms. Nothing is pressed on the recorded pages.

**Time budget:** the site read (shared with 9.A–9.C; 19.A itself measured 0.0 s on the agency budget page with one other page); the live search, when it runs, one live load and one read (a few seconds, within the time the other pages add).

## 3. Mechanical checks

The instance is the page: the kinds of way found.

**3a. Way rules**

| # | Evidence pattern | Result | Source |
| --- | --- | --- | --- |
| W1 | Links to T on the other pages, each classified by kind (Terms) | Kinds found | p. 75 HtT 1, 2.a |
| W2 | Fewer than two kinds, a search form, the live search allowed and run, its results link to T | Adds search | p. 75 HtT 2.b; G161 |
| W3 | The live search ran and its results do not link to T | Search does not lead to T (not a way) | p. 75 ER 2 |
| W4 | The search form cannot be run (POST, script only, off host, blocked, time) | Search not verified | Spec rule |

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Two or more kinds | PASS, naming them |
| G3 | Fewer than two kinds, and suggested pages exist or the search was not verified (W4) | NEEDS REVIEW, naming the ways found and the suggested pages to give next ("This test could not be performed" note) |
| G4 | Fewer than two kinds, no suggested pages left, and no search form or the search does not lead to T (W3) | FAIL: nothing is left to try (Abby, 2026-11-02) |
| G5 | Anything else | NEEDS REVIEW |

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| G2 | "This page can be found in more than one way: <kinds>." |
| G3 | "We found <n> way(s) to reach this page in the pages you gave (<kinds>). To check further, ask the user whether to run again with these pages too: <urls>." |
| G4 | "We found only <kinds or 'no way'> to reach this page, and nothing else to check: add a second way, such as a link in the site navigation, a site map or a site search that finds it." |
| A1 | "This test could not be performed: it needs other pages of the same site. Run it again with other_pages (the home page and, if there is one, the site map)." |
| A3 | "This page is a step in a process (or its result), so this test does not apply." |

## 4. Judgment questions

J1 is settled by looking (CLAUDE.md principle 8); the agent answers unsure whenever the text does not settle it.

### J1. Is this page a step in, or the result of, a process?

**Question:** "input.text is the tested page's visible text, in order. Is this page a step in a process that must be completed in order (a checkout step, a form wizard step, a review-and-submit page) or the result of one (an order or payment confirmation, a search results page)? Answer process, not_process or unsure."

**Output:** `{choice: process|not_process|unsure, reasons}`.

**Rubric.** process: "Step 2 of 4", a review page before submitting, a confirmation number after submitting, search results. not_process: a page anyone can reach directly that only contains a form (a contact form, a newsletter sign-up, a start page for an application). unsure: whenever the text does not settle it.

**Use:** A3, A4.

## 5. Edge cases

| Case | Rule | Verify |
| --- | --- | --- |
| T is the home page | Links to it (logo, "Home") are navigation as any other | Spec rule |
| T reached only through a redirect | T is the final URL; links to the requested URL also count | Spec rule |
| A search that runs in script only (no form submission) | W4: not verified | Spec rule |
| A results page that is itself a step in a process | Read only for links to T | Spec rule |

## 6. What a FAIL records

Every link to T found (page, region, name), the kinds, the search form and the live search (URL, term, whether its results link to T), and the pages given.
