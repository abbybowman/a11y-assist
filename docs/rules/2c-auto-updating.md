---
tt_test: 2.C
tt_name: 2.2.2-auto-updating
spec_version: 0.3.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 2.C (2.2.2-auto-updating)

The tool gives each page one 2.C outcome: PASS, FAIL, DOES NOT APPLY or
NEEDS REVIEW. It never emits NOT TESTED (p. 6). **PASS is gated** (Abby,
2026-11-03): a working mechanism gives NEEDS REVIEW until every test that
can apply to it is built (G4 and section 3c). This spec also defines what
2.A, 2.B and 2.D share: pass T, regions, elements and the mechanism probe.

Draft (0.3.0): no outcome until 1.0.0. 0.2.0 (2026-11-04) defines regions over the whole watch and adds polling seen during the watch (Terms, section 2), from building pass T. 0.3.0 (2026-11-04): the mechanism probe as built (section 2: what is pressed, how "slowed" is judged, the caps), K2 and K3 on the focus-only probe, O1 decided. Order of work and research:
[plans/2026-11-03-auto-updating-2a-2d.md](../plans/2026-11-03-auto-updating-2a-2d.md)
("plan" below; "item N" means its numbered "Verified" items).

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/2.C`). Identify Content, p. 15: content that "Automatically updates (the content changes without user activation) AND Is not the only content on the page"; it "includes timers, stock tickers, news carousels, and counters"; none: DNA for 2.C and 2.D. Note, p. 15: "the tester is not tasked with determining whether auto-updating is essential and should include all content that meets the Identify Content description"; when content moves without changing, only 2.B applies; when it changes (a carousel, tickers, scores), 2.C applies; both when both. Applicability, p. 15: DNA "if there is no auto-updating content or the auto-updating content is the only content on the page". HtT 1 ("an evident mechanism ... to pause, stop, or hide the content or to control the frequency of the update within the first three elements that the user would encounter OR within three elements before/after the auto-updating content"), HtT 2 (activate it), HtT 3 (test the mechanism for all applicable Test Conditions), p. 15. ER 1 (an evident mechanism that pauses, stops, hides or controls the frequency), ER 2 (where it is), ER 3 (it "passes all applicable Test Conditions"), p. 16.

**Other sources.** [Understanding 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html): auto-updating is content "that updates or disappears based on a preset time interval" (weather, news, stock prices, auto-advancing presentations); starting on focus, hover or scrolling into view counts as starting automatically; a pause must not "tie up the user or the focus"; streamed content need not keep what was produced during a pause (Note 3). Sufficient [G4](https://www.w3.org/WAI/WCAG22/Techniques/general/G4) (pause; it does not restart by itself; resume), [G186](https://www.w3.org/WAI/WCAG22/Techniques/general/G186) (a control that stops it; check that it stopped). W3C ACT [efbfc7](https://www.w3.org/WAI/standards-guidelines/act/rules/efbfc7/) (proposed): DHS scored all 11 cases under 2.C and agrees with ACT on every one (act-tt data, checked 2026-11-03). ICT Testing Baseline 3.1 [21.C-AutoUpdate](https://ictbaseline.access-board.gov/web-baselines/21TimedEvents/) (no position rule; essential excluded, which the TT does not do). No Baseline Alignment cases. DHS's course FAQ ([#114](https://github.com/Section508Coordinators/DHSA-TT-200-A/issues/114)): "Mechanism is specifically defined to include any element, including text or images."

**Terms** (shared by 2.A–2.D).

- *Pass T*: one fresh load of the recorded page, watched with no input
  for 6.5 s (section 2). It runs in the batch's own browser: full
  Chromium, headless, with autoplay allowed (Abby, 2026-11-03, plan
  Q1/Q11).
- *Frame*: a viewport screenshot taken by pass T (about every 0.5 s,
  through `traverse.screenshot()`).
- *Region*: a group of 20 px tiles that changed in any frame of the watch
  and touch one another, mapped once, at the end of the watch, to the
  smallest element whose box covers their changed pixels (by overlap, with
  4 px of slack for a focus ring drawn just outside its element; in every
  frame of the page, iframes included). Built rules (0.2.0):
  - The groups are taken over the whole watch, not frame by frame: per
    frame, a spinning square's changed pixels landed sometimes on the
    square and sometimes on its box, and slides taking turns gave one
    region per slide.
  - An element covers the group only if it also covered it at the first
    read, so content that moved there (the slide in view at the end of a
    sliding carousel) does not.
  - When the group's changed pixels fall in two or more of that element's
    children, one child each, each child's part is its own region (two
    widgets side by side).
  - An element that was not on the page at the first read (replaced every
    second) gives way to its nearest ancestor that was.
  - A frame where more than half the viewport's tiles changed (a dialog's
    backdrop, a scroll) is noted as a page-wide change and not mapped.
  - When that element is inside a carousel (an ancestor with
    `aria-roledescription="carousel"`, or a known carousel container:
    Slick, Splide, Swiper, Bootstrap, Glide, Flickity), the region and its
    *content* are the whole carousel, its own controls included (Abby,
    2026-11-03). USWDS has no carousel component, so none is listed for
    it.
  - Otherwise the content is the region's element.
- *Kind*:
  - A region is *auto-updating* when its visible text, the image sources
    it shows (`currentSrc`, CSS background image) or its rendered children
    change during pass T.
  - It is *moving* when its pixels change but those do not.
  - It can be both: auto-updating, and its children also move (their
    boxes shift between frames without a text change).
- *Element* (Abby, 2026-11-03, plan Q6): what a screen reader reads as
  one unit, in reading order. These are the units of `site.UNITS_FN`
  (text, headings, images with alt text, controls), with these rules:
  - A `<label>` that names a control is the same element as the control
    when their boxes share a line (vertical overlap of half the smaller
    height), and its own element when stacked above it.
  - Each data-table cell is its own element.
  - An iframe's content is read in its own frame and counted inline at the
    iframe's place.
  - Content with `aria-hidden="true"`, or inside such content, is not an
    element.
  - An image with empty or no alt text is not an element.
- *Windows*:
  - the *top window* is the page's first three elements;
  - the *before window* is the three elements before the content's first
    element;
  - the *after window* is the three elements after its last;
  - the *inside* is the content's own elements.
- *Candidate*: an element in a window this test uses (2.A: the top window
  only; 2.B and 2.C: all of them).
  - A *control candidate* is a control: a button, link, form element, or
    anything with a widget role or `tabindex` ≥ 0.
  - A *text candidate* is text or an image.
- *Period*: the time between a region's changes in pass T (the median).
  When the timer hooks saw an interval longer than the watch, that
  interval is used instead (item 7).

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | Pass T could not run or read the page (load, frames or reads failed) | NEEDS REVIEW, not performed, with the reason | p. 5; spec rule |
| A2 | No instance (an auto-updating region still changing at 5 s; OPEN O1 below), but a *hint* that updates exist: the HAR has repeated requests to one address after load (polling, item 10); a timer with a period longer than the watch (item 7); carousel markup that did not change; an auto-updating region that stopped changing before 5 s; or the walk kept finding the page changing (built: at least three walk steps whose DOM never settled; a menu a press opens settles, so it is not counted) | NEEDS REVIEW, not performed: "the page may update more slowly than we watched, or with data a recording cannot replay; a person should watch it" | p. 15 Identify Content; plan risks 4–5 |
| A3 | No instance | DOES NOT APPLY | p. 15 Applicability |
| A4 | Every element of the page (all read) is inside an instance and its box overlaps pixels that changed there (0.3.0: inside alone is not enough, since a focus ring once made a region of `<main>` whose heading never changed; a tag rule instead failed ACT efbfc7 inapplicable 5, a page that is only a changing number) | DOES NOT APPLY: it is the only content | p. 15 Applicability |
| A5 | Otherwise | Applies; go to section 3. A hint (A2) about other content is a note | |

Not essential: 2.C never excludes content as essential (p. 15 Note).

**O1: content that stopped changing before 5 s** (Abby, 2026-11-04: keep
as built, and the note says what was checked). TT gives 2.C no duration.
The rule: an auto-updating region is an instance only when
it is still changing at 5 s; one that stopped earlier (a spinner replaced
by content at 1.5 s, a late load, or a carousel slower than about 2.5 s
whose second change fell after the watch) is a hint, so the page is NEEDS
REVIEW (A2), never DOES NOT APPLY. The cost: pages with late-loading
content become NEEDS REVIEW instead of DOES NOT APPLY. The A2 note says
how long we watched, that we looked for content still changing after 5 s,
and names each content that changed and when it stopped.

## 2. Evidence to collect

**Pass T** (`motion.py`, shared with 2.A, 2.B and 2.D, `RunContext.cache["motion"]`; starts beside the walk's P1, plan Q2):

- **Setup.** One fresh load of the recorded page, in the batch's browser,
  with these added by init scripts before page scripts run (plan Q7):
  - a mutation log with targets (node path, kind, text before and after,
    capped);
  - timer hooks (`setInterval` and `setTimeout` periods of 1 s or more);
  - the Web Audio connect hook (2.A).
- **Frames** every 0.5 s for 6.5 s. From them come the regions, each with
  the times it changed and its kind.
- **Reads** at 0 s, 3.5 s and 6.5 s, for each region:
  - its visible text and the image sources it shows;
  - its children's boxes;
  - `getAnimations()` on it.
- **Polling.** Requests repeated to one address: in the HAR, and fetch,
  XHR or event-stream requests repeated during pass T. Recording stops
  once the network is idle, so a page polling every 0.7 s left only one
  or two polls in the HAR; the watch saw nine.
- **For 2.D:** the live regions present at 0 s (section 2 of
  [2d-change-notify-auto.md](2d-change-notify-auto.md)), the focus log and
  open dialogs.
- **Elements** of the page (Terms), read once at 0 s.
- **Scrolled watch** (plan Q3): when a hint points to content below the
  first viewport, one more 6.5 s watch with that content scrolled into
  view, on a fresh load. Built (0.3.0): the hints are elements the page
  observes for scrolling into view (`IntersectionObserver`), and carousels,
  below the first viewport and inside no region found; the first one is
  scrolled to, and the regions the second watch finds join pass T's,
  marked scrolled. Content below the first screen that keeps changing
  without being scrolled to is found by pass T itself (DOM log, animations,
  marquees, videos, animated images).

**Mechanism probe** (HtT 1–2; shared with 2.A and 2.B), per content, on fresh loads in the batch's browser (`ctx.replay`, `observe.py`):

1. **Control candidates**, nearest to the content first, then the top
   window:
   - A fresh load with focus on the candidate. A candidate the walk never
     reached is unreachable and is noted. One the walk reached, in the top
     page, is focused directly (0.3.0, T1: replaying every Tab press to a
     ticker at the bottom of a page cost 28.7 s); a media element's own
     controls and controls in frames get the walk's Tab presses.
   - Press Enter, or Space for a checkbox or switch. A slider gets Home,
     then End, then arrow keys.
   - Move focus off it with Tab.
   - Watch the content for its *confirm time*: max(5.5 s, 1.5 × period),
     at most 15 s. The watch stops at the first change.
2. **The focus-only probe** for a candidate that held: the same replay
   to the candidate, no key pressed, focus moved off, the same watch.
3. **Text candidates** go to J2. If J2 gives a key combination, the
   combination is pressed once on a fresh load, then the same watch
   (Abby, 2026-11-03, plan Q10: an approved exception to principle 5).
   The press is skipped, with a note, when the combination is not
   modifiers plus one key, or is one the browser itself uses (Ctrl+W,
   Ctrl+T, Ctrl+N, Ctrl+L, Ctrl+Q, Alt+F4, Alt+Home).
4. **Stop early.** The probes stop once a candidate holds and the
   focus-only probe did not stop the content. The number of candidates
   left untried is recorded.

A probe's result for the content (`mechanism.py`, as built in 0.3.0):

- *Stopped*: no change during the confirm time, or the content is no
  longer rendered (hidden).
- *Slowed*: it changes, but every time between two changes, and the quiet
  after the last one, is at least 1.5 times its period (a frequency
  control). Never judged on the first change alone: where the watch starts
  in the content's cycle is chance, and a 1 s ticker's first change came
  1.6 s in.
- *No effect*: two changes closer than 1.5 times its period, or any change
  when pass T measured no period.
- *Unreliable*: the replay failed, the content could not be found, or the
  page navigated away.
- *Unreachable*: the walk never focused it, or the replay ended elsewhere.

Not pressed:

- a text field, search box, combo box, spin button or list box: it needs a
  value (K5, naming it);
- a link whose href goes somewhere (not `#` or `javascript:`): following it
  is not pausing, so it is not a mechanism (K6 counts it with no effect).

Caps (reaching one is K7): 8 control candidates per content, 3 contents per
page. The probe looks at the content's own pixels (an element screenshot)
every 0.5 s, after 0.6 s for transitions to end; focus moves off with Tab.
Content with no element inside it cannot be placed among the elements, so
its before and after windows are unknown (K7). Controls inside iframes are
matched to the walk's stops by frame URL and path.

**Time budget.** Pass T runs beside P1 at no measurable cost (item 18).
The probes cost ~1–2 s per candidate rejected within one period, plus
2 × confirm time for the candidate that holds. Pages with a region get an
extra allowance (plan Q2; size set when measured on the budget page with a
carousel). Checks call `ctx.out_of_time()` before each probe.

## 3. Mechanical checks

Each auto-updating region whose content is not excluded is an *instance*.

**3a. Instance rules (first match wins).** Rows K1–K8 are the mechanism rows; 2.A and 2.B use them with their own windows and meaning of stopped.

| # | Evidence pattern | Instance outcome | Source |
| --- | --- | --- | --- |
| K1 | The content's reads failed, or no candidate held and some probe was unreliable | NEEDS REVIEW | Spec rule |
| K2 | A control candidate stopped or slowed the content, and its focus-only probe also stopped or slowed it (0.2.0: slowed counts; a carousel that resumes when focus leaves it read as slowed both ways) | NEEDS REVIEW: "it stops when the control is focused, which may be a pause on focus; a person should check that the control itself pauses it" | Understanding 2.2.2 (a pause must not tie up focus); plan item 12 |
| K3 | A control candidate stopped (or, for 2.C, slowed) the content, and its focus-only probe saw no effect (a focus-only probe that failed proves nothing: K8) | *Works*; go to J1 (evident) | p. 15 HtT 1–2; G186; G4 |
| K4 | A key combination from J2 stopped or slowed the content | *Works*; go to J1 | p. 15 HtT 1 (any element; DHS #114); plan Q10 |
| K5 | J2 named a mechanism the tool cannot try (a combination it may not press, a field that needs a value, a control outside the windows) | NEEDS REVIEW, naming it | Spec rule |
| K6 | Every control candidate gave no effect, J2 = no for every text candidate (or there are none), and nothing was left untried | No mechanism: FAIL | p. 16 ER 1–2 |
| K7 | The probe has not run (it is not built yet), or control candidates were left untried (time, or a candidate the walk never reached). Text candidates are asked about (J2), never pressed, so they do not count here | NEEDS REVIEW | p. 5 |
| K8 | Anything else (J2 unsure or unanswered) | NEEDS REVIEW | Spec rule |

After K3 or K4:

| # | Evidence | Instance outcome | Source |
| --- | --- | --- | --- |
| E1 | J1 = not evident | FAIL: the mechanism works but is not evident | p. 16 ER 1 ("an evident mechanism") |
| E2 | J1 = evident, and section 3c finds every applicable test built, run in this call and not failing at the mechanism | PASS | p. 16 ER 1–3 |
| E3 | J1 = evident, otherwise | NEEDS REVIEW: "the control works; a person must still check it against <tests not yet built or not run>" | p. 16 ER 3; Abby, 2026-11-03 (plan Q4) |
| E4 | J1 unsure or unanswered | NEEDS REVIEW | Spec rule |

**3b. Page outcome (first match wins)**

| # | Evidence pattern | Page outcome |
| --- | --- | --- |
| G1 | Section 1 gives DOES NOT APPLY or NEEDS REVIEW | That outcome |
| G2 | Any instance is FAIL | FAIL, listing every instance |
| G3 | Any instance is NEEDS REVIEW, or time ran out | NEEDS REVIEW, with the note "This test could not be performed" and the reason (p. 5) |
| G4 | Every instance is PASS | PASS |
| G5 | Anything else | NEEDS REVIEW |

**3c. ER 3: the tests a mechanism needs** (Abby, 2026-11-03, plan Q4). The mechanism must pass "all applicable Test Conditions" (p. 16 ER 3). A test applies to it as follows; names come from `tt.json`:

| Test | Applies when the mechanism | Built (2026-11-03) |
| --- | --- | --- |
| 4.A, 4.B, 4.C | is operated | yes |
| 4.D, 4.E, 4.F | takes focus | yes |
| 5.A, 5.B, 5.C, 5.D | is a form element (toggle, slider, field) | yes |
| 6.A | is a link or a button | no |
| 7.A, 7.E | is, or contains, an image or icon | no |
| 12.D | is inside an iframe | no |
| 13.A | shows its state (playing, paused) by color | no |
| 13.B | is a text instruction | no |
| 13.C, 18.A | has, or is, text | no |

E2 holds only when every applicable test is registered, was selected in
this call, and its finding has no FAIL instance at the mechanism's element.
While any applicable test is not built, E3 applies; its note lists them.
A built test's FAIL at the mechanism is named in the note.

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| Page PASS | "<content> changes by itself, and <mechanism> lets users pause it." |
| E3 | "<content> changes by itself, and <mechanism> pauses it when pressed with the keyboard. A person still needs to check <mechanism> for <tests>, which this tool does not test yet." |
| K6 | "<content> changes by itself, and we found no way to pause, stop or hide it in the three items before it, the three after it, or the first three on the page. Add a pause button next to it." |
| E1 | "<mechanism> pauses <content>, but it is not clear that it does (its name or icon does not say so). Give it a clear name like "Pause"." |
| K2 | "<content> stops while <mechanism> has focus, which may be a pause-on-focus rather than a real pause. A person should check that the control itself pauses it." |
| A2 | "We saw signs that this page updates by itself (<hint>), but nothing changed while we watched. A person should watch the page for a minute." |
| A3 | "Nothing on this page changed by itself while we watched, so this test does not apply." |
| A4 | "The changing content is the only content on this page, so this test does not apply." |

## 4. Judgment questions

J1 is settled by looking (CLAUDE.md principle 8, to be added at 1.0.0):
the key press that stopped the content is the mechanical check. The agent
judges only whether a user would recognize the control, and answers unsure
whenever the evidence does not settle it. J2 never leads to PASS on its
own: a key press must confirm it (K4).

### J1. Is the mechanism evident?

**Question:** "Pressing input.mechanism stopped the content in input.content (image A shows the content and the control). Would a user looking at the page recognize this control as a way to pause, stop, hide, or slow the changing content? Answer evident, not_evident or unsure."

**Input:** a crop around the control and the content; the control's accessible name and role; where it is (inside the content, N elements before or after it, or Nth on the page).

**Output:** `{choice: evident|not_evident|unsure, reasons}`.

**Rubric.** evident: its visible name or icon says pause, stop, hide, play/pause or slower, and it is in view with the content or at the top of the page. not_evident: it says something else ("Menu", "Next"), or has no visible name or icon. unsure: whenever the image does not settle it.

**Use:** E1–E4.

### J2. Does this text describe a way to pause, stop or hide the content?

Asked only for text candidates whose text mentions pausing, stopping, hiding, a key, or a control (a key name with `+`, "hotkey", "shortcut", "pause", "stop", "hide", "freeze", "turn off", and, from 0.3.0, "control" and "button": ACT efbfc7 passed 5 names its control only as "activate the "Control changes" button"); other text candidates are "no" mechanically.

**Question:** "input.text is page text near the changing content (input.position). Does it tell users how to pause, stop, hide or slow that content? If it names a key combination, put it in key exactly as written. Answer describes, no or unsure."

**Output:** `{choice: describes|no|unsure, key, quote, reasons}`. Guard: the quote must be found in input.text, and a key must parse as modifiers plus one key; else NEEDS REVIEW.

**Use:** K4–K6, K8.

## 5. Edge cases

V-numbers are in [2c-build-tasks.md](2c-build-tasks.md).

| Case | Rule | Verify |
| --- | --- | --- |
| A carousel that pauses on focus or hover (Slick, Splide) | K2, never PASS; pass T has no pointer over the page | V6 (plan item 12) |
| A carousel slower than the watch (8–10 s per slide) | The timer hook's period; A2 when nothing changed | V4 |
| A ticker fed by polling | A2 (the replay repeats the first response) | V5 (plan item 10) |
| A control inside the carousel (its own pause button) | Inside the content: a candidate | Abby, 2026-11-03 |
| A frequency field that needs a value (ACT efbfc7 passed 4) | K5, naming the field | ACT efbfc7 |
| A control that opens a dialog of controls (ACT efbfc7 passed 5) | The opener has no effect on its own: K5 when J2 or the opener's name points to it; a person checks | ACT efbfc7 |
| A timer or counter in an iframe | Regions and elements are read in every frame; iframe content counts inline | V7 |
| Content that starts only when scrolled into view | The scrolled watch (plan Q3) | V4 |

## 6. What a FAIL records

For each instance:

- the content (its element, a crop at two times, its period);
- every candidate, with its window, position, probe result and row;
- the J1 and J2 answers;
- how to reach each candidate ("Tab 4 times, then Enter").
