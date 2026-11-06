"""A run folder: runs/<run_id>/ with evidence/, steps.jsonl and report.json."""

from __future__ import annotations

import json
import secrets
import shutil
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from a11y_assist.access import claim_run, may_open
from a11y_assist.models import StepLog, utcnow
from a11y_assist.redact import safe_detail


def new_run_id() -> str:
    # Windows-safe (no colons) and sortable.
    return utcnow().strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)


class RunRecorder:
    def __init__(self, runs_dir: Path, run_id: str | None = None):
        new = run_id is None
        self.run_id = run_id or new_run_id()
        self.dir = (runs_dir / self.run_id).resolve()
        self.evidence_dir = self.dir / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        if new:
            claim_run(self.dir)  # signed-in caller owns it (access.py)
        self.steps_path = self.dir / "steps.jsonl"
        self.report_path = self.dir / "report.json"

    @classmethod
    def open(cls, runs_dir: Path, run_id: str) -> RunRecorder:
        """Reopen an existing run. Rejects ids that could escape runs_dir."""
        root = runs_dir.resolve()
        path = (root / run_id).resolve()
        # Another person's run reads as missing, so its id reveals nothing.
        if path.parent != root or not path.is_dir() or not may_open(path):
            # No server path in the message: it goes back to the client.
            raise FileNotFoundError(f"No run named {run_id!r} (it may have expired)")
        return cls(runs_dir, run_id)

    def log(self, step: str, status: str = "ok", **detail: Any) -> None:
        # Redacted at the sink, so no caller can log a query string (redact.py).
        entry = StepLog(step=step, status=status, detail=safe_detail(detail))
        with self.steps_path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

    def rel(self, path: Path) -> str:
        return path.resolve().relative_to(self.dir).as_posix()

    def write_json(self, path: Path, data: BaseModel | dict) -> Path:
        text = (
            data.model_dump_json(indent=2)
            if isinstance(data, BaseModel)
            else json.dumps(data, indent=2, default=str)
        )
        path.write_text(text + "\n", encoding="utf-8")
        return path


def prune_runs(runs_dir: Path, ttl_hours: float) -> int:
    """Delete run folders older than `ttl_hours`. Runs are working files for
    finishing a run (answers, overrides), not an archive. Returns the count."""
    if not runs_dir.is_dir():
        return 0
    cutoff = time.time() - ttl_hours * 3600
    n = 0
    for d in runs_dir.iterdir():
        if d.is_dir() and _last_activity(d) < cutoff:
            shutil.rmtree(d, ignore_errors=True)
            n += 1
    return n


def expires_at(run_dir: Path, ttl_hours: float):
    from datetime import datetime, timezone

    return datetime.fromtimestamp(
        _last_activity(run_dir) + ttl_hours * 3600, tz=timezone.utc
    )


def _last_activity(run_dir: Path) -> float:
    report = run_dir / "report.json"
    return (report if report.exists() else run_dir).stat().st_mtime
