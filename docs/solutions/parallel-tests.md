# The suite runs in parallel; shared files must be per worker

**Problem.** The full suite took 20 minutes serially. Tests mostly wait
(settle windows, timers, a 3 s key hold), so CPUs sat idle.

**What we do.** pytest-xdist, `-n auto` by default (one worker per CPU):
5.5 min on 4 CPUs; `-n 8` measured 3.5–3.9 min twice with no flakes. Every
test already had its own run folder, servers on ephemeral ports and browser
context. The one shared thing was the ACT scoreboard: each worker now writes
`tests/.act_scores/<worker>.json`, and only the controller (no `workerinput`)
clears them at session start. Anything new that writes a shared file from
tests needs the same treatment. Use `-n0` to run one test on its own.

**Known load-sensitive test.** `test_f29_feed_grows_live_and_footer_is_reachable_backward`
presses keys 20 ms apart on a live infinite feed; under `-n 8` it failed
once (2026-11-01) and passed alone and on the rerun. It checks the fixture,
not a rule; if it fails again, rerun it alone before looking further.

**In a container, `auto` counts the pod's CPU limit (2026-11-06).** xdist
counts the CPUs the scheduler shows (`sched_getaffinity`, the same number
`nproc` prints), which in a Kubernetes pod is every core of the node, not
the pod's limit. On VAST (4-CPU limit) a run under `-q` printed nothing and
seemed to hang; the likely cause is one worker, and so one Chromium, per
node core (with `-n 4` the full suite passed there in under 10 minutes;
`nproc` against the limit would confirm).
`tests/conftest.py` now implements `pytest_xdist_auto_num_workers` and caps
`auto` at the cgroup quota (v2 `cpu.max`, or v1 `cpu.cfs_quota_us`).
`PYTEST_XDIST_AUTO_NUM_WORKERS` or an explicit `-n` still wins. Verified:
`docker run --cpus=2` on a 4-CPU host started 2 workers, and a faked
`cpu.max` of 4 CPUs with 64 visible returned 4.

## A test that fails only on a busy machine: look for chance in the page first (2026-11-07)

`test_act_color_cycle_with_stop` (2.B on ACT efbfc7 inapplicable 3) failed about 1 run in 3 under `-n 8` on 4 CPUs and never alone, which looked like CPU starvation. The page picks one of four colours at random every second (`Math.random()`), so about one tick in four changes nothing. Pass T's watch is 6.5 s, and 2.B needs a change seen after 5 s: when the ticks near 5 s and 6 s both repeat (1 in 16), nothing moves late and 2.B is DOES NOT APPLY. On a busy machine the page starts its timer later, so fewer ticks fall in the window and it happens more often. Proof without load: with `Math.random` fixed so the colours repeat from the fifth tick, 2.B was DOES NOT APPLY every time; with every tick changing, NEEDS REVIEW.

What we do: the test fixes the page's `Math.random` with an init script (the page itself is not edited), so it tests the rules, not the dice. A test that checks an input on the page's run reads `run_check(...)["asked"]` (or `run_tests(..., asked=[])`) instead of running the page again; folding five such tests into the outcome tests removed seven pipeline runs (about 60-80 CPU s).

Where a run's CPU goes (4 CPUs, idle machine): 4-17 CPU s per test against 6-52 s of wall time; the Playwright driver and two browser launches are about 0.65 CPU s of that; pass T about 1.2 CPU s on a static page. The rest is Chromium doing the work (presses, settle polling, screenshots), which the outcomes need.

