# Linux container image for the server and its tests, for hosts such as VAST.
#
# Built by .github/workflows/container.yml, not on VAST itself: VAST hosts run
# in FIPS mode, and apt can't run inside VAST's nested containers.
#
# Debian rather than Playwright's Ubuntu images: on a FIPS-mode host, Ubuntu's
# OpenSSL tries to load a FIPS module that Ubuntu doesn't ship, and fails.
FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /usr/local/bin/

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, so a code change doesn't reinstall them.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --group dev --no-install-project

# Chromium and the system libraries it needs.
RUN uv run --no-sync playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN uv sync --frozen --group dev

# Hosted defaults (any of them can be overridden with -e or the platform's
# environment). A container has Playwright's Chromium and no display, not
# installed Chrome with a window (config.py's defaults, for a tester's own
# machine). Runs and the sign-in proxy's client registrations live under
# /data: mount persistent storage there, or point RUNS_DIR and FASTMCP_HOME
# at it (on VAST, anything under the home volume survives restarts).
ENV BROWSER_CHANNEL=chromium \
    HEADLESS=true \
    RUNS_DIR=/data/runs \
    FASTMCP_HOME=/data/fastmcp

RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data/runs /data/fastmcp \
    && chown -R app /app /data
USER app

# The server: HTTP on 0.0.0.0:8000 (VAST's port). Without AUTH=oidc and its
# settings it refuses to start (app.http_options), so a deployment missing
# its secrets fails closed. MCP_TRANSPORT and MCP_HOST are defaults for this
# command only, not image-wide, so `podman run <image> uv run pytest` sees a
# clean environment. MCP_TRANSPORT=stdio runs it for a local client instead.
EXPOSE 8000
CMD ["sh", "-c", "exec env MCP_TRANSPORT=\"${MCP_TRANSPORT:-streamable-http}\" MCP_HOST=\"${MCP_HOST:-0.0.0.0}\" uv run --no-sync tobi508"]
