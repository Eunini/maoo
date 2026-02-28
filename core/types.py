from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskType(str, Enum):
    DATA_RETRIEVAL = "data_retrieval"
    DATA_SUBMISSION = "data_submission"
    DATABASE = "database"
    FILE_OPS = "file_ops"
    CALCULATION = "calculation"
    SUMMARIZATION = "summarization"
    COMPOSITE = "composite"
    UNKNOWN = "unknown"


class RunStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PERCEIVED = "PERCEIVED"
    PLANNED = "PLANNED"
    VALIDATED = "VALIDATED"
    EXECUTING = "EXECUTING"
    REFINING = "REFINING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    RETRYING = "RETRYING"


class FailureType(str, Enum):
    TIMEOUT = "timeout"
    TOOL_ERROR = "tool_error"
    SCHEMA_ERROR = "schema_error"
    BAD_RESPONSE = "bad_response"
    POLICY_VIOLATION = "policy_violation"
    VALIDATION_ERROR = "validation_error"
    BUDGET_EXCEEDED = "budget_exceeded"
    NON_PROGRESS = "non_progress"
    UNKNOWN = "unknown"


class RefinementActionType(str, Enum):
    NONE = "none"
    PATCH_AND_RETRY = "patch_and_retry"
    REPLAN_REMAINING = "replan_remaining"
    SKIP_STEP = "skip_step"
    ABORT = "abort"


class StopReasonType(str, Enum):
    SUCCESS_CRITERIA_MET = "success_criteria_met"
    MAX_STEPS = "max_steps"
    MAX_RETRIES = "max_retries"
    BUDGET_GUARD = "budget_guard"
    NON_PROGRESS = "non_progress"
    FAILED = "failed"
    POLICY_BLOCKED = "policy_blocked"
    VALIDATION_FAILED = "validation_failed"
    NONE = "none"


class ToolCallStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SCHEMA_ERROR = "schema_error"
    POLICY_BLOCKED = "policy_blocked"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BudgetGuard(BaseModel):
    max_cost_units: int = 50
    max_tokens: int | None = None
    cost_per_step: int = 1


class PerceptionResult(BaseModel):
    intent: str
    task_type: TaskType
    entities: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    initial_state: dict[str, Any] = Field(default_factory=dict)


class PlanStep(BaseModel):
    step_id: str
    objective: str
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    expected_observation: str
    fallback_strategy: str = "retry_or_abort"


class Plan(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)
    max_steps: int = 12
    max_retries_per_step: int = 2
    budget_guard: BudgetGuard = Field(default_factory=BudgetGuard)
    planner_notes: list[str] = Field(default_factory=list)


class ValidatedPlan(BaseModel):
    plan: Plan
    warnings: list[str] = Field(default_factory=list)


class ToolCatalogEntry(BaseModel):
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    safe_by_default: bool = True


class FailureSignal(BaseModel):
    failure_type: FailureType
    retryable: bool
    severity: Severity = Severity.MEDIUM
    message: str
    recommended_action: str
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class RefinementDecision(BaseModel):
    action: RefinementActionType
    patched_args: dict[str, Any] | None = None
    replanned_steps: list[PlanStep] | None = None
    reason: str


class ToolCallRecord(BaseModel):
    step_id: str
    step_attempt_id: str
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    validated_args: dict[str, Any] = Field(default_factory=dict)
    status: ToolCallStatus
    latency_ms: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    raw_response: Any = None
    ts: str = Field(default_factory=utc_now_iso)


class StepEvent(BaseModel):
    step_id: str
    attempt: int
    status: StepStatus
    message: str
    observation: dict[str, Any] | None = None
    failure_signal: FailureSignal | None = None
    refinement_decision: RefinementDecision | None = None
    ts: str = Field(default_factory=utc_now_iso)


class StopReason(BaseModel):
    type: StopReasonType = StopReasonType.NONE
    message: str = ""


class RunTrace(BaseModel):
    trace_id: str
    run_id: str
    request: dict[str, Any]
    status: RunStatus = RunStatus.RECEIVED
    perception: PerceptionResult | None = None
    plan: Plan | None = None
    step_events: list[StepEvent] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    monitor_signals: list[FailureSignal] = Field(default_factory=list)
    refinements: list[RefinementDecision] = Field(default_factory=list)
    final_output: dict[str, Any] = Field(default_factory=dict)
    metrics_snapshot: dict[str, int] = Field(default_factory=dict)
    stop_reason: StopReason = Field(default_factory=StopReason)
    started_at: str = Field(default_factory=utc_now_iso)
    finished_at: str | None = None


class ExecutionResult(BaseModel):
    status: RunStatus
    final_output: dict[str, Any]
    stop_reason: StopReason
    completed_steps: int = 0


class EvalScenario(BaseModel):
    id: str
    description: str
    request: str
    context: dict[str, Any] = Field(default_factory=dict)
    config_overrides: dict[str, Any] = Field(default_factory=dict)
    expected_status: str
    required_output_contains: list[str] = Field(default_factory=list)
    required_trace_events: list[str] = Field(default_factory=list)
    forbidden_trace_events: list[str] = Field(default_factory=list)
    expected_stop_reason: str | None = None


class EvalScenarioResult(BaseModel):
    scenario_id: str
    passed: bool
    reason: str
    score: float = 0.0
    trace_path: str | None = None


class EvalSummary(BaseModel):
    total: int
    passed: int
    failed: int
    results: list[EvalScenarioResult]


@dataclass
class ToolExecutionContext:
    trace_id: str
    run_id: str
    step_id: str
    attempt: int
    config: Any
    logger: Any
    short_term_memory: Any
    long_term_memory: Any
    metrics: Any


@dataclass
class RunContext:
    config: Any
    logger: Any
    metrics: Any
    trace: RunTrace
    registry: Any
    policy: Any
    short_term_memory: Any
    long_term_memory: Any
    planner: Any
    monitors: Any
    refinement: Any


class PromptRequest(BaseModel):
    raw_goal: str
    context: dict[str, Any] = Field(default_factory=dict)


class TraceExportEnvelope(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    trace: RunTrace
    exported_at: str = Field(default_factory=utc_now_iso)

