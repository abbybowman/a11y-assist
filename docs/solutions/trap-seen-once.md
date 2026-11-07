# A trap seen on one load: pages that differ from load to load

**Problem.** Artemis III's Tab walk sometimes ended "loop" after 9-13 presses, against about 80 otherwise (development run 12, and 1 of 4 replays of the same frozen recording). Every test that reads the walk then went to NEEDS REVIEW. The ROADMAP guessed the video player.

**Cause.** A "Was this page helpful?" survey dialog (Popup Maker, `#pum-872473`, `role=dialog`, `aria-modal="false"`). The page's own script shows it on about one session in ten (`popupData = {"randomChance": "0.1"}`, `Math.random() < randomChance`, decided once per session cookie). It opens 5 s after load (`auto_open`, `delay: 5000`), takes focus and keeps Tab and Shift+Tab inside it ("#popmake-872473 > div", the "Yes" radio, "Submit", "Close"). The loop check was right about that load. The trouble is that every other load of the same recording rolls the dice again: P2, every probe and every check's replay.

**How we found it.** Round 1's committed report (`evals/judging/round1/results/arm-a-1/runs/20261104T130019Z-ac01df/report.json`) names the loop's stops. The recording itself is in an offline archive, so the page was frozen again (2026-11-07). Today's page has no video player and 75 stops; 10 replays all wrapped. With the survey's own session cookie (`pum_random_display_decision=show`) set on every load, P1 ended "loop" after 20 presses and P2 after 16, on the same four stops.

**What we do now (4.C 1.9.0).** A trap event ends a pass only when a second pass from a fresh load ends in the same trap (stops matched by frame chain plus CSS path, since node IDs change per load). Otherwise the second pass is the walk's pass and the first is kept as `unrepeated`. 4.C adds that trap as an instance seen once: it is never probed and never asked about, and row M1 leaves it for a person. A real trap repeats, so it costs one more pass up to the trap.

**How we know.**
- `tests/test_walk.py` covers three schedules on F36, a page whose survey opens on the loads a cookie chooses: shown on the first load only (the walk wraps, the loop is kept), shown on every load (confirmed), and never shown (no second pass).
- `tests/test_fixtures_4c.py` covers the outcomes: F36 shown on the walk's first load only is NEEDS REVIEW (M1); shown on every load it is PASS by its close button (M4).
- Replaying the new Artemis III recording (2026-11-07) 20 times with the 4.x and 5.x walk extras, with the survey's cookie set on the first load of each walk: all 20 walks reached the whole page (75 stops, wrap). On 10 of them a first pass met the survey (7 first P1s, 3 first P2s; the cookie did not always make it open) and was kept as an unrepeated loop on the four survey stops. On the old code, with the survey on every load, P1 ended "loop" after 20 presses and P2 after 16.

**What is left.** A check's own replay can still meet the dialog on about one load in ten; a check that verifies where focus arrived goes to NEEDS REVIEW then, and one that does not may read the dialog. Each check's probes are short, and the dialog opens 5 s after load, so few are affected; not measured.

**Testing a page that differs per load.** The test server serves a page once and runs replay from the recording, so randomness cannot come from the server. Let the page decide from a cookie, as the real one does, and let the test set the cookie on the loads it chooses (a wrapped `new_page`, or `capture.new_context`).
