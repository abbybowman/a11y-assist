# Editing code that the formatter reflows

**Problem (for agents editing this repo).** `ruff format` rewraps long calls
and dicts. A later exact-string edit written against the pre-format text then
fails to match, and a script that asserts on the match aborts *before
writing*, so none of its edits land. This happened several times.

**What to do.** Run `uv run ruff format` right after each edit, then edit
against the formatted text. For larger changes, replace a block between two
stable marker lines (a comment or a `def`) instead of matching a long
expression. Check `git diff` after scripted edits.
