# Keep tool output small: links and shared evidence

**Problem.** A Test 4 run on a two-link page returned about 20,000
characters (5,000 tokens), 60% of it the full report repeated after the
findings, and each 4.A question repeated the whole stop list (on a real page
with ten candidates, ten copies).

**What we do.** `RunResult.report` and `AnswerResult.report` stay on the
Python object (pipeline, tests and evals use them) but are `exclude=True`, so
the client gets `report_uri` (a `run://` resource) instead and reads it only
to save it. Evidence several questions use goes once in `shared_inputs` (a
check's optional `shared_inputs(state)`, like `page_text(state)`), and each
question lists the keys it uses in `shared`. 4.A and 4.B share one `stops`
key, so it goes once when both run. Same run: 8,300 characters (−59%).
Covered by `tests/test_tools.py` (`test_shared_evidence_is_sent_once`, the
report-link assertions).
