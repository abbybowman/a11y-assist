# Windows Chrome results: what differs from Linux

**What happened.** On 2026-11-01 the full suite ran on Windows for the
first time, at `main` 77a5e7b, in two ways. Both runs are compared below
with Linux CI on the same commit (GitHub Actions run 41316430551). Until
then every result, and every "not yet checked on Windows Chrome" item, came
from Linux.

| | Linux CI | Run A | Run B |
| --- | --- | --- | --- |
| OS | Ubuntu (GitHub runner) | Windows 11 (NT 10.0.26100) | same |
| Browser | Playwright Chrome Headless Shell 153.0.8010.12 | same build (Playwright 1.63.0, `chromium_headless_shell-1243`) | installed Google Chrome 156.0.8078.49, headed |
| Workers | `-n auto` | `-n 8` | `-n0` (one visible browser at a time) |
| Time | 6 min 47 s | 11 min 56 s | 42 min 47 s |
| Totals | 507 passed, 1 xfailed | 501 passed, 6 failed, 1 xfailed | 501 passed, 6 failed, 1 xfailed |
| 4.A on ACT (agreement with ACT) | 12/19 | 12/19, same mismatches | **11/19** |
| 4.C on ACT (DHS; ACT) | 16/17; 30/34 | same, same mismatches | same, same mismatches |

Run A changes only the OS. Run B changes the browser build and headed mode
together, so a Run B-only difference cannot be pinned on either one alone.
A person used the laptop during Run B, so every Run B difference was rerun
with no one touching it. All of them reproduced.

**Fixed: new windows were missed on Windows (a 5.D false PASS).**
Baseline TC10.C-3-fail-2 gave PASS ("filled in each of the 1 form fields
... none ... opened a window") in both Windows runs, where Linux gives FAIL,
and our `5d/f04-radio-opens-window` gave PASS in Run A. `observe.observe`
counted `context.pages` after the settle, and on Windows a new page can
join that list late, or never: the federal page's popup goes to a blocked
external URL. A longer settle window (`SETTLE_QUIET_MS=600`) fixed f04 but
not the federal case. The fix records pages the tested page opens as the
browser creates them (CDP `Target.targetCreated` with the page as opener),
with the count kept as a second signal. Both cases now FAIL correctly on
Windows; the full Run A suite gives the same scores, with nothing else
changed. `tests/test_observe.py` (a window that opens and closes at once)
fails on the old code on any OS, so Linux CI keeps the fix. Its other tests
show that a window opened and closed from a cross-site iframe is caught
(Chrome reports the tested page as its opener), and that a window from an
earlier action is not counted again. If discovery cannot start, only the
page count decides.

**Fixed: a Linux-only date format (5.F).** `t5f.wrong_date` wrote the date
in words with `strftime("%-d")`. Windows Python has no `-` flag and raises
`ValueError`, so 5.F's f13 and f14 gave NEEDS REVIEW ("One attempt to send a
form could not be completed") where Linux gives PASS. It now builds the day
from `d.day`. Never use `%-d`, `%-m` or the like in this repo.

**Real Windows differences (reproduced; open).**

- **Egress guard tests, Run B only.**
  `test_egress.py::test_iframe_and_subresources_pointing_inside_are_refused`
  records no "non-public" refusal, and
  `test_rebinding_mid_run_is_refused` sees one DNS lookup instead of two.
  **No bypass:** a rerun with `pytest -l` showed the sentinel server
  (127.0.0.2) got no hits in either test. Installed Chrome never made the
  requests: the servers saw only the top page (`/frames.html`,
  `/rebind.html`), with no iframe, image, script or later `fetch`. So in
  headed Chrome 156 these tests do not exercise the guard. Why Chrome skips
  the requests is not yet known; Chrome's own block on public pages reaching
  private addresses is one guess, unchecked.
- **4.A ACT case 8f9b5bf5 (rule 0ssw9k), Run B only:** PASS where ACT
  expects DNA ("Spec G4. no instances").

**Not Windows differences.**

- **Load only (Run A):** 4.D `f10-100-links` took 78 s against its 65 s cap,
  and `test_time_budget.py::test_out_of_time_is_needs_review_and_no_time_limit_finishes`
  never started its walk within 10 s. Both pass when run alone in Run A and
  in serial Run B. On Windows the 120 s budget has less headroom under
  parallel load. Once, also under 8 workers:
  `test_browser.py::test_page_initiated_navigation_to_disallowed_host_is_blocked`
  found the page had not reached the disallowed host (the check that
  matters), but the guard's record of the block was not there yet. The test
  passed 3 of 3 times when run alone.
- **Test-harness portability (both runs):** the two
  `test_config.py` launch tests start Python with only `PATH=/usr/bin:/bin`,
  a Linux path. Without `SYSTEMROOT`, Windows Python fails at `import
  asyncio` (WinError 10106). The product is not affected. Fixed 2026-11-02:
  the tests pass `SYSTEMROOT` through on Windows only (3 passed, headless).

**What this settles.** Each build-task file's "headed Chrome on Windows:
every fixture gives the same outcome" item is now answered for its test.
4.C, 4.D, 4.E and 4.F: yes, every fixture and ACT case. 4.B: yes. 4.A: yes
except ACT 8f9b5bf5. 5.D: yes after the new-window fix (headless full
suite, and a headed run of the 4.A, 4.B, 5.D and Baseline tests). The
individual browser checks in `tests/browser/` (4.C V1 to V15) passed in Run B. Items no test
covers, such as 4.B V1 (repeated keydown on a held key) and 4.D V8 (cost
per stop), are still open.

**Running headed beside your own work.** Every page load gets a fresh
browser context ([fresh-load-per-probe.md](fresh-load-per-probe.md)), and in
headed mode Playwright shows each context as its own new window. Windows
keep opening and closing in front of other work, and a stray click moves
keyboard focus, which these tests measure. Stay off the machine during a
headed run, or try a second Windows virtual desktop first (not yet tried).
Rerun any headed failure alone, hands off, before believing it.

**Headed runs hang when the screen locks (assumed).** With the new-window
fix, 3 of 5 headed runs of the same 112 tests stopped for 25 to 50 minutes,
each on a different test (5.D f10, 4.A f12, 4.A f04). A stack dump showed
the event loop idle, waiting on a browser call that has no time limit (a
CDP command or `page.evaluate`; the settle rule waits on animation frames).
Every hang came while no one was using the laptop. It auto-locks after 15
minutes idle (`InactivityTimeoutSecs` 900, a managed setting) and turns the
display off after 15 minutes, and Windows logged Modern Standby during
each hung run. A locked or dark screen stops Chrome drawing frames. The two
clean runs finished in about 12 minutes, one with a video playing to keep
the display on. The one headed run on `main` without the fix, while the
laptop was in use, did not hang. Not proven: two hangs began well before 15
minutes, and the decisive test (`main` with a deliberate lock) was not run.
The observer's own CDP calls now give up after 2 s (`observe.CDP_TIMEOUT_S`).

**For headed runs:** keep the screen on and unlocked (play a video in a small
window, or change the power settings), and run long checks under a hard
stop with `-v`, e.g. `timeout 1800 env TEST_BROWSER_CHANNEL=chrome
TEST_HEADED=1 uv run pytest -n0 -v -o faulthandler_timeout=240 ...`, so a
hang names its test and dumps where it waits.
