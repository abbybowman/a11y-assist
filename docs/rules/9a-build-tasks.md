# Build tasks: 9.A, 9.B and 9.C

Specs [9a-bypass.md](9a-bypass.md),
[9b-consistent-navigation.md](9b-consistent-navigation.md) and
[9c-consistent-identification.md](9c-consistent-identification.md) 1.0.0 (9.C 1.1.0)
(Abby, 2026-11-02) are built as `checks/t9a.py`, `t9b.py` and `t9c.py` on
the shared `site.py` read, registered. Judge eval: evals/README.md run 8 (4/4).

## Fixtures

Vendored first: 28 W3C ACT cases for 9.A (ye5d6e, 3e12e1, cf77f2), each
compared with the rules' own other page `bypass-blocks-cf77f2/chapter2.html`
(`tests/test_fixtures_9a.py`; expected outcomes in
`fixtures/act/manifest.json`). Ours differ from ACT's on three: cf77f2
passed 2 (heading only) and passed 3 (landmark only) are FAIL, because
headings and landmarks are not keyboard methods (Baseline 4.A excludes
ARIA11 and H69); passed 7 (the repeated block after main) is DOES NOT APPLY
(Abby: nothing before the main content to bypass, as with a footer). DHS scored none.
No ACT rule and no Baseline Alignment case exists for 9.B or 9.C, so they
rely on custom sites in `tests/fixtures/9x/` (`tests/test_fixtures_9x.py`,
all three tests in one call):

| Case | Pages | Covers |
| --- | --- | --- |
| consistent-site | a1 vs a2 | 9.A M7 PASS; 9.B N6; 9.C C1 |
| nav-reordered | a1 vs a3 | 9.B N3 (source order) |
| nav-css-order | a1 vs a4 | 9.B N4 (CSS `order` swaps two menu items on screen) |
| two-pages-one-reordered | a1 vs a2, a3 | 9.B: one FAIL instance is enough |
| renamed | a1 vs a5 | 9.C J1 inconsistent ("Contact"/"Get in touch" by destination, "Search"/"Find" by place); 9.B ignores unmatched items |
| unrelated | a1 vs c1 | DNA for all three |
| skip-past-heading | b1 vs a2 | 9.A M8 (lands past the main heading) |
| skip-after-nav | b2 vs a2 | 9.A: a skip link after the block covers nothing |
| documented-key | b3 vs a2 | 9.A J1 documented Alt+S, pressed (G4) |
| breadcrumbs-repeated / -not-repeated | b4 vs a2 | 9.A no main or h1: J2 (the second is rules-only, `NOT_EVAL`) |
| two-links | b5 vs b6 | 9.A coverage across two links (G123) |
| paging | d1 vs d2 | 9.C J1 consistent ("Go to page 4/5"); 9.A A4 DNA (block is one link) |

## Browser behavior to verify in code

| ID | Verify | Rules that depend on it |
| --- | --- | --- |
| V1 | Checked (Linux headless Chromium, 2026-11-02, ACT ye5d6e passed 7 and 8): after Enter on a link to a non-focusable target, `:target` is the target and the next Tab goes to the first stop after it | 9.A landing, M6 |
| V2 | Windows headed Chrome: V1 again, and a hotkey with Alt (Alt+letter can open browser menus there) | 9.A, J1 |
| V3 | ANDI on a page whose Content-Security-Policy blocks inline scripts: 9.C A2 (not performed) | 9.C A2 |

## Left

- V2 and V3 above (Windows headed Chrome; a page whose CSP blocks ANDI).
- Real .gov sites: the region match and 9.C's same-place pairing were
  tuned on fixtures only. Check them on the agent-eval pages
  (plans/2026-10-31-agent-eval.md) before trusting 9.B and 9.C there.
