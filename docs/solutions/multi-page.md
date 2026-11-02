# Several pages of one site: what repeats, and what cost time

Lessons from building 9.A, 9.B and 9.C (2026-11-02).

**The other pages come from the caller, never from the page.** Following
the tested page's links would let page content choose a URL (CLAUDE.md
principle 5). `other_pages` takes 1–5 URLs; each passes the allowlist and
must be on the tested page's host before and after redirects, else the
call is a tool error. Each is recorded as its own HAR
(`evidence/pages/p<N>.har.zip`) and `RunContext.pages` gives a fresh load of
it, like `ctx.new_page`. Pages are recorded only when a selected check has
`uses_pages`; such a check without pages is not performed and does not even
need the walk (`pipeline.needs_walk`), so a single-page run pays nothing.
The run limit grows by `OTHER_PAGE_S` (20 s) per page.

**Read each page once, as content, not as stops.** `site.py` reads every
page's rendered content in reading order (units: text, headings, images,
controls; regions: landmarks) into `RunContext.cache["site"]`. The ACT
bypass cases showed why stops are not enough: their repeated block is an
`aside` of plain text with nothing focusable in it, and W3C still expects a
bypass. A unit repeats if its text appears on another page, or it sits in
a landmark another page also has (blocks "do not have to be exactly the
same", p. 42).

**Where a skip link lands is `:target` or the focused element.** After
Enter, read `document.activeElement` (if focus left the link) else
`:target`, then the first unit at or after it. One Tab confirms the
keyboard continues from there, except when nothing focusable follows the
landing: the Tab then wraps to the top of the page or leaves it (ACT
235a899f looked broken until the M6 row required a stop after the landing).

**Stop trying candidates once the block is bypassed.** The agency page has
eight buttons and links before its main content; trying all of them cost
9.7 s, stopping after the skip link 1.2 s, with the same outcome.

**A rules-only case can poison the judge eval.** Two fixture cases used the
same page and question with opposite scripted answers (to test both rows);
an agent can only give one answer, so one would always "mismatch".
`test_fixtures_9x.NOT_EVAL` leaves the rules-only one out of the eval.

**Check the converted TT text before relying on it.** 9.B's PDF heading
breaks over a line ("consistent- navigation"), so the first conversion gave
9.B 9.A's steps and put 9.B's text into 9.C. 5.B, 7.C and 16.B have the
same problem (ROADMAP). Read the printed pages for each new test.

**Every record() call is bounded, and each other page by its own share.**
Each other page adds `OTHER_PAGE_S` (20 s) to the limit, but one recording
can take 30 s to load plus the idle wait and scrolls. The recordings were
not bounded at first. Bounding them by the whole run's deadline was not
enough: a slow page then ate the time the single-page tests needed. Now each
other page records within its own share; one that runs over leaves 9.A-9.C
not performed (never run on fewer pages than the caller named) and the
other tests run in full (Abby, 2026-11-02;
`test_time_budget.py::test_slow_other_page_drops_only_the_page_tests`).
