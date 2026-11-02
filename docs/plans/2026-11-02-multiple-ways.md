# Plan: 19.A Multiple ways (2026-11-02, done: 1.0.0)

The literal order of work. Rules live in
[19a-multiple-ways.md](../rules/19a-multiple-ways.md); Abby's answers are
written into the rules they decide.

## Sources read

| Source | 19.A (2.4.5) |
| --- | --- |
| TT 5.1.3 | p. 75 (`tt.json` checked against the PDF: correct) |
| W3C Understanding | [Multiple Ways](https://www.w3.org/WAI/WCAG22/Understanding/multiple-ways.html) |
| Sufficient (two or more of) | [G125](https://www.w3.org/WAI/WCAG22/Techniques/general/G125) related links, [G64](https://www.w3.org/WAI/WCAG22/Techniques/general/G64) table of contents, [G63](https://www.w3.org/WAI/WCAG22/Techniques/general/G63) site map, [G161](https://www.w3.org/WAI/WCAG22/Techniques/general/G161) search, [G126](https://www.w3.org/WAI/WCAG22/Techniques/general/G126) list of links to all pages, [G185](https://www.w3.org/WAI/WCAG22/Techniques/general/G185) all pages linked from the home page |
| Failures | none |
| W3C ACT | none ("No ACT Rules available for this criterion yet") |
| DHS ACT data | none |
| ICT Testing Baseline 3.1 | [23.A-MultipleWays](https://ictbaseline.access-board.gov/web-baselines/23MultipleWays/) |
| Baseline Alignment cases | none (no Baseline 23 rows in `baselineTestCases.csv`, 2026-11-02) |

## Order of work

1. Spec 0.1.0 and build tasks (this commit).
2. `site.py`: each page's title, and its search forms (GET action, the
   field to fill, hidden fields), read with the units.
3. `RunContext.record_live`: record one more live page on the tested
   page's host (allowlist and egress proxy on every hop, its own HAR), for
   19.A's site search only (Abby, 2026-11-02). CLAUDE.md records the
   exception to principle 5.
4. `checks/t19a.py` (draft in `tests/drafts.py`): ways by kind from the
   caller's pages; then, only if fewer than two kinds, the live search;
   suggested pages; J1 (process) when hinted.
5. Fixtures in `tests/fixtures/19a/` (a small site with a site map, a
   search page served from the fixture server, a checkout step);
   `tests/test_fixtures_19a.py`.
6. Judge eval on 19.A packets with one subagent; time with
   `time_budget.py --drafts --other`.
7. Specs match code; ask Abby for 1.0.0; compound (solutions, ROADMAP,
   hackathon evaluation and deck, CLAUDE.md).
