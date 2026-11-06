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
