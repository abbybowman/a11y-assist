# Rows no page can trigger reliably: test them on recorded evidence

Some rows depend on timing or chance: a redirect that fires on a timer, a
signal that happens once but not on the replay, a run over its replay limit.
A fixture page for them is flaky. The recorder waits for the page to go idle,
so a 3 s redirect may fire during recording or during the walk, depending on
speed.

**What we do.** Build the check's state model by hand with the evidence the
row needs and call `evaluate()` directly (e.g.
`tests/test_fixtures_4e.py::test_rows_on_recorded_evidence`). The outcome
still comes only from the spec's rows; the test just supplies the facts.
