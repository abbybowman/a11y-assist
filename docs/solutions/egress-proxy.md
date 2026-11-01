# The egress proxy: what the browser and Playwright actually do

`egress.py` gives Chrome one way out, a local proxy that checks every
connection's address. Three things were not obvious.

**Playwright's `route.fetch` uses the browser's launch proxy, and tunnels even
plain `http://` with CONNECT, loopback included.** So the navigation guard's
own top-level fetch is checked too. Playwright also adds `<-loopback>` to
Chrome's proxy bypass list, so loopback pages go through the proxy rather than
around it. (Verified with a logging proxy; `tests/test_egress.py` would show a
hit on the 127.0.0.2 sentinel otherwise.)

**A CONNECT refusal comes back from `route.fetch` as an ordinary 403
response**, not an exception. The guard served it as the page, so a refused or
unreachable page was "tested" as an empty 403. Now the proxy records every
refusal (`policy: True` for an address or port rule, `False` for a failed
connection), and the guard compares the list before and after its fetch:
policy refusals raise `NavigationBlocked`, failed connections raise
`PageUnreachable`. For plain-HTTP refusals the proxy sends no response at all,
because a 403 body would render as the page.

**HAR replay hangs on requests that failed while recording.** The HAR stores
them with status -1, and `route_from_har` waits on them forever (a
`page.goto` timeout of 30 s). This applies to any failed subresource, not only
refused ones. `capture.replay_context` aborts exactly those URLs, as they
failed live.

How we know: `tests/test_egress.py` (removing the proxy from the launch fails 9
tests), `tests/test_leakage.py::test_secrets_stay_out_of_a_load_failure` (found
the 403 case), and the iframe test (found the HAR hang).
