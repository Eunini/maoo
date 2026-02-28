from __future__ import annotations

from typing import Any

from .types import FailureType


class MAOOError(Exception):
    pass


class PolicyViolationError(MAOOError):
    def __init__(self, message: str, diagnostics: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.failure_type = FailureType.POLICY_VIOLATION
        self.diagnostics = diagnostics or {}


class ToolExecutionError(MAOOError):
    def __init__(self, message: str, failure_type: FailureType = FailureType.TOOL_ERROR, diagnostics: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.failure_type = failure_type
        self.diagnostics = diagnostics or {}


class PlanValidationError(MAOOError):
    def __init__(self, message: str, diagnostics: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.failure_type = FailureType.VALIDATION_ERROR
        self.diagnostics = diagnostics or {}


class StopConditionTriggered(MAOOError):
    def __init__(self, message: str, reason: str) -> None:
        super().__init__(message)
        self.reason = reason

