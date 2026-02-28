from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from core.types import RunTrace
from core.tracing import utc_now_iso


class LongTermMemory:
    def __init__(self, sqlite_path: Path, schema_path: Path | None = None, seed_path: Path | None = None) -> None:
        self.sqlite_path = Path(sqlite_path)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.schema_path = schema_path
        self.seed_path = seed_path
        self._initialized = False
        self._ensure_initialized()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        with self._connect() as conn:
            if self.schema_path and self.schema_path.exists():
                conn.executescript(self.schema_path.read_text(encoding="utf-8"))
            if self.seed_path and self.seed_path.exists():
                conn.executescript(self.seed_path.read_text(encoding="utf-8"))
            conn.commit()
        self._initialized = True

    def query(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        self._ensure_initialized()
        with self._connect() as conn:
            cur = conn.execute(sql, params or [])
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> int:
        self._ensure_initialized()
        with self._connect() as conn:
            cur = conn.execute(sql, params or [])
            conn.commit()
            return cur.rowcount

    def add_memory_entry(
        self,
        namespace: str,
        key: str,
        value_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.execute(
            "INSERT INTO memory_entries(namespace, key, value_text, metadata_json, created_at) VALUES(?,?,?,?,?)",
            [namespace, key, value_text, json.dumps(metadata or {}), utc_now_iso()],
        )

    def get_memory_entries(self, namespace: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        if namespace:
            return self.query(
                "SELECT * FROM memory_entries WHERE namespace = ? ORDER BY id DESC LIMIT ?",
                [namespace, limit],
            )
        return self.query("SELECT * FROM memory_entries ORDER BY id DESC LIMIT ?", [limit])

    def save_tool_outcome(
        self,
        trace_id: str,
        step_id: str,
        tool_name: str,
        status: str,
        latency_ms: int,
        outcome: dict[str, Any] | None,
    ) -> None:
        self.execute(
            "INSERT INTO tool_outcomes(trace_id, step_id, tool_name, status, latency_ms, outcome_json, created_at) VALUES(?,?,?,?,?,?,?)",
            [trace_id, step_id, tool_name, status, latency_ms, json.dumps(outcome or {}), utc_now_iso()],
        )

    def save_trace(self, trace: RunTrace) -> None:
        trace_json = trace.model_dump_json()
        self.execute(
            "INSERT OR REPLACE INTO runs(run_id, trace_id, status, request_json, final_output_json, stop_reason, started_at, finished_at) VALUES(?,?,?,?,?,?,?,?)",
            [
                trace.run_id,
                trace.trace_id,
                trace.status.value,
                json.dumps(trace.request),
                json.dumps(trace.final_output),
                trace.stop_reason.type.value if trace.stop_reason else "",
                trace.started_at,
                trace.finished_at,
            ],
        )
        self.execute(
            "INSERT OR REPLACE INTO traces(trace_id, run_id, trace_json, created_at) VALUES(?,?,?,?)",
            [trace.trace_id, trace.run_id, trace_json, utc_now_iso()],
        )

    def save_eval_result(self, scenario_id: str, passed: bool, reason: str, score: float, trace_path: str | None) -> None:
        self.execute(
            "INSERT INTO eval_results(scenario_id, passed, reason, score, trace_path, created_at) VALUES(?,?,?,?,?,?)",
            [scenario_id, 1 if passed else 0, reason, score, trace_path, utc_now_iso()],
        )

