from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_trace_id() -> str:
    return uuid.uuid4().hex


def new_run_id() -> str:
    return uuid.uuid4().hex


def new_step_attempt_id() -> str:
    return uuid.uuid4().hex[:16]


def trace_export_path(traces_dir: Path, trace_id: str, prefix: str = "trace") -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return traces_dir / f"{ts}_{prefix}_{trace_id}.json"

