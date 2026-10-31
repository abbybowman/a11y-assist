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
