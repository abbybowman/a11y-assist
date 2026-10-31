# A fresh browser context per load, not just a fresh page

**Problem.** Reusing one context and opening a new page per probe looks like a
cheap speedup. But pages keep state in localStorage, sessionStorage and
cookies. A probe that presses Enter on "Accept" in a cookie banner can store
that, and the next "fresh" load then has no banner: the evidence differs
between probes of the same frozen page.

**What we do.** `traverse.Session.close()` closes the whole context, and the
opener builds a new context with the HAR replay routes for every load.

**Where the time really went** (spec 1.4.0 → 1.5.0, same code otherwise):
probes that continued to the end of the page, P5/P4 sweeps, Enter and Space
on every member, a 300 ms focus window plus a 300 ms DOM window per press, and
a screenshot per press. Cutting those took F04 from 71 s to 9.5 s and F32 from
80 s to 25 s; context creation was not the bottleneck.
