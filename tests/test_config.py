"""Settings load the server's own .env, whatever directory a client launches
the server from."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tobi508.config import ENV_FILE, REPO_ROOT

PROBE = (
    "import json; from tobi508.config import ENV_FILE, Settings; "
    "s = Settings(); "
    "print(json.dumps({'env_file': str(ENV_FILE), 'port': s.mcp_port, "
    "'dev': s.dev_mode}))"
)


def _launch_from(cwd: Path, env_file: Path | None = None) -> dict:
    code = PROBE
    if env_file is not None:  # the same code path, pointed at a test file
        code = PROBE.replace(
            "s = Settings()", f"s = Settings(_env_file={str(env_file)!r})"
        )
    env = {"PATH": "/usr/bin:/bin"}  # no MCP_PORT / DEV_MODE from the caller
    if sys.platform == "win32":  # without it, asyncio's import fails (WinError 10106)
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return json.loads(out.stdout)


def test_env_file_is_the_repo_root_one():
    assert ENV_FILE == REPO_ROOT / ".env" and ENV_FILE.is_absolute()
    assert (REPO_ROOT / "pyproject.toml").is_file()


def test_launch_from_another_directory_ignores_its_env(tmp_path):
    # A client starts the server in some other project that has its own .env.
    (tmp_path / ".env").write_text("MCP_PORT=9123\nDEV_MODE=true\n")
    got = _launch_from(tmp_path)
    assert got["env_file"] == str(REPO_ROOT / ".env")
    assert got["port"] != 9123 and got["dev"] is False


def test_an_env_file_is_read_from_any_directory(tmp_path):
    env = tmp_path / "server.env"
    env.write_text("MCP_PORT=9124\n")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    assert _launch_from(elsewhere, env)["port"] == 9124


def test_an_unbuilt_judge_backend_is_refused_at_startup():
    import pytest
    from pydantic import ValidationError

    from tobi508.config import Settings

    for bad in ("api", "clinet"):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, judge_backend=bad)
    assert Settings(_env_file=None).judge_backend == "client"
