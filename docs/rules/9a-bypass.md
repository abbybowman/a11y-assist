---
tt_test: 9.A
tt_name: 2.4.1-bypass-function
spec_version: 0.1.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 9.A (2.4.1-bypass-function)

The tool gives each page one 9.A outcome: PASS, FAIL, DOES NOT APPLY or NEEDS REVIEW. It never emits NOT TESTED (p. 6). It needs other pages of the same site; without them the test is not performed.

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/9.A`). Identify Content, p. 42: blocks "repeated on other pages within the site" (navigation links, page headers, tabs, banners); they "do not have to be exactly the same" ("the same type of information and/or serve the same purpose"); EXCLUDE "repeated individual words, phrases, or single links"; Note: a bypass for links "at the bottom of a web page may be unnecessary"; none: DNA. HtT 1 (from the top, navigate forward to the repeated blocks; a bypass may be visible only on focus), HtT 2 (skip links, hotkeys, scripted elements; frames in some browsers; 2.a ANDI focusable elements: "skip links, hide options, collapse menu"), HtT 3 (activate it; 3.a several blocks may need several methods; 3.b the move may not be visibly evident), pp. 42–43. ER 1 (a keyboard method is provided), ER 2 ("when activated, the method works, and the block of content is bypassed"), p. 43. Notes, p. 43: "The bypass function(s) must not skip over content that is not repetitive."

**Other sources.** [Understanding 2.4.1](https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html); sufficient [G1](https://www.w3.org/WAI/WCAG22/Techniques/general/G1) (a link at the top that moves focus to the main content), [G123](https://www.w3.org/WAI/WCAG22/Techniques/general/G123), [G124](https://www.w3.org/WAI/WCAG22/Techniques/general/G124), SCR28 (collapsible menu); ARIA11 and H69 (landmarks, headings) are not keyboard methods. W3C ACT [cf77f2](https://www.w3.org/WAI/standards-guidelines/act/rules/cf77f2/) (proposed) passes when any of [ye5d6e](https://www.w3.org/WAI/standards-guidelines/act/rules/ye5d6e/) (an instrument moves focus to non-repeated content after repeated content), [3e12e1](https://www.w3.org/WAI/standards-guidelines/act/rules/3e12e1/) (an instrument hides the block and removes it from the accessibility tree), b40fd1 (landmark) or 047fe0 (heading) passes. DHS scored none of these rules (act-tt data, checked 2026-11-02). ICT Testing Baseline 3.1 [4.A-BypassBlocks](https://ictbaseline.access-board.gov/web-baselines/04RepetitiveContent/): "a keyboard-accessible method to bypass repetitive content, with no additional tools required"; it works when the block is "hidden, closed or skipped", and a skip moves "focus ... past the repetitive content only"; ARIA11 and H69 excluded; a bypass not visible on focus is Baseline 2.1 (our 4.D), not 4.A. No Baseline Alignment cases (rechecked 2026-11-02).

**Terms.**
- *Other pages*: 1–5 pages of the same site the caller names (`other_pages`), each allowlisted and on the tested page's host, recorded as its own HAR. Page content never chooses them (CLAUDE.md principle 5). How they are read: `site.py` (section 2).
- *Unit*: one piece of the page's rendered content in reading (DOM) order: a control (link, button, form field, any element with a widget role or `tabindex` ≥ 0; its text is not read again), a heading, an image with alt text, or an element's own text. Each has a *text key*: its visible text or name, lower case, spaces collapsed.
- *Region*: a banner, navigation, search, complementary or contentinfo landmark (elements or roles; `header` and `footer` only outside `article`, `aside`, `main`, `nav` and `section`), identified by role and its label or id, else by role and order among its role.
- *Repeated unit*: a unit whose text key appears on any other page, or that sits in a region that some other page also has (same role and label or id, else same role and order). Blocks "do not have to be exactly the same" (p. 42): a region match covers a navigation whose items differ.
- *Main start* M: the first unit of the `main` landmark; if it has none, or it does not come after a repeated unit, the first `h1` that is not repeated and comes after a repeated unit; else the first unit that is not repeated and comes after a repeated unit (ACT ye5d6e: "non-repeated content after repeated content"). Recorded as `main`, `h1` or `first_unique`.
- *Block* B: the repeated units before M. *Block stops*: those that are walk stops.
- *Candidate*: a P1 stop before M that may be a bypass: a link to a place on the same page (`#...`, including `#`), an element with role link and no address, a button that is not a form's submit button, or a `summary`. At most 8, in walk order.

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | No other pages were given | NEEDS REVIEW, not performed: "it needs other pages of the same site to know which content repeats" | Abby, 2026-11-02 (Q1: other pages required); p. 42 Identify Content |
| A2 | A page could not be read (load, units) | NEEDS REVIEW, not performed, naming the page | Spec rule |
| A3 | No unit of the tested page is repeated | DOES NOT APPLY | p. 42 Applicability |
| A4 | Repeated units exist but B is empty (they all come after the main content), or B is small: one control, or fewer than 4 words in all | NEEDS REVIEW, naming what repeats and where | p. 42 Identify Content (EXCLUDE, Note); Abby, 2026-11-02 (no outcome given by the TT for "nothing to bypass": NEEDS REVIEW) |
| A5 | Otherwise | Applies; go to section 3 | |

## 2. Evidence to collect

**From the shared keyboard walk** (`walk.py`; [4c-no-keyboard-trap.md](4c-no-keyboard-trap.md) section 2): P1's stops, to find candidates (matched to units by CSS path) and the keys to reach them. Nothing per step. The walk runs only when other pages were given.

**Site read** (`site.py`, shared with 9.B and 9.C, `RunContext.cache["site"]`): one fresh load of each page's HAR, its units (kind, role, text key, name, link destination, CSS path, region, box, whether it is a walk-reachable control) up to 600 per page; a page over the cap is incomplete.

**Candidate replays** (HtT 3): for each candidate, `ctx.replay` to it, press Enter, then read:
- the *landing*: the focused element if focus moved off the candidate, else the element the URL fragment targets (`:target`), else none; and its position: the first unit at or after it in reading order;
- which units of B are no longer rendered (hidden);
- whether the page navigated away;
- one Tab: the stop focus reaches next (Chrome moves the sequential focus starting point to a fragment target that cannot take focus; V1).

**Documented keys** (Q3): only after J1 names a key, one fresh load, the key pressed from the top of the page, then the same reads.

**Time budget:** the site read is one load and one DOM read per page (about 1 s each); candidate replays one each (about 1–2 s; usually one or two candidates). All of it runs only with other pages, within the time those pages add to the run limit (`OTHER_PAGE_S` each).

## 3. Mechanical checks

Each candidate is an *instance*. A candidate's *jump* is the set of units strictly between it and its landing.

**3a. Instance rules (first match wins)**

| # | Evidence pattern | Instance | Source |
| --- | --- | --- | --- |
| M1 | The replay did not reach the candidate, or the reads failed | NEEDS REVIEW | Spec rule |
| M2 | Enter left the page (navigation) | Does not work | p. 43 ER 2 |
| M3 | Every unit of B after the candidate is no longer rendered | Works: hides the block (covers those units) | Baseline 4.A ("hidden, closed"); SCR28; ACT 3e12e1 |
| M4 | Some units of B after the candidate are no longer rendered | Works in part: covers those units | p. 43 HtT 3.a |
| M5 | No landing, or the landing is not after the candidate | Does not work (target missing, nothing moved) | p. 43 ER 2; ACT ye5d6e failed 2 |
| M6 | The next Tab reached a stop before the landing | Does not work (focus did not really move) | p. 43 ER 2 |
| M7 | The landing is at or before M | Works: covers its jump | G1; Baseline 4.A ("past the repetitive content only") |
| M8 | The landing is past M and M is `main` or `h1` | Does not work: skips main content | p. 43 Note 2 |
| J2? | The landing is past M, M is `first_unique`, J2 not answered | NEEDS REVIEW | Open question (Q2) |
| M9 | J2 = repeated | Works: covers its jump | p. 42 Identify Content ("same type of information") |
| M10 | J2 = not_repeated | Does not work: skips content that is not repetitive | p. 43 Note 2 |
| M11 | Anything else (J2 unsure) | NEEDS REVIEW | Spec rule |

**Coverage.** The block is *bypassed* when, from the first working candidate F onwards, every unit of B after F is covered by some working candidate (or is a working candidate itself), and at most 2 block stops come before F (a logo or language link before the skip link; G1 asks for the first control, the TT does not, so its position is a note). Several candidates may share the work (HtT 3.a; G123).

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | The block is bypassed | PASS, naming the method(s) |
| G3 | An instance is NEEDS REVIEW, a J question is open or unsure, the candidates were capped, or time ran out | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | J1 named a key and pressing it bypasses the block (M3–M9 applied to it) | PASS |
| G5 | Not bypassed, every candidate decided, and J1 = no or J1 not asked (no page text mentions keys) | FAIL: no keyboard method bypasses the repeated block (landmarks and headings alone do not count: Baseline 4.A excludes ARIA11 and H69) |
| G6 | Anything else | NEEDS REVIEW |

**Notes (no outcome).** Where the working method sits ("the first thing the keyboard reaches" or "the Nth"); whether it is visible when focused (a skip link that never shows is a 4.D matter, Baseline 2.1); which other pages were compared.

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| Page PASS | "This page repeats content from the other pages you gave (for example <first repeated text>), and <method> lets keyboard users skip it." |
| Page FAIL | "This page starts with content repeated on the other pages you gave (for example <first repeated text>), and we found no keyboard way to skip past it. Add a "Skip to main content" link as the first thing on the page." |
| A1 | "This test could not be performed: it needs other pages of the same site, to see which content repeats. Run it again with other_pages." |
| A3 | "Nothing on this page appears on the other pages you gave, so this test does not apply." |
| A4 | "Content repeated on the other pages you gave comes only after the main content (or is very short), so a skip link may not be needed. A person should decide." |
| M8, M10 | "<method> skips past the start of the main content." |
| M5, M6 | "<method> did not move the keyboard past the repeated content." |

## 4. Judgment questions

J2 is settled by looking (CLAUDE.md principle 8): the key press that moved focus is the mechanical check; the agent judges only whether the skipped items repeat in purpose, and answers unsure whenever the evidence does not settle it.

### J1. Does the page document a keyboard shortcut that skips repeated content?

Asked only when the block is not bypassed by any candidate, every candidate is decided, and the tested page's text mentions keys (a key name with `+`, "access key", "shortcut", "hotkey", `accesskey` or `aria-keyshortcuts`); otherwise the answer is "no" mechanically (judge-eval lesson: decide what has one possible answer).

**Question:** "input.text holds the tested page's text that mentions keys. Does it document a keyboard shortcut that skips the repeated content at the top of the page (for example "Press Alt+S to skip to the content")? Answer documented (put the key in key and copy the exact words into quote), not_documented or unsure."

**Output:** `{choice: documented|not_documented|unsure, key, quote, reasons}`. Guard: the quote must be found in input.text and the key must be a key name; else NEEDS REVIEW.

**Use:** G4 (the key is pressed on a fresh load), G5.

### J2. Are the skipped items part of the repeated content?

**Question:** "Activating input.method moved the keyboard to input.landing. Doing so skipped the items in input.skipped, in page order. Items marked repeats: true were found on another page you gave; the others were not found word for word. Are the unmarked items also repeated site content, of the same kind and purpose on every page (for example breadcrumbs or a section menu whose links change), or are they content of this page that a user would miss? Answer repeated, not_repeated or unsure."

**Input:** the method (name), the landing (text), the skipped units (text, kind, region, repeats), and the matching units of the other pages' first screens.

**Output:** `{choice: repeated|not_repeated|unsure, reasons}`.

**Rubric.** repeated: navigation, banners, breadcrumbs, a section menu or site search that every page has, even with different words. not_repeated: page text, a heading or a form belonging to this page only. unsure: whenever the items do not settle it.

**Use:** M9–M11.

## 5. Edge cases

| Case | Rule | Verify |
| --- | --- | --- |
| A skip link visible only on focus | Candidate as any other; a note | ACT ye5d6e passed 4 |
| A fragment target that cannot take focus | Landing is the `:target` element | V1 |
| Scripted skip (`location.assign('#main')`, `focus()`) | Landing read the same way | ACT ye5d6e passed 5; cf77f2 passed 8 |
| Toggle that only moves the block off screen, or only sets `aria-hidden` | Still rendered and focusable: M5 or not covered | ACT 3e12e1 failed 2, 3 |
| Landmarks or headings only | Not a keyboard method: G5 FAIL (ACT passes these; noted as a difference) | ACT cf77f2 passed 2, 3 |
| Block in an iframe, or frames as the method | Units are read in the top document only: NEEDS REVIEW when a frame sits in B | Spec rule |
| More than 8 candidates | The first 8 in walk order; G3 if the block is not bypassed | Spec rule |

## 6. What a FAIL records

The other pages compared; B's units (text, region, whether they repeat by text or by region); M and how it was found; every candidate with its landing, hidden units, next Tab stop and row; how to reach each ("Tab 2 times, then Enter").
