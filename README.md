# MAOO: Multi-Agent Autonomous Operations Orchestrator

MAOO is a portfolio-grade Python project demonstrating a coordinated 3-layer autonomous AI architecture:

1. Perception (intent + state extraction)
2. Planning (task decomposition + tool planning)
3. Execution (tool calls + monitoring + adaptive refinement)

It includes a CLI demo, strict tool schemas, a mock API server with fault injection, SQLite-backed memory, observability, and an evaluation harness with 24 scenarios.

## Features

- 3-layer agent pipeline with typed interfaces
- Safe allowlisted tool execution with Pydantic schemas
- Feedback monitoring + adaptive refinement (retry / patch args / replan)
- Stop guards (`max_steps`, retries, budget, non-progress)
- Short-term and long-term memory (SQLite)
- Structured logs, trace IDs, metrics counters
- Offline deterministic mode (`MAOO_NO_LLM_MODE=true`)
- Optional OpenAI-compatible LLM integration (feature-flagged)
- Docker Compose demo (`app` + `mock-api`)

## Quick Start (Local)

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

Run the mock API:

```bash
python -m mock_api.server
```

Run a demo:

```bash
python -m cli demo happy
python -m cli demo refinement
python -m cli demo stop
```

Run a custom request:

```bash
python -m cli run --request "Fetch mock data, calculate 2 + 2, and summarize the result"
```

Run evaluation:

```bash
python -m cli eval
```

## Quick Start (Docker Compose)

Build and start the mock API:

```bash
docker compose up --build -d mock-api
```

Run a demo from the app container:

```bash
docker compose run --rm app python -m cli demo happy
docker compose run --rm app python -m cli demo refinement
docker compose run --rm app python -m cli demo stop
```

Run evaluation:

```bash
docker compose run --rm app python -m cli eval
```

## CLI Output Shows (Required Views)

- User request
- Perceived intent + structured state JSON
- Plan (steps)
- Execution logs + tool calls
- Final output

## Architecture Explanation

### Modules

- `core/`: shared types, config, logging, metrics, tracing
- `memory/`: short-term scratchpad + SQLite long-term memory/retrieval
- `perception/`: intent extraction, task classification, state building
- `planning/`: planner, policy engine, plan validation, critic
- `execution/`: tool schemas/registry, tools, executor, monitors, refinement
- `mock_api/`: FastAPI fault-injection API for demos/tests
- `eval/`: scenarios, runner, scoring, trace export
- `cli/`: Typer + Rich interface

### ASCII Architecture Diagram

```text
┌──────────────┐
│ User Request │
└──────┬───────┘
       v
┌──────────────┐
│ Perception   │ intent/task/entities/constraints/success criteria
│ Agent        │
└──────┬───────┘
       v
┌──────────────┐     ┌──────────────┐
│ Planner      ├────>│ Policy +     │
│ Agent        │     │ Plan Validator│
└──────┬───────┘     └──────┬───────┘
       │ valid plan                │
       └──────────────┬────────────┘
                      v
               ┌──────────────┐
               │ Executor     │
               │ + Monitors   │<──────┐
               │ + Refinement │       │ failure signal
               └──────┬───────┘       │
                      v               │
               ┌──────────────┐       │
               │ Tool Registry│───────┘
               │ (allowlist + │
               │ schemas)     │
               └──────┬───────┘
                      v
       ┌─────────────────────────────────────┐
       │ http_get/http_post/db_query/        │
       │ file_write/calc/summarize           │
       └─────────────────────────────────────┘
```

## Reliability + Safety Choices

- Mocked tools and mock API are the default path
- Optional real integrations are behind flags and OFF by default
- HTTP allowlist and SQL/file/calc policy constraints
- Strict schema validation before and during execution
- Retry/replan logic is bounded by stop rules
- Non-progress detection prevents infinite loops
- Full trace export enables debugging and evaluation

## Evaluation Harness

- `eval/scenarios.json` includes 24 scenarios
- automatic scoring (`success/fail + reason`)
- trace export per scenario (`runtime/traces/*.trace.json`)
- JSON summary export (`runtime/traces/eval_summary.json`)

## Portfolio Story

### Problem

Single-agent demos often look good on happy paths but fail under tool errors, malformed responses, or repeated retries. Real autonomous systems need explicit control loops, typed boundaries, and safe execution constraints.

### Approach

MAOO separates the agent into three layers with typed contracts:

- perception normalizes the request into structured state
- planning generates explicit tool steps
- execution runs a monitored control loop with adaptive refinement

This separation makes the system inspectable, testable, and safer to evolve.

### What Makes It Autonomous

- The executor monitors each tool call
- Failures are classified into normalized signals
- A refinement engine chooses patch/retry or replanning
- The run adapts while staying within hard stop guards

### Reliability and Safety Highlights

- Allowlisted tools only
- Strict Pydantic schemas for tool args/results
- Mock API fault injection for repeatable failure drills
- SQLite trace + memory persistence for debugging and retrieval
- Offline deterministic mode for portfolio demos and CI

## Files to Explore

- `main.py`
- `execution/executor.py`
- `execution/refinement.py`
- `planning/planner.py`
- `perception/agent.py`
- `mock_api/routes.py`
- `eval/runner.py`
- `eval/scenarios.json`

## Notes

- `examples/traces/` contains example traces for the three requested demo scenarios.
- If you enable a real OpenAI-compatible endpoint, set `MAOO_OPENAI_BASE_URL` and `MAOO_OPENAI_API_KEY`.

