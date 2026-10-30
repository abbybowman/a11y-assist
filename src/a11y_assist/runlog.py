"""A run folder: runs/<run_id>/ with evidence/, steps.jsonl and report.json."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from a11y_assist.models import StepLog, utcnow


def new_run_id() -> str:
    # Windows-safe (no colons) and sortable.
    return utcnow().strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)


class RunRecorder:
    def __init__(self, runs_dir: Path, run_id: str | None = None):
        self.run_id = run_id or new_run_id()
        self.dir = (runs_dir / self.run_id).resolve()
        self.evidence_dir = self.dir / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.steps_path = self.dir / "steps.jsonl"
        self.report_path = self.dir / "report.json"

    @classmethod
    def open(cls, runs_dir: Path, run_id: str) -> RunRecorder:
        """Reopen an existing run. Rejects ids that could escape runs_dir."""
        root = runs_dir.resolve()
        path = (root / run_id).resolve()
        if path.parent != root or not path.is_dir():
            raise FileNotFoundError(f"No run named {run_id!r} in {root}")
        return cls(runs_dir, run_id)

    def log(self, step: str, status: str = "ok", **detail: Any) -> None:
        entry = StepLog(step=step, status=status, detail=detail)
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
