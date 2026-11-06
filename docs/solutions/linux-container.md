# The Linux container image (built in GitHub Actions, run on VAST)

**Problem.** A hosted deployment needs Chromium and its system libraries on
a Linux host. NASA's VAST runs in FIPS mode
(`/proc/sys/crypto/fips_enabled` = 1): Ubuntu images, Playwright's official
ones among them, can't start OpenSSL there, and apt fails inside VAST's
nested rootless podman. So the image can't be built on VAST.

**What we do.** `Dockerfile` builds from Debian (`python:3.11-slim-bookworm`)
with uv, the dev group, and `playwright install --with-deps chromium`
(Chromium, the headless shell and ffmpeg), running as uid 1000.
`.github/workflows/container.yml` builds it and pushes
`ghcr.io/abbybowman/a11y-assist:latest` and `:<sha>`; VAST only pulls and
runs it. `.dockerignore` keeps `.env`, `.venv`, `.git` and `runs/` out. It
was first committed as `dockerignore`, without the dot, so Docker ignored it
and the published image held `.git` (no secret was in it: CI checks out a
clean tree with no `.env`).

**Running the suite in the image, with progress.** Under `-q` the suite
prints a dot only as each test finishes, so a slow start looks like a hang.
Run with `-v` into a log, or read the progress file from another shell:

```bash
podman run --rm --name tt ghcr.io/abbybowman/a11y-assist:latest uv run --no-sync pytest -v -p no:cacheprovider
podman exec tt cat /app/runs/test-progress.txt
```

`-n auto` caps workers at the container's CPU limit (see
[parallel-tests.md](parallel-tests.md)); on an image built before that fix,
pass `-n 4`.

**How we know.** 2026-11-06, the `:latest` image in Docker on a 4-CPU Linux
host: the default 64 MB `/dev/shm` is enough (Playwright launches Chromium
with `--disable-dev-shm-usage`), and the full suite ran with 4 workers: 930 passed, 3 skipped,
1 xfailed, no failures, in 14 min 52 s. On VAST: pulling the image and loading
https://www.nasa.gov from Chromium inside it worked; the suite there is not
yet confirmed.
