# The Linux container image (built in GitHub Actions, run on VAST)

**Problem.** A hosted deployment needs Chromium and its system libraries on
a Linux host. NASA's VAST (internal Forgejo plus Kubernetes dev
environments) runs in FIPS mode (`/proc/sys/crypto/fips_enabled` = 1):
Ubuntu images, Playwright's official ones among them, can't start OpenSSL
there, and apt fails inside VAST's nested rootless podman. So the image
can't be built on VAST.

**What we do.** `Dockerfile` builds from Debian (`python:3.11-slim-bookworm`)
with uv, the dev group, and `playwright install --with-deps chromium`
(Chromium, the headless shell and ffmpeg), running as uid 1000; about
2.2 GB unpacked. `.github/workflows/container.yml` builds it and pushes
`ghcr.io/abbybowman/a11y-assist:latest` and `:<sha>`; VAST only pulls and
runs it. `.dockerignore` keeps `.env`, `.venv`, `.git` and `runs/` out. It
was first committed as `dockerignore`, without the dot, so Docker ignored it
and the published image held `.git` (no secret was in it: CI checks out a
clean tree with no `.env`). The workflow's path filter does not include
`tests/`, so a change only to tests does not rebuild the image; run the
workflow by hand.

**Running the suite in the image, with progress.** Under `-q` the suite
prints a dot only as each test finishes, so a slow start looks like a hang.
Run it detached, so a dropped ssh connection doesn't end it, and read the
progress file:

```bash
podman run -d --name tt ghcr.io/abbybowman/a11y-assist:latest uv run --no-sync pytest -n 4 -v -p no:cacheprovider
podman exec tt cat /app/runs/test-progress.txt
podman logs tt 2>&1 | tail -30
podman rm tt
```

`-n auto` caps workers at the container's CPU limit (see
[parallel-tests.md](parallel-tests.md)); on an image built before that fix,
pass `-n 4`. The suite takes about 15 minutes at 4 workers.

## Working on a VAST dev environment

- **Each session:** `vastdev login`, then `vastdev up`, then
  `ssh <you>-dev`. `vastdev up` requests a fresh SSH certificate; without
  it, ssh fails with `Permission denied (publickey)` once yesterday's
  certificate has expired. The access token lasts 5 minutes and the
  refresh token 30, so after about 30 idle minutes `vastdev` logs in again.
- **Use PowerShell or Windows Terminal for ssh,** not Git Bash. vastdev
  writes Win32-OpenSSH's config, and Win32 ssh inside Git Bash's mintty
  window shows no prompt or output, so it looks hung while it is in fact
  logged in. Commands typed then run on VAST: `C:\...` paths fail there and
  ssh asks about VAST's own host key. If you must use Git Bash, put
  `winpty` in front of `/c/Windows/System32/OpenSSH/ssh.exe`.
- **Knowing where you are:** the dev container is a minimal RHEL 8.10
  with no `hostname` command (use `uname -n` or
  `cat /etc/redhat-release`), and its login shell does not read
  `~/.bashrc`. Add `[ -f ~/.bashrc ] && . ~/.bashrc` to `~/.bash_profile`
  and set a prompt such as `PS1="[vast \w]\$ "` in `~/.bashrc`.
- **Storage:** home is a 20 GB volume and persists across container
  restarts (an image pulled two days earlier was still there after a
  restart). Rootless podman keeps its images there
  (`~/.local/share/containers/storage`), so pulls count against it.
- **Dropped connections:** on 2026-11-06 opening a second ssh session
  closed the first and reset the second while the container stayed up
  (`stat -c %y /proc/1` showed it had started hours earlier, and
  `oom_kill` was 0). Cause unknown; until it is, use one session and run
  long jobs detached.

**How we know.** 2026-11-06: the `:latest` image in Docker on a 4-CPU Linux
host: the default 64 MB `/dev/shm` is enough (Playwright launches Chromium
with `--disable-dev-shm-usage`), and the full suite ran with 4 workers: 930
passed, 3 skipped, 1 xfailed, no failures, in 14 min 52 s. On VAST, the same
day: Chromium in the image loaded https://www.nasa.gov, and the suite
(an older `:latest` with 793 tests) runs detached with `-n 4`; its result is
recorded below once it finishes.
