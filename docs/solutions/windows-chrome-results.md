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

**Real Windows differences (reproduced; open).**

- **5.D false PASS on the federal radio case.** Baseline
  TC10.C-3-fail-2 gives PASS ("filled in each of the 1 form fields ...
  none ... opened a window") in both Windows runs; Linux gives FAIL. That
  page opens a window on blur of the *last* radio option. Our fixture
  `5d/f04-radio-opens-window` (window opens on change) gives PASS in Run A
  only, and FAIL correctly in Run B and on Linux.
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
  parallel load.
- **Test-harness portability (both runs):** the two
  `test_config.py` launch tests start Python with only `PATH=/usr/bin:/bin`,
  a Linux path; Windows Python needs more of the environment to start. The
  product is not affected. This was found by reading the test; no fix has
  been tried yet.

**What this settles.** Each build-task file's "headed Chrome on Windows:
every fixture gives the same outcome" item is now answered for its test.
4.C, 4.D, 4.E and 4.F: yes, every fixture and ACT case. 4.B: yes. 4.A: yes
except ACT 8f9b5bf5. 5.D: no (TC10.C-3-fail-2). The individual browser
checks in `tests/browser/` (4.C V1 to V15) passed in Run B. Items no test
covers, such as 4.B V1 (repeated keydown on a held key) and 4.D V8 (cost
per stop), are still open.

**Running headed beside your own work.** Every page load gets a fresh
browser context ([fresh-load-per-probe.md](fresh-load-per-probe.md)), and in
headed mode Playwright shows each context as its own new window. Windows
keep opening and closing in front of other work, and a stray click moves
keyboard focus, which these tests measure. Stay off the machine during a
headed run, or try a second Windows virtual desktop first (not yet tried).
Rerun any headed failure alone, hands off, before believing it.
