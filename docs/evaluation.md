# Evaluation Harness

The evaluation harness runs a scenario matrix (`eval/scenarios.json`) and scores each run automatically.

## Scenario Fields

- `id`, `description`
- `request`, optional `context`
- optional `config_overrides`
- `expected_status`
- optional `expected_stop_reason`
- `required_output_contains`
- `required_trace_events`
- `forbidden_trace_events`

## Outputs

- Per-scenario trace JSON exported to `runtime/traces/`
- `eval_summary.json` with pass/fail and reasons
- SQLite persistence of eval results (`eval_results` table)

## Scoring

`eval/scoring.py` checks:

- final status matches expected
- stop reason matches when specified
- required substrings exist in trace JSON
- required/forbidden trace tokens (failure types, refinement actions, stop reasons)

