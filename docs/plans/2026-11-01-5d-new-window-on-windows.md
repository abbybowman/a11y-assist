# Plan: new windows missed on Windows (5.D false PASS) (2026-11-01, not started)

The first Windows runs ([solutions/windows-chrome-results.md](../solutions/windows-chrome-results.md))
found 5.D giving PASS where Linux gives FAIL on two radio pages. A false
PASS is the worst error (CLAUDE.md principle 3). The two pages have
different causes, so this plan has two parts. Its own small PR, on a
branch from `main`, before the spring cleaning resumes.

## Part 1: a new window registers after we count (understood)

**Evidence.** `5d/f04-radio-opens-window` (window opens on `change`, local
page) gives PASS in headless Chromium on Windows with the default 150 ms
settle window, and FAIL correctly with `SETTLE_QUIET_MS=600`.
`observe.observe` decides "new window" by comparing
`len(context.pages)` before and after the settle (`observe.py`,
`snapshot` and the `new_page` check). On Windows the new page can join
`context.pages` after that second count.

**Fix.** Record a new window when the browser creates it, not when it is
counted. Keep the page count as a second signal.

- First choice: the browser's own signal, which a page cannot spoof
  (the reason focus is read through CDP, see
  [solutions/focus-reading.md](../solutions/focus-reading.md)). Listen
  for Playwright's context `page` event, or CDP `Target.targetCreated`
  for a page target, from just before the action until the settle ends.
- Not chosen: logging `window.open` calls in the page's init script. That
  is in `traverse.INIT_JS` (the spring-cleaning plan keeps `traverse.py`
  untouched), it misses `target="_blank"` links and forms, and page
  script can overwrite it.
- Raising the settle window for everyone is not a fix: it costs time on
  every key press, and Windows already has less room in the 120 s budget.

**Who it touches.** `observe.py` is shared by 4.A, 4.B and 5.D. A more
reliable "new window" can only add the `new_page` effect where a window
really opened, so an outcome can move from PASS to FAIL or NEEDS REVIEW,
never toward PASS. No spec row changes: the specs already name "a new
window or tab" as an effect. Each spec's version gets a PATCH note if its
wording mentions how windows are detected; otherwise none.

**Check.**
- f04 FAILs on Windows headless and headed, and still FAILs on Linux CI.
- Every other fixture, ACT and Baseline outcome is unchanged.
- The time budget on the two realistic pages is unchanged (the listener
  adds no waiting).

## Part 2: the federal case is not timing (one focused look)

**Evidence.** Baseline TC10.C-3-fail-2 gives PASS on Windows in headless
Chromium and in headed Chrome 156, even with `SETTLE_QUIET_MS=600`. It
opens `https://www.access-board.gov/` when focus leaves the *last* radio
option. That external URL is outside the allowlist, so the navigation
guard refuses it.

**Questions, in order; stop at the first one that answers it.**
1. Does Windows Chrome create the popup at all when its first navigation
   is refused? Part 1's listener answers this directly: if a target is
   created, Part 1 fixes this case too.
2. If no window is ever created, is the blur that opens it happening?
   That is, does the completion of the group (every option chosen by arrow
   keys, then Tab away) leave focus on the last option before Tab on
   Windows, as it does on Linux?

If neither question explains it, stop and report. Do not widen the
investigation without Abby.

**Never:** edit the vendored Baseline page, or change its expected result.

## Out of scope

The two egress tests that installed Chrome does not exercise (ROADMAP
item), the 4.A ACT 8f9b5bf5 difference, and the Linux-only environment in
the two `test_config.py` launch tests. Each is recorded in the Windows
results note.
