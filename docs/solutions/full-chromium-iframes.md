# Full Chromium for pages with cross-site iframes

**What happened.** Playwright's `"chromium"` channel in headless mode is the
*headless shell*, which runs cross-site iframes in the page's own process.
Full Chromium and installed Chrome run them out-of-process, as users' Chrome
does. So a run in the shell (the tests, containers, a hosted deployment)
never exercised the out-of-process path. This was found on the 2.A-2.D plan
branch (`plan-2a-2d-auto-updating`, its Q11 and experiments 15 and 16),
measured on 2026-11-03.

**What we do now.**

- `capture.record` lists frames on another host than the top page
  (`Capture.cross_site_frames`). "Another host" is wider than Chrome's site
  (same registrable domain), so a same-site subdomain also counts. That
  costs only a slower replay, never a different one.
- `browser.replay_in_full_chromium`: when that list is not empty, and the
  configured browser is headless `"chromium"`, the page's replays run in a
  second browser launched with `channel="chromium"`. Installed Chrome is
  unchanged (already out-of-process), and so is headed `"chromium"`
  (already full Chromium).
- Each page's report records its frames and `replay_browser`.
- Recording does not depend on the browser, so the replay browser is
  chosen after recording.

**How we know.** `tests/test_full_chromium.py` replays one recording in
each browser. It finds 0 out-of-process iframe targets in the shell and 1
in full Chromium, and checks that a run records and uses full Chromium.
Cost: about 90 ms more per page load (the other branch's measurement),
paid only by pages with such frames.

**What is left.** A cross-site iframe that appears only after a click is
not seen while recording, so its page replays in the shell. Its content is
still reached, as in-process frames are.
