# Plan: hosted results service and dashboard (2026-11-04, proposed)

A second, hosted MCP server that keeps a11y-assist results inside NASA and
shows them in a dashboard for site owners, Trusted Testers (TTs) and web
governance. The Playwright runner stays a local MCP server. This plan
records the goals, user stories and decisions from Abby's 2026-11-04
review, and the cut for the GSA hackathon demo (due Nov 20).

## Goals

- Keep every agent-assisted result NASA runs, with a full audit trail, in
  one place NASA controls.
- Let anyone at NASA see results across sites, pages, tests and time,
  and understand what was tested, what was not, and what still needs a
  person.
- Rank what to fix first, and say who it affects and (later) how to fix it.
- Give certified TTs a path to review, correct and certify results, so
  agent-assisted results can become TT-certified ones.
- The dashboard itself must be as accessible as possible: as little text
  and as few keyboard stops as the task allows. It must pass a11y-assist's
  own tests.

## Who uses it

| Role | Who | Can |
| --- | --- | --- |
| Everyone | Any NASA user signed in through workspace SSO | View, answer judgment questions (logged by name), flag results, pin sites |
| TT-certified | A user whose TT ID an admin verified | Everything above, plus edit and certify rows, save SCRT files, upload SCRT files, override anyone's answer |
| Admin | Runs the service | Everything above, plus approve role requests, work the flag queue, manage scans and the domain list |

No separate site owner role for now: logging who made each call, plus TT
overrides, does the job without admins managing a POC list (Abby,
2026-11-04). Revisit if a source of site POCs turns up.

## User stories

IDs are for reference in wireframes and issues. **MVP** = in the Nov 20
demo. **Later** = end state.

### Everyone

| ID | Story | When |
| --- | --- | --- |
| E1 | On every page, see that results are agent-assisted, do not cover all Section 508 tests yet, and are not certified unless marked TT-certified. | MVP |
| E2 | For any result, see who decided it: Agent only, Human-verified (not a TT) or TT-certified, with who and when. Shown as text, not hover-only. | MVP (read-only) |
| E3 | See all tested NASA sites with pages tested and latest results, including the latest TT-certified date. | MVP |
| E4 | See the two GSA numbers: unique pages tested in the last 12 months, and pages TT-certified with no failures. | MVP |
| E5 | Sort sites by name, issues found, or date of last agent or TT report. | MVP |
| E6 | Filter sites by part of a domain name. | MVP |
| E7 | Open a site: its pages (sortable by path, date, issues, needs review) and its results by test. | MVP |
| E8 | See what to fix first on a site, in priority order (see Decisions). | MVP |
| E9 | Open a page: latest result per test, top issues and scan history. | MVP |
| E10 | Open a result: plain-language explanation, WCAG links, screenshots and code for fails and needs review, what the test checked and what it can't. | MVP |
| E11 | Download a page's pre-SCRT file. | MVP |
| E12 | Publish a local a11y-assist run to the service. | MVP |
| E13 | Answer or confirm the agent's judgment calls in the dashboard; my answer is logged under my name and role. | Later |
| E14 | Flag a result as wrong, a bug, an improvement or a question. | Later |
| E15 | Pin sites to the top of my dashboard, from the site list. | Later |
| E16 | Have a profile: my pins, my activity log, my flags and requests, and help links (GitHub). | Later |
| E17 | Request the TT role by giving my TT ID. | Later |
| E18 | See when a newer agent scan directly contradicts an older TT-certified result. | Later |
| E19 | Export agency stats (CSV) for GSA reporting. | Later |
| E20 | Get fix advice for developers and for content editors. | Later |

### TT-certified

| ID | Story | When |
| --- | --- | --- |
| T1 | Open a pre-SCRT or SCRT file stored in the service or on my computer. | Later |
| T2 | Download any stored pre-SCRT or SCRT file. | MVP (pre-SCRT only) |
| T3 | See the audit detail of an agent run: what it examined, what it could not test, versions and model. | Later |
| T4 | Edit results, comments, locations and screenshots, as in SCRT, and certify each row with a checkbox (who and when are saved). | Later |
| T5 | Save as an updated pre-SCRT, or as a formal SCRT under my name once every row is certified and none needs review. | Later |
| T6 | Upload a complete SCRT file as a TT-certified result. | Later |
| T7 | Request scans of one or more URLs and see the queue and log. Needs a hosted runner. | Later |
| T8 | See my flags and their status. | Later |

### Admin

| ID | Story | When |
| --- | --- | --- |
| A1 | Approve or deny role requests, seeing the TT ID given. | Later |
| A2 | Work the flag queue (TT flags first): view, reply, link a GitHub issue, close. | Later |
| A3 | See and manage the scan queue and the log of runs and uploads. | Later |
| A4 | Withdraw a bad run, retire a domain, and keep the list of 544 public domains current. | Later (MVP: directly in the database) |

## Decisions

### Hosting and repo

- **Databricks Apps** hosts the results MCP server and the dashboard as one
  app, with **Lakebase** (managed Postgres) for storage. NASA already has
  Databricks. Databricks Apps can't run Playwright (no system packages), so
  the runner stays local. IBM Cloud Code Engine could host the runner later,
  only if NASA has an IBM Cloud account.
- **Same repo, separate package** (a uv workspace member), with its own
  deploy config. It does not import `a11y_assist`, so Playwright never ships
  to Databricks. A contract test feeds it a real `report.json`.
- **Results go in server to server.** A new runner tool, `a11y_publish_run`,
  sends `report.json` and `pre-scrt.json` with a SHA-256 hash. The model
  never retypes a report.
- **Hosted MCP tools are read-only for agents**: a site summary and a find
  issues tool for the MVP.

### Wording and trust

- **Three tiers**: Agent only, Human-verified, TT-certified.
- **"TT-certified"** only for rows or files certified by a TT whose role an
  admin verified.
- **"Conforms"** only for one page, as of its test date, with a complete
  TT-certified SCRT: all 61 rows, no Fail, and Not Tested only on 3.A or
  20.A (the rows SCRT allows it on). Never for a whole site unless every
  page qualifies. Agent-assisted output is never called certified,
  compliant or conformant.
- **CLAUDE.md principle 1 needs updating** to say this.
- **Non-TTs answer questions; only TTs set results directly.** Answers are
  facts the rules spec turns into outcomes; a TT's edit is a person row
  and wins.
- A person's answer always wins over the agent's; a TT's over a non-TT's.

### Which result is current

- **Latest result per test, not per run.** A run of only some tests must
  not make other tests look resolved.
- **Newest wins.** Show agent and TT-certified results side by side. Flag
  an older TT-certified result only when a newer agent scan directly
  contradicts it (a different Pass, Fail or Does Not Apply), never for
  needs review or not tested. The flag stays neutral ("disagrees"); the
  agent may be the one that's wrong.
- **Fixes are checked by the next scan** of the page. Anyone can run one
  locally and publish it.
- **Human answers don't carry over between runs** for now. Later: carry an
  answer forward when the evidence is unchanged.

### Priority ("fix first")

1. Site-wide failures of a non-interference test
2. Other site-wide failures
3. Single-page failures of a non-interference test, by share of pages failing
4. Other single-page failures, by share of pages failing

Non-interference rows (WCAG conformance requirement 5, from the SCRT
template): 1.D, 2.A, 2.B, 2.C, 3.A, 4.C. Only 4.C is automated today.
MVP: site-wide means the test fails on every tested page. Later: group by
element (same test and element on 3 or more pages).

### GSA numbers

- **Unique pages tested, last 12 months**: one per page however many runs,
  using the pa11y scanner's URL rules (`/page` and `/page/` are one page;
  query-string URLs are left out).
- **Pages TT-certified with no failures, last 12 months**: needs a complete
  TT-certified SCRT, as defined under "Conforms". Expect zero for a while.
- pa11y results are out of scope for now.

### Flags and roles

- Everyone can flag; TT flags rank higher in the admin queue. Flags carry a
  kind and duplicates group together.
- Admins grant the TT role by hand after checking the TT ID. Only the ID is
  stored, not certificate copies. Open: whether DHS can verify IDs.

### Dashboard design

- Low text: one H1, one short banner, tables with captions, evidence behind
  disclosures, no charts in the MVP.
- Every status in words, never color or icon alone; no hover-only details.
- Page text and uploaded SCRT comments are untrusted: shown as text only.
- Built on USWDS with HDS Core styling when it is built; wireframes stay
  low fidelity until the flows are settled.

## MVP for Nov 20

Read-only for people. The only data coming in is `a11y_publish_run`.

**In**

- Ingest (`a11y_publish_run`) into Lakebase, with the report hash
- E1 banner, E2 tiers (as data allows), E3 to E10 screens, E11 download
- Two hosted MCP tools: site summary, find issues
- Fix first ranking (E8)

**Stretch**

- Element-level template grouping
- "Copy prompt for Claude" buttons
- An in-chat card (MCP Apps) for the site summary

**Later**: everything marked Later above.

In the MVP, TT-certified never appears and the second GSA number stays at
zero, since there is no way to upload an SCRT yet.

## Order of work

1. **Nov 4 to 6, spike (go/no-go)**: deploy Databricks' MCP template on the
   NASA workspace; confirm Apps and Lakebase are on and Claude Code can
   connect. If blocked, run the service locally with SQLite for the demo.
2. **Nov 7 to 11**: schema, ingest, `a11y_publish_run`, the two MCP tools.
3. **Nov 12 to 14**: the four MVP screens.
4. **Nov 15 to 17**: load real runs (agent eval round 1 pages); run
   a11y-assist on the dashboard itself.
5. **Nov 18 to 19**: record the demo; update `docs/hackathon/`.

## Open questions

- Is NASA's Databricks workspace on GovCloud (FedRAMP High) or commercial?
- Can DHS verify TT IDs, and is a TT's certification tied to a test
  process version?
- Per-test "what it can't tell you" text: add a `limits` field next to each
  check's `about`.
- pre-SCRT rows don't carry the agent's reasoning; the dashboard joins it
  from `report.json` by test ID, or the row starts carrying it.
