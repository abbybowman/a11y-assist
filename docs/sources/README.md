# Source documents

| File | Source | SHA-256 |
| --- | --- | --- |
| `Trusted Tester Test Process v5.1.3.pdf` | [Section508Coordinators/TrustedTester5.1 @ 79616ab](https://github.com/Section508Coordinators/TrustedTester5.1/blob/79616ab447adf2649f7266491fb3aebc670fc41d/Documents/Trusted%20Tester%20Test%20Process%20v5.1.3.pdf) (DHS, April 2024) | `050f706f879a2b0bff2913732f56d71c906aad4eb30caaf837f22e4ae94985ee` |

The PDF is the authority for every rules spec in `docs/rules/`. Specs cite
printed page numbers; the PDF file's page index is printed page + 3. To read a
page as text: `pdftotext -layout -f 24 -l 24 "docs/sources/Trusted Tester Test Process v5.1.3.pdf" -`
(printed p. 21, test 4.C).

## Machine-readable copy: `tt-5.1.3/`

A text copy of the PDF so code, agents and people can look tests up without
it. The PDF stays the authority.

- `tt-5.1.3/md/*.md`: the whole document as Markdown, one file per part.
- `tt-5.1.3/tt.json`: the 63 test conditions with name, status, condition,
  requirements (Appendix A, with WCAG level and Understanding link from W3C's
  [wcag.json](https://www.w3.org/WAI/WCAG22/wcag.json)) and each test's
  blocks as Markdown.

Made once on 2026-10-31 with `pdftotext -layout` and a script that checked
every word against the PDF (commit `df488cf`, `docs/sources/tt-5.1.3/convert.py`).
The PDF's own inconsistencies are recorded as given: 5.E is `obsolete`, 6.B is
`removed` (Appendix C only), and Appendix C wordings that differ are kept as
`quick_reference_condition`. 4.1.1 Parsing's level (A in WCAG 2.0) is a manual
entry.

**When DHS publishes a new version** (rare): read its change log (Appendix B)
and edit the affected entries by hand, or re-run the script from `df488cf`.
