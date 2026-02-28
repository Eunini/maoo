from __future__ import annotations

import json
import time
from typing import Any

from core.exceptions import PolicyViolationError, ToolExecutionError
from core.tracing import new_step_attempt_id, utc_now_iso
from core.types import (
    ExecutionResult,
    FailureSignal,
    FailureType,
    PerceptionResult,
    Plan,
    PlanStep,
    RefinementActionType,
    RunContext,
    RunStatus,
    StepEvent,
    StepStatus,
    StopReason,
    StopReasonType,
    ToolCallRecord,
    ToolCallStatus,
    ToolExecutionContext,
)


class Executor:
    def run(self, plan: Plan, perception: PerceptionResult, run_ctx: RunContext) -> ExecutionResult:
        trace = run_ctx.trace
        trace.status = RunStatus.EXECUTING
        steps: list[PlanStep] = [PlanStep.model_validate(s.model_dump()) for s in plan.steps]
        stm = run_ctx.short_term_memory
        metrics = run_ctx.metrics
        logger = run_ctx.logger.child(component="execution", trace_id=trace.trace_id, run_id=trace.run_id)

        completed_steps = 0
        cost_units = 0
        step_index = 0
        final_output = {
            "message": "Execution started",
            "step_outputs": {},
            "observations": [],
        }

        metrics.inc("runs_started_total")

        while step_index < len(steps):
            trace.status = RunStatus.EXECUTING
            success_met = self._success_criteria_met(perception.success_criteria, stm)
            if success_met:
                trace.status = RunStatus.STOPPED
                trace.stop_reason = StopReason(
                    type=StopReasonType.SUCCESS_CRITERIA_MET,
                    message="Success criteria met before executing remaining steps",
                )
                break

            if completed_steps >= plan.max_steps:
                trace.status = RunStatus.STOPPED
                trace.stop_reason = StopReason(type=StopReasonType.MAX_STEPS, message="max_steps reached")
                break

            if cost_units >= plan.budget_guard.max_cost_units:
                trace.status = RunStatus.STOPPED
                trace.stop_reason = StopReason(type=StopReasonType.BUDGET_GUARD, message="Budget guard exceeded")
                break

            step = steps[step_index]
            attempt = stm.retry_count(step.step_id) + 1
            logger.info("step_start", f"Executing step {step.step_id}", step_id=step.step_id, attempt=attempt, tool=step.tool_name)

            # Improve summarize input with current observations.
            if step.tool_name == "summarize" and step.tool_args.get("text") == "Summarize run observations":
                obs_blob = json.dumps(stm.observations or [stm.state], default=str)
                step.tool_args["text"] = obs_blob

            step_attempt_id = new_step_attempt_id()
            tool_ctx = ToolExecutionContext(
                trace_id=trace.trace_id,
                run_id=trace.run_id,
                step_id=step.step_id,
                attempt=attempt,
                config=run_ctx.config,
                logger=logger,
                short_term_memory=stm,
                long_term_memory=run_ctx.long_term_memory,
                metrics=metrics,
            )

            started = time.perf_counter()
            result_payload: dict[str, Any] | None = None
            error_text: str | None = None
            raw_response: Any = None
            status = ToolCallStatus.SUCCESS
            validated_args_model = None

            try:
                validated_args_model = run_ctx.registry.validate_args(step.tool_name, step.tool_args)
                result_model = run_ctx.registry.get(step.tool_name).handler(validated_args_model, tool_ctx)
                result_payload = result_model.model_dump()
                raw_response = result_payload
            except PolicyViolationError as exc:
                status = ToolCallStatus.POLICY_BLOCKED
                error_text = str(exc)
                raw_response = {"diagnostics": getattr(exc, "diagnostics", {})}
            except ToolExecutionError as exc:
                if exc.failure_type == FailureType.TIMEOUT:
                    status = ToolCallStatus.TIMEOUT
                elif exc.failure_type == FailureType.SCHEMA_ERROR:
                    status = ToolCallStatus.SCHEMA_ERROR
                elif exc.failure_type == FailureType.POLICY_VIOLATION:
                    status = ToolCallStatus.POLICY_BLOCKED
                else:
                    status = ToolCallStatus.ERROR
                error_text = str(exc)
                raw_response = {"diagnostics": getattr(exc, "diagnostics", {})}
            except Exception as exc:  # pragma: no cover - defensive fallback
                status = ToolCallStatus.ERROR
                error_text = f"unexpected error: {exc}"
                raw_response = {"exception_type": type(exc).__name__}

            latency_ms = int((time.perf_counter() - started) * 1000)
            cost_units += plan.budget_guard.cost_per_step
            metrics.inc("tool_calls_total", labels={"tool": step.tool_name, "status": status.value})

            tool_call_record = ToolCallRecord(
                step_id=step.step_id,
                step_attempt_id=step_attempt_id,
                tool_name=step.tool_name,
                tool_args=dict(step.tool_args),
                validated_args=validated_args_model.model_dump() if validated_args_model is not None else {},
                status=status,
                latency_ms=latency_ms,
                result=result_payload,
                error=error_text,
                raw_response=raw_response,
            )
            trace.tool_calls.append(tool_call_record)
            run_ctx.long_term_memory.save_tool_outcome(
                trace_id=trace.trace_id,
                step_id=step.step_id,
                tool_name=step.tool_name,
                status=status.value,
                latency_ms=latency_ms,
                outcome=result_payload or {"error": error_text},
            )

            if status == ToolCallStatus.SUCCESS and result_payload is not None:
                observation = {
                    "tool_name": step.tool_name,
                    "objective": step.objective,
                    "result": result_payload,
                }
                stm.record_observation(step.step_id, observation)
                self._update_state_for_success(stm, step.tool_name, result_payload)
                final_output = self._build_final_output(stm)
                trace.step_events.append(
                    StepEvent(
                        step_id=step.step_id,
                        attempt=attempt,
                        status=StepStatus.SUCCESS,
                        message=f"Step {step.step_id} succeeded",
                        observation=observation,
                    )
                )
                completed_steps += 1
                step_index += 1
                continue

            signals = run_ctx.monitors.evaluate_tool_call(tool_call_record)
            if not signals:
                signals = [
                    FailureSignal(
                        failure_type=FailureType.UNKNOWN,
                        retryable=False,
                        message="Unknown failure",
                        recommended_action="abort",
                    )
                ]

            signature = stm.step_signature(step.tool_name, step.tool_args)
            non_progress_signal = run_ctx.monitors.detect_non_progress(
                signature_count=stm.signature_count(signature),
                threshold=run_ctx.config.non_progress_threshold,
                tool_name=step.tool_name,
                step_id=step.step_id,
            )
            if non_progress_signal:
                signals.insert(0, non_progress_signal)

            trace.monitor_signals.extend(signals)
            failure_signal = signals[0]

            if failure_signal.failure_type == FailureType.NON_PROGRESS:
                metrics.inc("stop_rule_triggers_total", labels={"rule": "non_progress"})
                trace.step_events.append(
                    StepEvent(
                        step_id=step.step_id,
                        attempt=attempt,
                        status=StepStatus.FAILED,
                        message="Stopping due to non-progress",
                        failure_signal=failure_signal,
                    )
                )
                trace.status = RunStatus.STOPPED
                trace.stop_reason = StopReason(type=StopReasonType.NON_PROGRESS, message=failure_signal.message)
                break

            if attempt >= plan.max_retries_per_step and failure_signal.retryable:
                metrics.inc("stop_rule_triggers_total", labels={"rule": "max_retries"})
                trace.step_events.append(
                    StepEvent(
                        step_id=step.step_id,
                        attempt=attempt,
                        status=StepStatus.FAILED,
                        message="Max retries reached",
                        failure_signal=failure_signal,
                    )
                )
                trace.status = RunStatus.STOPPED
                trace.stop_reason = StopReason(type=StopReasonType.MAX_RETRIES, message="max_retries_per_step reached")
                break

            decision = run_ctx.refinement.decide(
                step=step,
                failure_signal=failure_signal,
                attempt=attempt,
                max_retries_per_step=plan.max_retries_per_step,
                perception=perception,
                tool_catalog=run_ctx.registry.catalog(),
                planner=run_ctx.planner,
                remaining_steps=steps[step_index:],
                scratchpad={"failure_context": failure_signal.model_dump()},
            )
            metrics.inc("refinement_actions_total", labels={"action": decision.action.value})
            stm.record_refinement(
                {
                    "step_id": step.step_id,
                    "attempt": attempt,
                    "failure_signal": failure_signal.model_dump(),
                    "decision": decision.model_dump(),
                }
            )
            trace.refinements.append(decision)
            trace.step_events.append(
                StepEvent(
                    step_id=step.step_id,
                    attempt=attempt,
                    status=StepStatus.FAILED,
                    message=f"Step {step.step_id} failed and refinement decided {decision.action.value}",
                    failure_signal=failure_signal,
                    refinement_decision=decision,
                )
            )

            if decision.action == RefinementActionType.PATCH_AND_RETRY:
                trace.status = RunStatus.REFINING
                if decision.patched_args:
                    step.tool_args.update(decision.patched_args)
                stm.mark_retry(step.step_id)
                continue

            if decision.action == RefinementActionType.REPLAN_REMAINING:
                trace.status = RunStatus.REFINING
                if decision.replanned_steps:
                    steps = steps[:step_index] + [PlanStep.model_validate(s.model_dump()) for s in decision.replanned_steps]
                    # Avoid immediate retry counter carryover for new plan step IDs, but preserve if same ID.
                    continue
                trace.status = RunStatus.FAILED
                trace.stop_reason = StopReason(type=StopReasonType.FAILED, message="Replan requested but no steps returned")
                break

            if decision.action == RefinementActionType.SKIP_STEP:
                trace.step_events.append(
                    StepEvent(
                        step_id=step.step_id,
                        attempt=attempt,
                        status=StepStatus.SKIPPED,
                        message=f"Skipped step {step.step_id} after failure",
                    )
                )
                step_index += 1
                continue

            # Abort
            if failure_signal.failure_type == FailureType.POLICY_VIOLATION:
                trace.status = RunStatus.STOPPED
                trace.stop_reason = StopReason(type=StopReasonType.POLICY_BLOCKED, message=failure_signal.message)
            else:
                trace.status = RunStatus.FAILED
                trace.stop_reason = StopReason(type=StopReasonType.FAILED, message=failure_signal.message)
            break

        if trace.status == RunStatus.EXECUTING:
            # Completed all steps normally.
            final_output = self._build_final_output(stm)
            if self._success_criteria_met(perception.success_criteria, stm):
                trace.status = RunStatus.COMPLETED
                trace.stop_reason = StopReason(type=StopReasonType.SUCCESS_CRITERIA_MET, message="Success criteria met")
            else:
                trace.status = RunStatus.COMPLETED
                trace.stop_reason = StopReason(type=StopReasonType.NONE, message="Plan exhausted")

        if trace.status == RunStatus.REFINING:
            # Defensive fallback if loop exits unexpectedly while refining.
            trace.status = RunStatus.FAILED
            trace.stop_reason = StopReason(type=StopReasonType.FAILED, message="Unexpected executor termination")

        final_output = self._build_final_output(stm)
        trace.final_output = final_output
        trace.metrics_snapshot = metrics.snapshot()
        trace.finished_at = utc_now_iso()
        metrics.inc(
            "runs_completed_total" if trace.status == RunStatus.COMPLETED else "runs_failed_total",
            labels={"status": trace.status.value},
        )
        return ExecutionResult(
            status=trace.status,
            final_output=trace.final_output,
            stop_reason=trace.stop_reason,
            completed_steps=completed_steps,
        )

    def _build_final_output(self, stm: Any) -> dict[str, Any]:
        return {
            "message": "Execution finished",
            "state": dict(stm.state),
            "step_outputs": dict(stm.step_outputs),
            "observations": list(stm.observations),
            "criteria_progress": dict(stm.criteria_progress),
        }

    def _update_state_for_success(self, stm: Any, tool_name: str, result_payload: dict[str, Any]) -> None:
        stm.state["last_tool"] = tool_name
        stm.state["last_result"] = result_payload
        if tool_name in {"http_get", "http_post"}:
            stm.state["http result captured"] = True
        elif tool_name == "db_query":
            stm.state["db result captured"] = True
        elif tool_name == "calc":
            stm.state["calculation result available"] = True
        elif tool_name == "file_write":
            stm.state["file write acknowledged"] = True
        elif tool_name == "summarize":
            stm.state["summary produced"] = True

    def _success_criteria_met(self, criteria: list[str], stm: Any) -> bool:
        if not criteria:
            return False
        for criterion in criteria:
            key = criterion.strip()
            if key in stm.state and bool(stm.state[key]):
                stm.criteria_progress[key] = True
                continue
            # Fallback textual check against state/outputs.
            blob = json.dumps({"state": stm.state, "step_outputs": stm.step_outputs}, sort_keys=True, default=str).lower()
            matched = key.lower() in blob
            stm.criteria_progress[key] = matched
            if not matched:
                return False
        return True
