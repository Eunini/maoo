# Safety and Policy

MAOO is designed to be safe by default:

- No shell execution tool is implemented.
- HTTP tools are restricted to allowlisted hosts (`localhost`, `127.0.0.1`, `mock-api`) unless `MAOO_ENABLE_REAL_HTTP=true`.
- `db_query` is read-only by default and only permits `SELECT` / `PRAGMA`.
- `file_write` is sandboxed to the configured workspace root.
- `calc` uses a strict AST whitelist (arithmetic only).
- Executors use bounded retries and stop conditions to prevent loops.

## Feature Flags (default OFF where relevant)

- `MAOO_NO_LLM_MODE=true` (offline deterministic mode)
- `MAOO_ENABLE_REAL_HTTP=false`
- `MAOO_ENABLE_DB_WRITES=false`

## Safe Demo Defaults

- Mock API server for HTTP interactions
- SQLite local file for persistence
- Trace export for inspection and debugging

