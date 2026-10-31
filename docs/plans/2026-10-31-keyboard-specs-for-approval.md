# For approval: 4.D, 4.E and 4.F specs

Status: **drafts awaiting Abby.** No code is written for them yet. Draft
specs (version 0.x) load and are recorded in reports, but give no outcome
until a check is registered.

| Spec | Version | Written by |
| --- | --- | --- |
| [4d-focus-visible.md](../rules/4d-focus-visible.md) | 0.3.0 | 4.D thread (0.2.0), reviewed and edited here |
| [4e-on-focus.md](../rules/4e-on-focus.md) | 0.1.0 | this thread |
| [4f-focus-order-meaning.md](../rules/4f-focus-order-meaning.md) | 0.1.0 | this thread |

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

## Decisions needed

| # | Spec | Question | Recommendation |
| --- | --- | --- | --- |
| 1 | 4.D O5 | aria-activedescendant widgets: note only, or arrow through them? | Note only |
| 2 | 4.D O7 | Element that drops focus on focus (F55): FAIL in 4.D too, or only in 4.E? | Both (F55 counts it against both) |
| 3 | 4.D O8 | Indicator that disappears after a few seconds: not tested, or a late image? | Not tested, listed as a known limit |
| 4 | 4.E O1 | Is a change of context on focus ever "expected" (e.g. warned about)? | No exception (WCAG 3.2.1 has none) |
| 5 | 4.E O2 | Focus pulled back by the element just left: 4.E instance or not? | Not 4.E (the target did not initiate it; 4.C judges it) |
| 6 | 4.E M8 | A dialog that appears on focus without taking focus: NEEDS REVIEW for a person, or ignore? | NEEDS REVIEW (false PASS is the worst error) |
| 7 | 4.F O1 | The agent says the order "preserves meaning" despite a signal: PASS, or NEEDS REVIEW until a person confirms? | NEEDS REVIEW with the agent's recommendation; a person's answer gives PASS |
| 8 | 4.F O2 | DNA from p. 23 Note 2: only for a page with one stop? | Yes, only one stop |
| 9 | 4.F O3 | Opening triggers (HtT 2.b, "may be necessary"): first 6, dialogs and menus only, or none? | First 6, revisit after real pages |

Decision 7 is the one that most affects users: with it, multi-column pages
will often end NEEDS REVIEW with "we think it still makes sense; please
confirm", which a person can settle in one answer.

## Shared build work these specs need

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
