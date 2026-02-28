CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  status TEXT NOT NULL,
  request_json TEXT NOT NULL,
  final_output_json TEXT,
  stop_reason TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT
);

CREATE TABLE IF NOT EXISTS traces (
  trace_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  trace_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  namespace TEXT NOT NULL,
  key TEXT NOT NULL,
  value_text TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_outcomes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trace_id TEXT NOT NULL,
  step_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  status TEXT NOT NULL,
  latency_ms INTEGER NOT NULL,
  outcome_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scenario_id TEXT NOT NULL,
  passed INTEGER NOT NULL,
  reason TEXT NOT NULL,
  score REAL NOT NULL,
  trace_path TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS demo_numbers (
  id INTEGER PRIMARY KEY,
  label TEXT NOT NULL,
  value REAL NOT NULL
);

