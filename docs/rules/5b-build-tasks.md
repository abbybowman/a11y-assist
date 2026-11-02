# Build tasks: 5.B and 5.H

Specs [5b-label-descriptive.md](5b-label-descriptive.md) and
[5h-error-prevention.md](5h-error-prevention.md) 1.0.0 (Abby, 2026-11-02)
are built
as `checks/t5b.py` (on pass L, shared with 5.A and 5.C; components now
record their form) and `checks/t5h.py` (on 5.F's error pass E),
registered. Judge eval:
evals/README.md runs 10 (30/30) and 11 (5.H, 9/9). Order of work:
[plans/2026-11-02-forms-5b-5h.md](../plans/2026-11-02-forms-5b-5h.md).

## Fixtures

- 5.B: the 16 W3C ACT cc0f0a cases (`tests/test_fixtures_5b.py`; DHS
  scored 14: ours agree with all 14, including PASS where ACT says
  inapplicable because the visible label is hidden from assistive
  technology), and 13 TC10.A/TC10.E Baseline cases (TC10.E-1-pass-1, "The
  sky is blue", is a 5.B FAIL; placeholder-only and empty labels are DNA:
  no visual label to judge).
- 5.H: the six TC10.G Baseline cases (one-page forms are DNA under the TT,
  where Baseline expects PASS or FAIL, except 2.c, whose cart is a step),
  and custom pages in `tests/fixtures/5h/`:

| Fixture | Covers |
| --- | --- |
| f01 checks input | J1 multi_step, an error shown on submit: M1 PASS |
| f02 no review | J2 none after a non-refundable payment: M3 FAIL |
| f03 cancel period | J2 reversible ("cancel within 30 days"): M2 PASS |
| f04 server step | the submit leaves the recording: J2 unsure, M4 NEEDS REVIEW |
| f05 newsletter | no consequence hint: A3 DNA |
| f06 confirm dialog | "Pay the $40 fee now?" before paying (G168): J2 review_step, PASS |
| f07 confirm checkbox | a required "I confirm the details are correct" box (G155): J2 review_step, PASS |

## Time

Measured with `time_budget.py --drafts` (Linux headless, 2026-11-02): 5.B
0.0 s and 5.H 0.1 s on both budget pages (they reuse pass L and pass E);
agency page 109.1–110.4 s, benefits form 97.6 s for all sixteen tests.

## Left

- 5.B: icon-only buttons are left out (no picture of buttons in pass L);
  add one if real pages show icon buttons with misleading names.
- 5.H: the consequence word list and the error words for "checked" were
  tuned on fixtures; check them on the agent-eval pages (real checkout,
  payment and account-deletion flows) before trusting a DNA from A3. Known
  over-match: "order" also matches "tab order" or "in order to", so J1 is
  asked on pages that only mention those (one question; never a PASS on
  its own). Narrowing the list is a MINOR change.
