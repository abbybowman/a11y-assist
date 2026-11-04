---
tt_test: 2.A
tt_name: 1.4.2-audio-control
spec_version: 0.2.0
source: DHS Section 508 Conformance Test Process for Web (Trusted Tester) v5.1.3, April 2024
owner: Abby Bowman
---

# Rules spec: Test 2.A (1.4.2-audio-control)

The tool gives each page one 2.A outcome: PASS, FAIL, DOES NOT APPLY or
NEEDS REVIEW. It never emits NOT TESTED (p. 6). PASS is gated as in 2.C:
a working mechanism gives NEEDS REVIEW until every test that can apply to
it is built ([2c-auto-updating.md](2c-auto-updating.md) section 3c).

Draft (0.2.0): no outcome until 1.0.0. 0.2.0 (2026-11-04), from building
it (`checks/t2a.py`, `mechanism.audio_watch`, the media store in
`capture.py`):

- A media element's own controls (`controls`) are one control element at
  its place in reading order; the walk's stop on its play button inside
  the element reaches it (V1, verified: Enter pauses it).
- Media that reached its end during the probe is "unreliable", never
  stopped: a clip that ran out must not be credited to a control.
- The media store keys files without their `#fragment`, so a file played
  from `#t=8,10` can seek on replay (ACT 80f0bf passed 2; before this it
  played from 0 s and was a false FAIL).
- Loudness is the peak of the whole file (not only the part that plays).
- 2.C's J2 trigger words gain "mute", "volume", "sound" and "audio".
- Audio in an iframe is read in its frame, but the probe does not yet find
  that frame again (V7 for audio: not built). Plan:
[plans/2026-11-03-auto-updating-2a-2d.md](../plans/2026-11-03-auto-updating-2a-2d.md).

**Citations.** Printed pages of TT 5.1.3 (text also in `tt://5.1.3/tests/2.A`). Identify Content, p. 13: before loading, "make sure the browser is not set to block auto-playing content"; audio that "automatically plays (without user activation) for more than 3 seconds" (alerts, sounds, music); none: DNA. Applicability, p. 13. HtT 1 ("a mechanism within the first three elements encountered for the user to pause or stop the audio or to control the volume of only the auto-playing audio"; 1.a the browser allows autoplay), HtT 2–3, p. 13. ER 1 (a mechanism that pauses, stops or controls the volume of only the auto-playing audio), ER 2 ("within the first three elements encountered by the user"), ER 3 (it passes all applicable Test Conditions), p. 13. Notes, p. 13: three elements "for clear measurability" ("the mechanism can be a focusable element or text instructions at the top of the page prior to repetitive content"); a browser's ability to disable autoplay or mute a tab is "acceptable", but not all browsers have it. Appendix B: 5.1.3 changed setup to a browser that does not block autoplay (TT 5.0 said to disable it).

**Other sources.** [Understanding 1.4.2](https://www.w3.org/WAI/WCAG22/Understanding/audio-control.html): "Muting the system volume is not 'pausing or stopping'"; volume control "includes being able to reduce its volume to zero"; plays automatically means not started by the user's intentional activation. Sufficient G60 (sound stops within 3 s), [G170](https://www.w3.org/WAI/WCAG22/Techniques/general/G170) (a control near the beginning of the page), G171; failures [F23](https://www.w3.org/WAI/WCAG22/Techniques/failures/F23), [F93](https://www.w3.org/WAI/WCAG22/Techniques/failures/F93) (`autoplay`, no `muted`, > 3 s, no control). W3C ACT 80f0bf, [4c31df](https://www.w3.org/WAI/standards-guidelines/act/rules/4c31df/), aaa1bf (all proposed); DHS scored none (act-tt data, checked 2026-11-03). ICT Testing Baseline 3.1 21.D-AudioControl ("at the beginning of the page content or in platform accessibility features"; it says to disable autoplay before testing, which TT 5.1.3 reverses). No Baseline Alignment cases. DHS course FAQ ([#114](https://github.com/Section508Coordinators/DHSA-TT-200-A/issues/114)): any element, text included, can be the mechanism.

**Terms.** Pass T, element, top window, candidate, the mechanism probe and rows K1–K8, E2–E4: [2c-auto-updating.md](2c-auto-updating.md) (Terms, sections 2 and 3).

*Auto-playing audio* is any of these at 3.5 s into pass T, with no key
pressed:

- **A media element**, in any frame, that:
  - is not paused, not muted, and has volume above 0;
  - is advancing (`currentTime` grew since the 0 s read);
  - is audible: the recorded bytes, decoded in a tool page (never the
    tested page) with `OfflineAudioContext.decodeAudioData`, have samples
    above -40 dBFS within the part that plays;
  - plays for more than 3 s: its duration from where it started is over
    3 s, or it loops.
- **Web Audio:** a node was connected to an `AudioContext` destination
  (connect hook), and that context is `running`.

The mechanism must act on that audio only:

- for a media element: paused, muted, or volume 0;
- for Web Audio: the context suspended or closed.

Changing the page's other sound, or the system volume, does not count.
For 2.A, *stopped* means one of these holds for the 3.5 s after the
probe's focus leaves the control. The confirm time is 3.5 s.

## 1. Applicability

| # | Evidence | Outcome | Source |
| --- | --- | --- | --- |
| A1 | Pass T could not run or read the page | NEEDS REVIEW, not performed, with the reason | p. 5 |
| A2 | Media that would play could not be measured: an `error`; a streaming player (an iframe from youtube.com or player.vimeo.com with `autoplay=1`, or an MSE `blob:` source); media over the recording cap; or Web Audio (no bytes to measure) | NEEDS REVIEW, not performed. For media over the cap the note gives each file's size and length, and the result offers a run with no time limit (Abby, 2026-11-03, plan Q9). Streaming players: "a person should load the page and listen" | plan items 13–14, 17 |
| A3 | No auto-playing audio | DOES NOT APPLY | p. 13 Applicability |
| A4 | Otherwise | Applies; go to section 3 | |

A2 applies only when no measurable audio applies (A4). When both are
present, the unmeasured media is a NEEDS REVIEW instance.

## 2. Evidence to collect

**Pass T** (2.C section 2), whose reads add:

- for each media element in every frame: paused, muted, volume,
  `currentTime` at 0 s and 3.5 s, duration, loop, `error` and
  `currentSrc`;
- the Web Audio connect hook's count and each context's state;
- the loudness of each media source from its recorded bytes. The media
  store keeps media in full up to 50 MB and 15 s per page (plan Q9); a
  file over the cap is sized from `Content-Length` or `Content-Range`, and
  its length comes from `duration` once metadata has loaded.

**The mechanism probe** (2.C section 2) with the top window only (ER 2),
2.A's meaning of stopped and its 3.5 s confirm time. Text candidates in
the top window go to 2.C's J2. Browser features (tab mute, an autoplay
setting) are not candidates (Abby, 2026-11-03, plan Q5): ER 2 asks for
the mechanism within the first three elements, and a page cannot mute its
own tab.

**Time budget:** none beyond pass T, plus at most three candidates.

## 3. Mechanical checks

Each auto-playing audio (a media element or an `AudioContext`) is an *instance*; one control can serve several.

**3a. Instance rules.** Rows K1–K8 of [2c-auto-updating.md](2c-auto-updating.md) section 3a, first match wins, with the top window only and 2.A's meaning of stopped. "Slowed" is no effect. After K3 or K4, 2.A asks no "evident" question (ER 1 does not say evident):

| # | Evidence | Instance outcome | Source |
| --- | --- | --- | --- |
| E2 | Section 3c (2.C) finds every applicable test built, run in this call and not failing at the mechanism | PASS | p. 13 ER 1–3 |
| E3 | Otherwise | NEEDS REVIEW: "the control works; a person must still check it against <tests>" | p. 13 ER 3; plan Q4 |

**3b. Page outcome.** As [2c-auto-updating.md](2c-auto-updating.md) section 3b, G1–G5.

**Notes (no outcome).** "Chrome can mute a tab, but the TT asks for a control within the first three elements of the page, so a tab mute does not count here."

**Plain-language sentences.**

| Row | Sentence |
| --- | --- |
| Page PASS | "Audio plays by itself when the page loads, and <mechanism>, near the top of the page, stops it." |
| E3 | "Audio plays by itself, and <mechanism> stops it when pressed with the keyboard. A person still needs to check <mechanism> for <tests>, which this tool does not test yet." |
| K6 | "Audio plays by itself for more than 3 seconds, and nothing among the first three items on the page stops it or turns it down. Screen reader users hear it over their screen reader. Put a pause or mute button first on the page, or do not start the audio until the user asks." |
| A2 | "This page has media we could not play from our recording (<why>). A person should load the page and listen." |
| A3 | "No audio played by itself for more than 3 seconds, so this test does not apply." |

## 4. Judgment questions

None of its own. Text candidates use 2.C's J2 (a stated key combination is pressed to confirm, plan Q10).

## 5. Edge cases

| Case | Rule | Verify |
| --- | --- | --- |
| A video with a silent audio track (ACT 80f0bf inapplicable 2) | Not audible by loudness: not an instance | V2 (plan item 4) |
| Audio that stops by itself within 3 s (G60; ACT aaa1bf) | Not more than 3 s: not an instance | V2 |
| `<audio autoplay muted>` | Muted: not an instance | ACT 80f0bf inapplicable 1 |
| Native controls on the media element (`controls`) | Its play/pause button is an element: a candidate when in the top window (ACT 4c31df passed 1, 2) | V1 |
| Audio in a cross-site iframe | Read in its frame; its controls are elements inline | V7 (plan item 16) |
| A volume slider | Home, End, arrows; works only if volume reaches 0 (Understanding 1.4.2) | V9 |

## 6. What a FAIL records

For each instance:

- the media (source, duration, loudness, frame);
- the first three elements of the page, each with its probe result and
  row;
- how to reach them.
