# Build tasks: 19.A

Spec [19a-multiple-ways.md](19a-multiple-ways.md) 1.0.0 (Abby,
2026-11-02, including G4) is built as `checks/t19a.py` on the shared `site.py` read (each page's title
and search forms added) and `RunContext.record_live` (the live site
search), registered.
Judge eval: evals/README.md run 9 (2/2). Order of work:
[plans/2026-11-02-multiple-ways.md](../plans/2026-11-02-multiple-ways.md).

## Fixtures

No ACT rule, DHS verdict or Baseline Alignment case covers 2.4.5. A small
custom site in `tests/fixtures/19a/` (`tests/test_fixtures_19a.py`); the
fixture server answers its search (`search.html` for any query,
`search-empty.html` finds nothing):

| Case | Pages | Covers |
| --- | --- | --- |
| nav-and-site-map | t-benefits vs home, sitemap | navigation + site map: G2 |
| nav-and-related-link | t-benefits vs home, related | navigation + links between pages: G2 |
| nav-and-live-search | t-benefits vs home | one kind, then the live search finds it (W2): G2 |
| search-finds-nothing | t2-status vs home | W3; the site map is suggested, not visited: G3 |
| search-finds-nothing-site-map-given | t2-status vs home, sitemap | the suggested page given: G2 |
| one-way-nothing-else | t3-forms vs home2 | one kind, no search, nothing to suggest: G4 FAIL |
| contact-form-not-process | contact vs home, sitemap | hinted, J1 not_process, then G2 |
| process-step | step2 vs home | J1 process: A3 DNA |
| (no other pages) | t-benefits | A1 |

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | A real .gov site search: GET forms, result pages that link to the page, and searches that run only in script (W4) | W2–W4 |

## Left

- V1 on real .gov sites (with the agent-eval pages).
