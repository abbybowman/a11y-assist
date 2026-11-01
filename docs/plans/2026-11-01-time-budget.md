# Time budget across Test 4 (2026-11-01)

One `a11y_run_tt_tests` call runs every implemented test (4.A–4.F) and must
finish within `RUN_LIMIT_S` (120 s). A run that runs out of time stays
NEEDS REVIEW with the reason, never PASS.

## Measured

`uv run python evals/time_budget.py [--limit S] <pages>`: every implemented
test, Playwright Chromium headless, Linux container, 4 CPUs. Costs come from
steps.jsonl (`walk` and `collected` entries carry `cost`: seconds, page loads,
key presses). Windows headed Chrome not measured (cannot run here).

| Page | Limit | Total | Walk | 4.A | 4.C | 4.D | 4.F | Others |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4.D F10, 100 links | 120 | 60 s | 54 s, 204 presses | 4 s | 0.3 | 0.2 | 0 | <0.5 |
| budget/agency-home (≈80 stops, menus, tabs, carousel, dialog) | 900 | **153 s** | 59 s, 160 | 52 s, 13 loads, 191 presses | 8 s | 18 s | 14 s | <0.5 |
| budget/benefits-form (≈60 stops, help toggles) | 120 | **139 s** (over the limit) | 43 s, 120 | 76 s, 14 loads, 318 presses | 9 s | 10 s | 0.4 | <0.5 |
| 4.C F34, 600 links | 120 | 125 s | 120 s, stopped at 378 presses | 2 s | 0.2 | 1 s | 0 | all NEEDS REVIEW |

Where the time goes (agency-home, sub-steps timed by wrapping functions):

- The settle wait: 545 calls, 102 s of 153 s (≈190 ms per press: two
  animation frames plus the 150 ms quiet window after the press's own focus
  event).
- Replays that Tab back to a stop before doing their one thing: 4.A's 11
  replays spend 141 presses (33 s) on Tab prefixes, inside its arrow probe
  (78 presses, 17 s) and execute check (56, 15 s); 4.D widget pass W (77,
  18 s); 4.F reveal (54, 13 s). 358 of the run's 518 presses are in check
  replays, nearly all Tab prefixes.
- 4.D's per-stop on/off images in the walk: 22 s (≈275 ms a stop).

Holes in the limit (benefits-form ran 139 s): 4.A and 4.C check the deadline
before each replay but not during its Tab prefix (one 4.A execute replay
takes ~7 s), 4.D's widget pass never checks it, and nothing reserves time to
evaluate and write the report after collecting. 4.A finished at ~120 s; 4.C
and 4.D then ran 19 s past the limit.

## Proposed cuts

Asked as multiple-choice questions; answers recorded in the specs.
