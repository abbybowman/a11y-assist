# The TT PDF as data, and where the PDF disagrees with itself

**Problem.** Rules, tools and explanations kept needing TT text (names,
conditions, how to test, WCAG mapping). Parsing the PDF at run time is
fragile, and retyping text drifts.

**What we do.** `docs/sources/tt-5.1.3/convert.py` converted the PDF once into
Markdown (one file per part) and `tt.json` (63 conditions). The converter
fails unless every word of the PDF body appears in the Markdown in the same
order; `tests/test_tt_source.py` re-runs that check where `pdftotext` exists.
Code reads TT text only through `catalog.py`.

**Layout traps found while converting** (pdftotext -layout):

- Running headers and footers on every page ("Section 508 Conformance Tests",
  "<section title>   <page>"), sometimes with the page number on its own line.
- Some test tables have "Applicability" without a colon (17.x, 18.A), and a
  condition can start a column left of its header (7.B).
- Some "Check" headings carry a prefix ("For Decorative Images – Check …") or a
  suffix ("(Obsolete)").
- Each section ends with a two-column "Applicable Standards" table; joined as
  a paragraph it scrambles, so it is kept as a fenced block.

**The PDF disagrees with itself; record, don't resolve.** Page 5 says 63 test
conditions; Appendix A lists 62. 6.B appears only in the Appendix C quick
reference, and Appendix B says it was removed. 5.E keeps its section marked
"(Obsolete)". Some Appendix C conditions are worded differently from the
section text (e.g. 1.B), kept as `quick_reference_condition`. The section text
is used for rules.
