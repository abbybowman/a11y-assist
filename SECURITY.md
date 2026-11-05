# Security Policy

a11y-assist is an MCP server that drives a real Chrome browser to web pages
an agent names, records them, and tests the recordings against parts of the
DHS Trusted Tester 5.1.3 process. That makes two things its main risks: the
pages it visits (where the browser may go, and what their content may try to
make an agent do) and what it keeps (recordings, screenshots, reports).

> **Draft for review (2026-11-05).** Replaces the GSA starter template's
> policy. Items marked **[TO CONFIRM]** need a decision before this is final.

## Reporting a vulnerability

**[TO CONFIRM: the reporting route.]** The template pointed to GSA's
Vulnerability Disclosure Policy, which covers software GSA develops. This
project is developed at NASA for the GSA MCP hackathon, so it should
probably point to NASA's policy, or to a named project contact until it is
released.

Please do not open a public issue for a vulnerability. Include the version
(commit), how you ran the server (stdio or HTTP, operating system, browser),
and the steps to reproduce.

When testing, avoid privacy violations, disruption of production systems
and destruction or manipulation of data; use an exploit only as far as
needed to confirm a vulnerability; and keep the details confidential until
the vulnerability is fixed. Point the server only at pages you are allowed
to test: it loads real agency sites.

## Supported versions

Pre-release. Only `main` is supported; there are no tagged releases yet.

## Status: local use only

The server runs on the user's own machine, over stdio by default. **It has
no authentication.** Its HTTP transport listens on loopback only (127.0.0.1
or ::1; any other host is refused at start) and checks the Host and Origin
headers on every request. Do not expose it on a network or host it for
others until the items under "Before a hosted deployment" are done.

## What the server does to stay safe

**Where the browser may go**
- **Navigation allowlist** (default `.gov` and `.mil`), enforced on every
  top-level navigation and every redirect hop. `file://` only with
  `DEV_MODE=true`.
- **Connection-time address checks** (`egress.py`). Chrome's only route out
  is a local proxy that resolves each host once, refuses the connection if
  any answer is not a public unicast address (internal hosts, cloud metadata
  services, loopback) or the port is not 80 or 443, and connects to the
  address it checked. A second DNS answer (rebinding) is never used. TLS
  stays end to end. If the proxy is down, nothing gets through.
- **The caller chooses the pages, never the page.** Other pages of the same
  site come only from the caller and must be on the tested page's host,
  before and after redirects. Links found on a page are suggested to the
  user, never visited. One exception: 19.A may run the site's own search
  once (a GET form on the same host, allowlisted, every hop checked).
- **Tests run on a recording.** Each page is recorded once (HAR) and tested
  from the replay, so the tests' key presses and form entries never reach
  the live site. 5.F–5.H submit forms with wrong values only into the
  replay.
- **ANDI is served from the repository.** It is never loaded from ssa.gov;
  other www.ssa.gov requests are aborted. No Content-Security-Policy bypass
  is used.

**Page content is untrusted**
- Text from tested pages (DOM, accessible names, URLs, titles, screenshots,
  recordings) may contain instructions aimed at the agent reading the
  results. Tool descriptions and results mark page-derived evidence as
  untrusted, and page content never chooses a URL to visit, a tool to call
  or an outcome. The one exception: a key combination a page names as the
  way to stop moving content or audio may be pressed once, in a fresh
  replay, to confirm what an open question found (modifiers plus one key,
  never a key the browser itself uses).
- The test fixtures include pages with planted instructions to check this.

**What it keeps and what it says**
- **Errors and logs are redacted** (`redact.py`): tool errors, the result's
  `errors` and the run log keep a URL's scheme, host, port and path only (no
  query string, fragment or credentials), one line per error, no stack
  traces, request headers or page text. `tests/test_leakage.py` seeds
  secrets and checks they do not appear.
- **Run folders** (`runs/<run_id>/`) hold the report, recordings and
  screenshots of the tested pages, including the full tested URL. They are
  deleted after `RUN_TTL_HOURS` (default 24). Evidence is served only as
  `run://` resources with validated run IDs, never as file paths. Test only
  pages whose content you may store; a recording of a signed-in page can
  hold personal data. **[TO CONFIRM: whether runs/ needs an access or
  retention rule beyond the 24 h deletion on NASA machines.]**
- **No secrets in the repository.** Keys (for example the agent eval's
  model API keys) go in environment variables or `.env`, which git ignores.

**Supply chain**
- Python dependencies are locked in `uv.lock`; Playwright is pinned
  exactly. ANDI and jQuery are vendored with SHA-256 hashes in
  `third_party/PROVENANCE.json`, checked by the test suite. The agent eval's
  Node tools are pinned with a lockfile.
- The container image runs as an unprivileged user.

## Before a hosted deployment

Hosting is the target (see `docs/plans/2026-11-04-results-service.md`), and
these are not built yet:
- authentication and authorization on the MCP endpoint;
- network-level egress rules on the host, as a second layer behind the
  proxy;
- access control and retention for stored runs, and per-user separation of
  run data;
- NASA's security review and ATO for the hosting environment;
- NASA's software release review before the code is published.

## Known gaps

- In headed Chrome 156 on Windows, two egress tests do not exercise the
  guard (Chrome never sends the requests they check). Nothing leaked, and
  the default headless run exercises it (`docs/ROADMAP.md`).
- Some browser calls have no time limit; a headed run on a locked screen
  can stall. Hosted runs are headless.

## Changing a security control

Do not weaken the allowlist, the egress proxy, the redaction or the
untrusted-content rules to make a test pass. A change to any of them is
recorded in `docs/hackathon/evaluation.md` and its deck slide in the same
commit (`CLAUDE.md`).
