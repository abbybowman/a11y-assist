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
