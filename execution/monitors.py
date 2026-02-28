from __future__ import annotations

from typing import Any

from core.types import FailureSignal, FailureType, Severity, ToolCallRecord, ToolCallStatus


class Monitors:
    def evaluate_tool_call(self, record: ToolCallRecord) -> list[FailureSignal]:
        signals: list[FailureSignal] = []
        if record.status == ToolCallStatus.SUCCESS:
            if isinstance(record.result, dict) and record.result.get("malformed"):
                signals.append(
                    FailureSignal(
                        failure_type=FailureType.SCHEMA_ERROR,
                        retryable=True,
                        severity=Severity.MEDIUM,
                        message="Tool returned malformed response",
                        recommended_action="replan_or_patch",
                        diagnostics={"tool_name": record.tool_name},
                    )
                )
            return signals

        if record.status == ToolCallStatus.TIMEOUT:
            signals.append(
                FailureSignal(
                    failure_type=FailureType.TIMEOUT,
                    retryable=True,
                    severity=Severity.MEDIUM,
                    message=record.error or "Tool timeout",
                    recommended_action="increase_timeout_and_retry",
                    diagnostics={"tool_name": record.tool_name},
                )
            )
        elif record.status == ToolCallStatus.SCHEMA_ERROR:
            signals.append(
                FailureSignal(
                    failure_type=FailureType.SCHEMA_ERROR,
                    retryable=True,
                    severity=Severity.MEDIUM,
                    message=record.error or "Schema error",
                    recommended_action="replan_or_adjust_expectations",
                    diagnostics={"tool_name": record.tool_name},
                )
            )
        elif record.status == ToolCallStatus.POLICY_BLOCKED:
            signals.append(
                FailureSignal(
                    failure_type=FailureType.POLICY_VIOLATION,
                    retryable=False,
                    severity=Severity.HIGH,
                    message=record.error or "Policy violation",
                    recommended_action="abort",
                    diagnostics={"tool_name": record.tool_name},
                )
            )
        else:
            signals.append(
                FailureSignal(
                    failure_type=FailureType.TOOL_ERROR,
                    retryable=True,
                    severity=Severity.MEDIUM,
                    message=record.error or "Tool error",
                    recommended_action="retry_or_replan",
                    diagnostics={"tool_name": record.tool_name},
                )
            )
        return signals

    def detect_non_progress(self, signature_count: int, threshold: int, tool_name: str, step_id: str) -> FailureSignal | None:
        if signature_count > threshold:
            return FailureSignal(
                failure_type=FailureType.NON_PROGRESS,
                retryable=False,
                severity=Severity.HIGH,
                message="Repeated identical failing tool call detected",
                recommended_action="abort",
                diagnostics={"tool_name": tool_name, "step_id": step_id, "signature_count": signature_count},
            )
        return None

