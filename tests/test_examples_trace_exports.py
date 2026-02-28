from __future__ import annotations

from pathlib import Path

from core.types import RunTrace


def test_example_traces_validate_against_runtrace_schema():
    trace_dir = Path("examples/traces")
    files = sorted(trace_dir.glob("*.json"))
    assert len(files) >= 3
    for f in files:
        trace = RunTrace.model_validate_json(f.read_text(encoding="utf-8"))
        assert trace.trace_id
        assert trace.run_id

