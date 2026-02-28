# MAOO Architecture

MAOO implements a 3-layer autonomous orchestration flow:

1. `perception/`: converts raw user requests into structured intent/state (`PerceptionResult`)
2. `planning/`: decomposes tasks into tool steps (`Plan`) and validates safety/policy
3. `execution/`: runs tools with monitoring, retries/replanning, and stop guards

## High-level Data Flow

```text
User Request
   |
   v
PerceptionAgent ---> PerceptionResult
   |
   v
PlannerAgent -----> Plan -----> PlanValidator + PolicyEngine
   |                                   |
   +-----------------------------------+
                   valid plan
                       |
                       v
Executor -> ToolRegistry -> Tools -> Observations
   |            |             |
   |            |             +--> Mock API / SQLite / File workspace
   |            +--> strict schemas (Pydantic)
   |
   +--> Monitors -> FailureSignal -> RefinementEngine -> retry or replan
   |
   +--> RunTrace + logs + metrics + long-term memory persistence
```

## Runtime State Machine

`RECEIVED -> PERCEIVED -> PLANNED -> VALIDATED -> EXECUTING -> (REFINING -> EXECUTING)* -> COMPLETED|STOPPED|FAILED`

## Key Reliability Features

- allowlisted tool registry + policy checks
- strict tool arg/result schemas
- monitor-driven refinement (patch/retry/replan)
- stop guards (`max_steps`, `max_retries`, budget, non-progress)
- structured logs, trace IDs, metrics snapshot

