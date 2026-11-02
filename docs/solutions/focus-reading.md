# Read focus through CDP, not page script

**Problem.** A page can override `document.activeElement` (or move focus in a
blur handler), so reading focus from page script can be spoofed or stale.

**What we do.** `traverse.FocusReader` reads the focused node through CDP in an
isolated world, follows it into in- and out-of-process iframes and open and
closed shadow roots, and takes role and name from Chrome's accessibility tree.
Tested by `tests/test_traverse.py::test_page_cannot_spoof_focus`.

**Identity across loads.** CDP backend node IDs change on every load. Within a
load a stop is `(frame ID, backend node ID)`; across loads (probes, the two
passes) stops match by frame chain plus CSS path (`Stop.path_key`).

**Browser facts that shaped rules** (Linux Chromium; Windows Chrome not yet
checked, see `docs/rules/4c-build-tasks.md`):

- Script `focus()` pulls keyboard focus back even from the browser toolbar
  (V15), so a refocus-on-blur pair cycles in both directions.
- Tab skips an iframe with `tabindex=-1` and everything inside it (V9).

**Every focus read that decides an outcome goes through the isolated world.**
9.A first asked `page.evaluate` for `document.activeElement` after a skip
link (code review, 2026-11-02). A page that overrides that getter turned a
broken skip link into a PASS. The fix was one line: run the same script with
`s.traversal.reader.evaluate_top(...)`, where the page's getter does not
apply. That was simpler than resolving the CDP stop's path, which breaks at
shadow roots ([shadow-paths-and-contains.md](shadow-paths-and-contains.md)).
Fixture `9x/b7-fake-focus.html`. Its first version still came out FAIL on
the old code, because the next-Tab check (M6) caught it. To show a false
PASS, a fixture has to get past every later row too (no stop after the faked
landing). Run a new fixture against the old code once to see it fail.
