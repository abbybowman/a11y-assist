# Results are for the browser that ran them

**Chrome tabs to scroll containers.** Since Chrome 130 a scrollable element
with no focusable content is in the Tab order (checked in Chromium 153 on
ACT 0ssw9k: Tab reaches the `<section>`). ACT's rule is browser-neutral and
calls those pages failures; for a Chrome keyboard user they are not. Abby's
rule: report what this browser does, and never claim it for others (each
4.A summary names the browser version). Firefox is a roadmap item, not a
setting: focus reading uses CDP.

**A federal test page that is broken in Chrome.** Baseline Alignment case
TC01.A-2-fail-1 (hold Space for 3 seconds) loads jQuery from cdnjs with a
wrong SRI hash (`1H2T9w…`; the real file's sha384 is `1H217gw…`, checked
against cdnjs on 2026-10-31). Chrome blocks the script, so the timed
behaviour never runs and 4.B gives NEEDS REVIEW where Baseline expects FAIL.
The page is vendored unchanged; `tests/fixtures/4b/f01` is a working copy of
the same behaviour for the FAIL path. Before trusting a published test case,
load it in the browser and confirm its behaviour actually happens.

**Tests never use the network.** `tests/conftest.py` maps cdnjs to
NOTFOUND (`--host-resolver-rules`), which gives the same result as the SRI
block: no jQuery.
