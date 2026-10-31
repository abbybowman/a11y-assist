# ACT test cases (vendored)

W3C ACT test cases for the rules our specs use, saved byte for byte by
`sync_act.py` and served from this folder as the web root (pages load assets by
absolute `/WAI/...` paths). `manifest.json` pins each case's full `testcaseId`,
the SHA-256 of every file and of the `testcases.json` it was built from, ACT's
expected result per rule, DHS's Trusted Tester 5.1 result, and our expected
outcome. Expected outcomes are never written into a page.

Rules vendored: 4.C — a1b64e, ebe86a, 80af7b. None is approved by W3C yet
(proposed rules).

## Attribution

This folder includes material copied from the W3C ACT test cases
(<https://www.w3.org/WAI/content-assets/wcag-act-rules/testcases.json>, from the
ACT Rules at <https://www.w3.org/WAI/standards-guidelines/act/rules/>).
Copyright © 2026 W3C® (MIT, ERCIM, Keio, Beihang). The files are unmodified.
DHS results come from
<https://github.com/Section508Coordinators/act-tt> (`act-trusted-tester.json`).

## W3C Software and Document Notice and License

This work is being provided by the copyright holders under the following
license.

**License.** By obtaining and/or copying this work, you (the licensee) agree
that you have read, understood, and will comply with the following terms and
conditions.

Permission to copy, modify, and distribute this work, with or without
modification, for any purpose and without fee or royalty is hereby granted,
provided that you include the following on ALL copies of the work or portions
thereof, including modifications:

- The full text of this NOTICE in a location viewable to users of the
  redistributed or derivative work.
- Any pre-existing intellectual property disclaimers, notices, or terms and
  conditions. If none exist, the W3C Software and Document Short Notice should
  be included.
- Notice of any changes or modifications, through a copyright statement on the
  new code or document such as "This software or document includes material
  copied from or derived from [title and URI of the W3C document]. Copyright ©
  [YEAR] W3C® (MIT, ERCIM, Keio, Beihang)."

**Disclaimer.** This work is provided "AS IS," and copyright holders make no
representations or warranties, express or implied, including but not limited
to, warranties of merchantability or fitness for any particular purpose or that
the use of the software or document will not infringe any third party patents,
copyrights, trademarks or other rights.

Copyright holders will not be liable for any direct, indirect, special or
consequential damages arising out of any use of the software or document.

The name and trademarks of copyright holders may NOT be used in advertising or
publicity pertaining to the work without specific, written prior permission.
Title to copyright in this work will at all times remain with copyright
holders.

Source of this notice: <https://act-rules.github.io/pages/license/>.
