# Plan: multi-page tests 9.A, 9.B, 9.C (2026-11-02, done: 1.0.0)

The literal order of work. Rules live in the specs
([9a-bypass.md](../rules/9a-bypass.md),
[9b-consistent-navigation.md](../rules/9b-consistent-navigation.md),
[9c-consistent-identification.md](../rules/9c-consistent-identification.md));
each answer from Abby is written into the rule it decides.

## Sources read

| Source | 9.A (2.4.1) | 9.B (3.2.3) | 9.C (3.2.4) |
| --- | --- | --- | --- |
| TT 5.1.3 | pp. 42–43 | pp. 43–44 | p. 44 |
| W3C Understanding | [Bypass Blocks](https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html) | [Consistent Navigation](https://www.w3.org/WAI/WCAG22/Understanding/consistent-navigation.html) | [Consistent Identification](https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification.html) |
| Sufficient | G1, G123, G124, SCR28 (ARIA11, H69: not keyboard methods) | [G61](https://www.w3.org/WAI/WCAG22/Techniques/general/G61) | [G197](https://www.w3.org/WAI/WCAG22/Techniques/general/G197) (+ 1.1.1, 4.1.2 techniques) |
| Failure | none | [F66](https://www.w3.org/WAI/WCAG22/Techniques/failures/F66) | [F31](https://www.w3.org/WAI/WCAG22/Techniques/failures/F31) |
| W3C ACT | cf77f2 (proposed composite) of ye5d6e, 3e12e1, b40fd1, 047fe0 | none ("No ACT Rules available") | none |
| DHS ACT data ([act-tt](https://raw.githubusercontent.com/Section508Coordinators/act-tt/main/act-trusted-tester.json), checked 2026-11-02: 251 assertions) | none of the five rules scored | none | none |
| ICT Testing Baseline 3.1 | [4.A-BypassBlocks](https://ictbaseline.access-board.gov/web-baselines/04RepetitiveContent/) | 4.B-ConsistentNavigation | 4.C-ConsistentIdentification |
| Baseline Alignment cases | none (rechecked 2026-11-02: the full `baselineTestCases.csv` has no TC04 row and no 2.4.1, 3.2.3 or 3.2.4) | none | none |

Found while reading: `tt.json` had 9.B's text scrambled into 9.C (the
PDF's heading "consistent- navigation" breaks over a line); fixed from
pp. 43–44. 5.B, 7.C and 16.B carry the previous test's steps the same way
(ROADMAP).

## Order of work

1. **Other pages input** (shared by the three tests). `a11y_run_tt_tests`
   takes `other_pages`: 1–5 URLs of the same site, chosen by the caller
   (never by page content: principle 5). Each passes the allowlist, must be
   on the tested page's host before and after redirects (else a tool error,
   nothing tested), and is recorded as its own HAR
   (`evidence/pages/p<N>.har.zip`); the report records each URL and final
   URL. The run limit grows by `OTHER_PAGE_S` (default 20 s) per other
   page; progress messages name each page. Pages are recorded only when a
   selected test uses them. Without other pages, 9.A–9.C are NEEDS REVIEW
   "This test could not be performed: it needs other pages of the same
   site", at no cost to a single-page run.
2. **`site.py`**: one read per page (fresh load of its HAR) of its content
   in reading order (units: text, headings, images, controls with role,
   name, link destination, landmark, box), cached in `RunContext.cache` so
   the three checks read each page once; matching of units and regions
   across pages. Facts only.
3. **Specs 0.1.0** (this commit) and their build-tasks files.
4. **Fixtures**: vendor ACT cases for 9.A with `sync_act.py` (ye5d6e,
   3e12e1, cf77f2's landmark-only and heading-only passes and its other
   cases), plus the shared test asset `bypass-blocks-cf77f2/chapter2.html`
   as their other page. Custom pages in `tests/fixtures/9x/` for the gaps
   (9.B and 9.C have no vendored cases at all), each a small site of two or
   three pages.
5. **9.A** (`checks/t9a.py`, draft in `tests/drafts.py`): bypass
   candidates from the walk, one replay each (`ctx.replay`, Enter, read the
   landing, Tab once), hidden blocks, J1 documented keys, J2 skipped items.
6. **9.B** (`checks/t9b.py`): order of matched components and regions per
   other page; no questions.
7. **9.C** (`checks/t9c.py`): ANDI on every page (`andi.andi_output`),
   components matched by destination, id or place; J1 by looking.
8. **Judge eval** with one subagent for every 9.x packet
   (`evals/judge_eval.py prepare OUT 9.A,9.B,9.C`); fix mismatches in
   questions or evidence.
9. **Time**: `evals/time_budget.py --drafts budget/agency-home.html` before
   and after (single page: 9.x must add about 0 s), and one multi-page run
   timed.
10. Specs match code; ask Abby for 1.0.0; lessons in `docs/solutions/`,
    ROADMAP, `docs/hackathon/evaluation.md` and the deck slide.
