# For approval: 4.D, 4.E and 4.F specs

Status: **every open decision answered (Abby, 2026-10-31); specs ready for final approval before building.** No code is written for them yet. Draft
specs (version 0.x) load and are recorded in reports, but give no outcome
until a check is registered.

| Spec | Version | Written by |
| --- | --- | --- |
| [4d-focus-visible.md](../rules/4d-focus-visible.md) | 0.5.0 | 4.D thread (0.2.0), reviewed and edited here |
| [4e-on-focus.md](../rules/4e-on-focus.md) | 0.2.0 | this thread |
| [4f-focus-order-meaning.md](../rules/4f-focus-order-meaning.md) | 0.3.0 | this thread |

Checked against: TT 5.1.3 text (`tt://5.1.3/tests/4.D`, `4.E`, `4.F`), W3C
Understanding 2.4.7, 3.2.1 and 2.4.3, failures F55, F44 and F85, and W3C's
ACT test cases with DHS's TT 5.1 results. Only 4.D has ACT cases (rule
oj04fd: 7 approved, all matching DHS). No ACT rule covers 3.2.1 or 2.4.3, so
4.E and 4.F fixtures are custom.

## 4.D review (0.2.0 → 0.3.0)

The 4.D draft is good: it reads the shared walk, adds no passes, measured its
cost (about 100 ms per stop), and every row has its plain sentence. Its ACT
table matches W3C and DHS exactly. Changes made:

1. **Thresholds are spec constants, not server config.** They decide outcomes;
   if config could change them, a deployment could change outcomes outside the
   spec (principle 2). A change is now a spec version change.
2. **The region grows to any ancestor whose style changes.** Otherwise an
   indicator on a wrapper or card larger than the 8 px margin (oj04fd Passed 3,
   C15 Example 2) would give a false FAIL.
3. **Style reads compare the whole computed style** of the stop, its ancestors
   up to its block container, its labels and their ::before/::after, instead of
   a list of 14 properties. That is simpler and misses nothing.
4. **Citations made exact** for M4 (Understanding 2.4.7's caret example) and O8
   (Understanding: "must not be time limited").
5. **Sticky header note:** the F07 FAIL rests on p. 22 ER 1 (a tester sees no
   indicator); WCAG 2.2's 2.4.11 Focus Not Obscured covers the same case but is
   outside TT 5.1.3.
6. **O7 cross-referenced to 4.E**, which fails F55 under its own PDF step.

## Decided (Abby, 2026-10-31)

- **4.D O7 / F55:** an element that drops focus as soon as it gets it fails in
  4.D (new row M3, later rows renumbered; 4.D 0.4.0) and in 4.E (M7).
- **4.F J1:** the agent decides whether a signalled order makes sense; only
  "unsure" goes to a person. Its "preserves" gives PASS and "does not matter"
  gives DOES NOT APPLY, explained and overridable (4.F 0.2.0). Principle 8 now
  allows this for spec-designated look-and-decide questions, with "unsure"
  required whenever the evidence does not settle it.
- **4.F triggers:** the first 6 in forward order.

Second round (Abby, 2026-10-31):

- **4.D widget items** (roving tabindex and aria-activedescendant) are tested,
  not noted: WAI-ARIA 1.2 says the active descendant "is treated as having
  keyboard focus in the user interface" and the author must style it; the ARIA
  Authoring Practices say to move the visual focus indicator with the arrow
  keys; TT 4.C navigates with arrow keys and 4.D continues from it. New widget
  pass W: up to 5 items per widget, 10 widgets per page, sharing 4.C's widget
  replay (4.D 0.5.0).
- **4.D fading indicator:** not tested, a known limit.
- **4.E dialog on focus:** the agent decides from before/after images (new J1,
  look-and-decide); only unsure goes to a person (4.E 0.2.0).
- **4.E warned changes:** no exception.
- Written in as recommended (say if you disagree): **4.E** focus pulled back
  by the element just left is not a 4.E instance (4.C judges it); **4.F** DNA
  is mechanical only for a single-stop page (4.F 0.3.0).

## Shared build work these specs need

- **Widget pass W** (4.D), sharing one replay per widget with 4.C's P4.
- **A walk extras hook** (all three): a check declares per-step extras, the
  walk collects the union, and running 4.C alone collects none.
- **A richer focus log** (4.E; also helps 4.C and 4.D): trusted flag, CSS path,
  `relatedTarget` containment.
- **Pass R** (4.F): opening triggers, as a shared collector 4.C can opt into
  later.
- **A DNA page row** (4.F) in the engine's shared page table, or per-check page
  rows.
- **Time:** 4.C plus these three must fit one call's 120 s on a typical page.
  The estimates are 4.D about 10 s per 100 stops, 4.E near zero, and 4.F about
  15–30 s. That is to be measured once built.
