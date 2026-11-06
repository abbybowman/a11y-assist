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

RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app

# stdio by default. HTTP still listens on loopback only until authentication
# exists (see app.py), so this image is for running tests and runs, not yet
# for serving MCP over the network.
CMD ["uv", "run", "--no-sync", "tobi508"]
