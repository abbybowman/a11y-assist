# Source documents

| File | Source | SHA-256 |
| --- | --- | --- |
| `Trusted Tester Test Process v5.1.3.pdf` | [Section508Coordinators/TrustedTester5.1 @ 79616ab](https://github.com/Section508Coordinators/TrustedTester5.1/blob/79616ab447adf2649f7266491fb3aebc670fc41d/Documents/Trusted%20Tester%20Test%20Process%20v5.1.3.pdf) (DHS, April 2024) | `050f706f879a2b0bff2913732f56d71c906aad4eb30caaf837f22e4ae94985ee` |

The PDF is the authority for every rules spec in `docs/rules/`. Specs cite
printed page numbers; the PDF file's page index is printed page + 3. To read a
page as text: `pdftotext -layout -f 24 -l 24 "docs/sources/Trusted Tester Test Process v5.1.3.pdf" -`
(printed p. 21, test 4.C).

## Machine-readable copy: `tt-5.1.3/`

A faithful text copy of the PDF for lookup by code, agents and people, so
nobody has to parse the PDF. The PDF stays the authority.

| Path | What |
| --- | --- |
| `tt-5.1.3/md/*.md` | The whole document as Markdown, one file per part (front matter, sections 1–20, appendices A–D). Layout tables (Applicable Standards, change log, quick reference, mapping) are fenced text blocks, kept as laid out |
| `tt-5.1.3/tt.json` | All 63 test conditions: ID, name, status, condition, section, requirements (Appendix A) with WCAG level and Understanding link, baseline test, whether the test's own text says to record NOT TESTED, and each test's blocks (Identify Content, Applicability, How to Test, Evaluate Results, notes) as Markdown |
| `tt-5.1.3/convert.py` | The converter. It fails unless every word of the PDF body (running headers and footers removed) appears in the Markdown in the same order, with nothing added |

Statuses, as the PDF gives them: 61 `active`; 5.E `obsolete` (its section
says it is no longer required as of Baseline 3.1 and is kept as a
placeholder); 6.B `removed` (listed only in the Appendix C quick reference;
Appendix B says it has been removed; Appendix A omits it). Where Appendix C
words a condition differently from the section text, `quick_reference_condition`
records both.

WCAG data (handle, level, Understanding URL) comes from W3C's
[wcag.json](https://www.w3.org/WAI/WCAG22/wcag.json), fetched 2026-10-31,
SHA-256 in `tt.json` (`wcag_source`). Section 508 uses WCAG 2.0; the WCAG 2.2
Understanding pages cover the same success criteria. One manual entry: 4.1.1
Parsing is Level A in WCAG 2.0 (wcag.json lists it as obsolete in 2.2, with no
level), noted in its record.

**Updating for a new TT version.** Add the new PDF and its hash above, update
`PARTS` and the expected counts in `convert.py` if the structure changed, and
run it (needs poppler's `pdftotext`):

```bash
curl -sSo /tmp/wcag.json https://www.w3.org/WAI/WCAG22/wcag.json
python -I docs/sources/tt-5.1.3/convert.py /tmp/wcag.json
```

Then use the PDF's Appendix B change log to review the diff of `md/` and
`tt.json` test by test, and update any rules spec whose cited text changed.
`tests/test_tt_source.py` checks the copy against the PDF when `pdftotext` is
installed, and checks `tt.json` against the Markdown always.
