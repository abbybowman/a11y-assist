# Agent eval score: round1

Agent-assisted results scored against a tester's SCRT files. Not a certified Trusted Tester result.

Scored 2026-11-04T18:07:08.549399+00:00; lock commit 7d26a02b317b45a5580b37658105e5004bdbf7f1; 9 of 9 pages have keys.

## arm-a-1

RESULT line: found. Ended: completed. Wall time: 1217.0 s. Tokens: {'input_tokens': 14, 'cache_creation_input_tokens': 154875, 'cache_read_input_tokens': 349470, 'output_tokens': 15590}. Model calls: 6. Tool calls: {'mcp__a11y__a11y_run_tt_tests': 11}.

Per WCAG 2.0 criterion (what the agent reported): weighted 40

- scored: 136
- agreement (of decided): 44/48
- needs review (of scored): 88/136
- false PASS: 0
- missed fail (Does Not Apply): 0
- false FAIL: 4
- Fail vs Does Not Apply: 0
- other mismatch: 0
- no answer given: 0
- not performed by the tool: 0
- no reference answer: 0

Tool's own results, per TT test: weighted 44

- scored: 52
- agreement (of decided): 48/52
- needs review (of scored): 0/52
- false PASS: 0
- missed fail (Does Not Apply): 0
- false FAIL: 4
- Fail vs Does Not Apply: 0
- other mismatch: 0
- no answer given: 0
- not performed by the tool: 84
- no reference answer: 352

Tool's own results rolled up per criterion: weighted 41

| Page | Criterion | Key | Arm | Verdict | Elements |
| --- | --- | --- | --- | --- | --- |
| https://www.nasa.gov/careers/ | 2.4.3 | Pass | Fail | false_fail | Internships (button) dialog: Tab leaves the open dialog onto the page behind it |
| https://www.nasa.gov/careers/ | 2.4.7 | Pass | Fail | false_fail | Read More (link) |
| https://www.nasa.gov/missions/ | 2.4.7 | Pass | Fail | false_fail | 3D Tissue Chips (link); A-Train: The Afternoon Constellation (link); Able 1 (Pioneer 0) (link); Able 2 (Pioneer 1) (link); Able 5A (Pioneer P-30) (link); Able 5B (Pioneer P-31) (link); ACE (link) |
| https://www.nasa.gov/mission/artemis-iii/ | 2.4.7 | Pass | Fail | false_fail | NASA (link); Hide player controls (button); More NASA News (link) |

## arm-a-2

RESULT line: found. Ended: completed. Wall time: 1245.9 s. Tokens: {'input_tokens': 10, 'cache_creation_input_tokens': 128272, 'cache_read_input_tokens': 372185, 'output_tokens': 10509}. Model calls: 5. Tool calls: {'mcp__a11y__a11y_run_tt_tests': 11, 'Bash': 1}.

Per WCAG 2.0 criterion (what the agent reported): weighted 40

- scored: 136
- agreement (of decided): 42/44
- needs review (of scored): 92/136
- false PASS: 0
- missed fail (Does Not Apply): 0
- false FAIL: 2
- Fail vs Does Not Apply: 0
- other mismatch: 0
- no answer given: 0
- not performed by the tool: 0
- no reference answer: 0

Tool's own results, per TT test: weighted 41

- scored: 43
- agreement (of decided): 42/43
- needs review (of scored): 0/43
- false PASS: 0
- missed fail (Does Not Apply): 0
- false FAIL: 1
- Fail vs Does Not Apply: 0
- other mismatch: 0
- no answer given: 0
- not performed by the tool: 93
- no reference answer: 352

Tool's own results rolled up per criterion: weighted 39

| Page | Criterion | Key | Arm | Verdict | Elements |
| --- | --- | --- | --- | --- | --- |
| https://www.nasa.gov/missions/ | 2.4.7 | Pass | Fail | false_fail | 3D Tissue Chips link; A-Train: The Afternoon Constellation link; Able 1 (Pioneer 0) link; Able 2 (Pioneer 1) link; Able 5A (Pioneer P-30) link; Able 5B (Pioneer P-31) link; ACE link |
| https://www.nasa.gov/mission/artemis-iii/ | 2.4.7 | Pass | Fail | false_fail | Link to Facebook. (link); About Orion (link); Hide player controls (button); Start Exploring about Join Artemis (link); NASA (link) |

## arm-a-3

RESULT line: found. Ended: completed. Wall time: 1056.3 s. Tokens: {'input_tokens': 14, 'cache_creation_input_tokens': 158418, 'cache_read_input_tokens': 491857, 'output_tokens': 16183}. Model calls: 6. Tool calls: {'mcp__a11y__a11y_run_tt_tests': 9, 'Bash': 1, 'Read': 1, 'ListMcpResourcesTool': 1}.

Per WCAG 2.0 criterion (what the agent reported): weighted 42

- scored: 153
- agreement (of decided): 45/48
- needs review (of scored): 105/153
- false PASS: 0
- missed fail (Does Not Apply): 0
- false FAIL: 3
- Fail vs Does Not Apply: 0
- other mismatch: 0
- no answer given: 0
- not performed by the tool: 0
- no reference answer: 0

Tool's own results, per TT test: weighted 47

- scored: 51
- agreement (of decided): 49/51
- needs review (of scored): 0/51
- false PASS: 0
- missed fail (Does Not Apply): 0
- false FAIL: 2
- Fail vs Does Not Apply: 0
- other mismatch: 0
- no answer given: 0
- not performed by the tool: 85
- no reference answer: 352

Tool's own results rolled up per criterion: weighted 43

| Page | Criterion | Key | Arm | Verdict | Elements |
| --- | --- | --- | --- | --- | --- |
| https://www.nasa.gov/spot-the-station/ | 3.2.2 | Pass | Fail | false_fail | City: select (navigates on change, not announced beforehand) |
| https://www.nasa.gov/careers/ | 2.4.7 | Pass | Fail | false_fail | Learn More about People of NASA link; Read More link |
| https://www.nasa.gov/mission/artemis-iii/ | 2.4.7 | Pass | Fail | false_fail | About Orion link; Go To Gallery link; Hide player controls button; Start Exploring about Join Artemis link; NASA link |

## arm-b

RESULT line: found. Ended: completed. Wall time: 177.3 s. Tokens: {'input_tokens': 60, 'cache_creation_input_tokens': 40438, 'cache_read_input_tokens': 872476, 'output_tokens': 16378}. Model calls: 30. Tool calls: {'mcp__browser__browser_navigate': 11, 'mcp__browser__browser_evaluate': 20, 'mcp__browser__browser_press_key': 1, 'mcp__browser__browser_snapshot': 1, 'mcp__browser__browser_wait_for': 2}.

Per WCAG 2.0 criterion (what the agent reported): weighted 20

- scored: 153
- agreement (of decided): 86/112
- needs review (of scored): 41/153
- false PASS: 20
- missed fail (Does Not Apply): 0
- false FAIL: 0
- Fail vs Does Not Apply: 0
- other mismatch: 6
- no answer given: 0
- not performed by the tool: 0
- no reference answer: 0

| Page | Criterion | Key | Arm | Verdict | Elements |
| --- | --- | --- | --- | --- | --- |
| https://www.nasa.gov/spot-the-station/ | 2.4.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/spot-the-station/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/?search=artemis | 2.4.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/?search=artemis | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/forms/nssc-accounts-receivable | 2.4.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/forms/nssc-accounts-receivable | 2.4.5 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/forms/nssc-accounts-receivable | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/careers/ | 2.4.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/careers/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/missions/ | 1.3.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/missions/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/missions/ | 4.1.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/mission/artemis-iii/ | 2.4.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/mission/artemis-iii/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/feature/naca-at-110-special-feature/ | 2.4.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/feature/naca-at-110-special-feature/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/news-release/nasa-releases-max-power-key-events-for-media-participants/ | 2.4.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/news-release/nasa-releases-max-power-key-events-for-media-participants/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/gallery/ksc-history/ | 2.4.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/gallery/ksc-history/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/?search=artemis | 2.4.5 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/careers/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/mission/artemis-iii/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/feature/naca-at-110-special-feature/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/news-release/nasa-releases-max-power-key-events-for-media-participants/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/gallery/ksc-history/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |

## arm-b-2

RESULT line: found. Ended: completed. Wall time: 180.1 s. Tokens: {'input_tokens': 66, 'cache_creation_input_tokens': 43501, 'cache_read_input_tokens': 1018462, 'output_tokens': 19184}. Model calls: 33. Tool calls: {'mcp__browser__browser_navigate': 10, 'mcp__browser__browser_evaluate': 21, 'mcp__browser__browser_press_key': 1, 'mcp__browser__browser_click': 4, 'mcp__browser__browser_snapshot': 1, 'mcp__browser__browser_wait_for': 3, 'mcp__browser__browser_find': 1}.

Per WCAG 2.0 criterion (what the agent reported): weighted 41

- scored: 153
- agreement (of decided): 95/117
- needs review (of scored): 36/153
- false PASS: 16
- missed fail (Does Not Apply): 0
- false FAIL: 0
- Fail vs Does Not Apply: 0
- other mismatch: 6
- no answer given: 0
- not performed by the tool: 0
- no reference answer: 0

| Page | Criterion | Key | Arm | Verdict | Elements |
| --- | --- | --- | --- | --- | --- |
| https://www.nasa.gov/spot-the-station/ | 2.4.7 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/spot-the-station/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/?search=artemis | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/forms/nssc-accounts-receivable | 2.4.5 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/forms/nssc-accounts-receivable | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/careers/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/missions/ | 1.3.1 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/missions/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/missions/ | 4.1.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/mission/artemis-iii/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/feature/naca-at-110-special-feature/ | 2.4.7 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/feature/naca-at-110-special-feature/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/news-release/nasa-releases-max-power-key-events-for-media-participants/ | 2.4.7 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/news-release/nasa-releases-max-power-key-events-for-media-participants/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/gallery/ksc-history/ | 2.4.7 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/gallery/ksc-history/ | 3.3.2 | Fail | Pass | false_pass |  |
| https://www.nasa.gov/?search=artemis | 2.4.5 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/careers/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/mission/artemis-iii/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/feature/naca-at-110-special-feature/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/news-release/nasa-releases-max-power-key-events-for-media-participants/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |
| https://www.nasa.gov/gallery/ksc-history/ | 2.4.6 | Does Not Apply | Pass | other_mismatch |  |
