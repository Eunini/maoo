from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.types import EvalSummary, RunTrace


def export_trace(trace: RunTrace, export_dir: str | Path, filename: str) -> Path:
    p = Path(export_dir)
    p.mkdir(parents=True, exist_ok=True)
    target = p / filename
    target.write_text(trace.model_dump_json(indent=2), encoding="utf-8")
    return target


def export_eval_summary(summary: EvalSummary, export_dir: str | Path, filename: str = "eval_summary.json") -> Path:
    p = Path(export_dir)
    p.mkdir(parents=True, exist_ok=True)
    target = p / filename
    target.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    return target


def export_json(data: dict[str, Any], export_dir: str | Path, filename: str) -> Path:
    p = Path(export_dir)
    p.mkdir(parents=True, exist_ok=True)
    target = p / filename
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return target

