# Hackathon submission docs

Drafts of the two documents the GSA MCP and AI Agent Hackathon asks for, kept
in Markdown so they change with the code.

| File | GSA deliverable |
| --- | --- |
| [evaluation.md](evaluation.md) | Evaluation document (GSA's sample: `MCP-hackathon-sample-evaluation-document.docx`) |
| [deck.md](deck.md) | Presentation deck, one section per slide (GSA's sample: `MCP-hackathon-sample-deck.pptx`) |

## Markers

- **[FILL: …]** a final figure. Copy it from the scored submission run, never from a run during development.
- **[PENDING]** work not done yet. Remove the marker only when the work exists and has been checked.

## Keeping them current

- **These Markdown files are the source.** Render them into GSA's Word and PowerPoint templates only at submission time.
- **Update in the same commit.** When a TT test, spec version, evaluation method or security control changes, update `evaluation.md` and the matching slide in `deck.md` in the same commit. Keep figures as [FILL] until the submission run.
- **Fill in from one run.** At submission, run the scored suite once at the submission commit and fill every [FILL] from that run, with its commit, date and environment.
- **No certification claims.** Never describe a tested page as certified, compliant or Section 508 conformant (CLAUDE.md principle 1).

Submission is due Nov 20, 2026 (subject to change). Hackathon page: https://www.gsa.gov/super-intelligence/si-community-of-practice/events-and-training/mcp-server-and-si-agent-government-hackathon
