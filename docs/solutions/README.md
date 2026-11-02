# Solutions: lessons that save the next test time

One short file per lesson: what happened, what we do now, and how we know.
Specs link here instead of repeating the reasoning. Add a file when a problem
took more than an hour to understand; update it when the answer changes.

| File | Lesson |
| --- | --- |
| [focus-reading.md](focus-reading.md) | Read focus through CDP, not page script; how stops are identified across loads |
| [fresh-load-per-probe.md](fresh-load-per-probe.md) | Why every probe gets a new browser context, not just a new page |
| [exit-check-on-small-pages.md](exit-check-on-small-pages.md) | An exit check must accept reaching the end of the page |
| [scanners-after-the-walk.md](scanners-after-the-walk.md) | ANDI changes the page; run scanners on their own load |
| [tt-pdf-as-data.md](tt-pdf-as-data.md) | The TT PDF converted once to Markdown and JSON; layout traps; where the PDF disagrees with itself |
| [focus-events-in-chrome.md](focus-events-in-chrome.md) | What the focus log shows; blur inside a focus handler fires no focus-in; `id="close"` is shadowed by `window.close` |
| [animation-noise.md](animation-noise.md) | A second focused read separates animation from a focus indicator |
| [widget-items.md](widget-items.md) | Arrowing through roving-tabindex and aria-activedescendant widgets |
| [unique-paths-and-frame-coordinates.md](unique-paths-and-frame-coordinates.md) | Paths need `:nth-of-type`; positions must be top-level, not frame-relative |
| [testing-what-no-page-can-trigger.md](testing-what-no-page-can-trigger.md) | Test timing-dependent rows on hand-built evidence |
| [editing-formatted-code.md](editing-formatted-code.md) | Agents: format first, then edit against the formatted text |
| [shadow-paths-and-contains.md](shadow-paths-and-contains.md) | `contains()` and `querySelector` stop at shadow roots; resolve walk paths part by part |
| [browser-specific-results.md](browser-specific-results.md) | Chrome tabs to scrollers (ACT 0ssw9k); a Baseline test page broken by its SRI hash; results are per browser |
| [judge-eval.md](judge-eval.md) | Scripted answers test rules, not questions; how the judge eval stays unbiased; what agents need in a question |
| [subagent-token-cost.md](subagent-token-cost.md) | One subagent per question costs ~55k tokens each; batch all questions in one |
| [parallel-tests.md](parallel-tests.md) | pytest-xdist; per-worker files for anything tests write in common |
| [small-tool-output.md](small-tool-output.md) | Report as a `run://` link; shared evidence once per result |
| [andi-output.md](andi-output.md) | Reading ANDI's per-element output; its wrapper changes CSS paths; viewport clips; scoping nearby text |
| [form-fields.md](form-fields.md) | Read vendored cases first; one control kind per stop; Chrome's date-input parts; changes outside a field's own widget; submission log; draft checks; before-reads on the fresh load; alerts, native validation and live regions; read every listed technique before a rubric (5.H) |
| [time-budget.md](time-budget.md) | Measure with `evals/time_budget.py`; the tool's own screenshots are DOM mutations; replay with `ctx.replay` |
| [windows-chrome-results.md](windows-chrome-results.md) | First Windows runs (headless and headed Chrome 156) against Linux: 5.D false PASS, egress tests, one 4.A ACT case; load-only and harness-only failures; stay off the machine in headed runs |
| [egress-proxy.md](egress-proxy.md) | `route.fetch` goes through the launch proxy; a CONNECT 403 is a response, not an error; HAR replay hangs on failed requests |
| [multi-page.md](multi-page.md) | Other pages come from the caller; read content, not stops (ACT's text-only blocks); where a skip link lands; stop once bypassed; rules-only cases and the judge eval; 19.A's live search and suggested pages |
