# Round 1: what is in git and what is in the archive

The round's page recordings (`*.har.zip`), screenshots (`*.png`) and tool
evidence (`runs/*/evidence/`) are not in git: together about 800 MB.
They are in an archive Abby keeps (2026-11-04), a complete snapshot of
`evals/judging/round1/` as it was at the first lock:

| File | SHA-256 |
| --- | --- |
| `round1-frozen.zip` | `768b8f5f1ca03cf44e8e8162f368fb3ee678e80083ca462010857220141fc390` |
| `round1-results.zip` | `2155e49f1ab671dc6804e17aaf73a72ec4651498c286a29b60eaa640752bca5b` |
| `round1-attempts.zip` | `aae3567c2880f40c856b47986cca1cfa44b72e38ee42491100826efc78e189ad` |
| `MANIFEST-round1.json` (SHA-256 of all 10,528 files) | `b05042815da5323ca65bbf41ff851ca0dc0053caf0396218e97ba25e35c80d70` |

To restore, unzip the three zips into the repository root; the files land
at their paths under `evals/judging/round1/`. Check them against the
manifest.

What stays in git is what scoring and an audit read: each arm's
transcript, step log, summary and final message; each tool run's
`report.json`, `pre-scrt.json` (screenshots inline) and `steps.jsonl`;
the frozen index; and the locks.

## Why there are two locks

`lock-1.json` is the first lock (2026-11-04 16:34 UTC, before any answer
key). It covered files that were never in git: `.gitignore` excluded every
`runs/` folder, so the tool runs' reports existed only in the cloud session,
and the recordings made the repository too large to clone. So, still before
any answer key (Abby, 2026-11-04):

1. the round folder was archived, as above;
2. the recordings and screenshots were removed from git history
   (`git filter-repo`; commit hashes changed, so `lock-1.json`'s
   `code_commit` names a commit from before the rewrite);
3. the tool runs' reports, pre-SCRT files and step logs were committed;
4. the round was locked again: `lock.json` covers what is in git,
   `lock-1.json` included.

No result changed: every file in both git and the archive has the same
SHA-256 in both (the manifest).
