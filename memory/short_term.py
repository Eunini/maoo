from __future__ import annotations

import hashlib
import json
from typing import Any


class ShortTermMemory:
    def __init__(self, initial_state: dict[str, Any] | None = None) -> None:
        self.state: dict[str, Any] = dict(initial_state or {})
        self.step_outputs: dict[str, Any] = {}
        self.observations: list[dict[str, Any]] = []
        self.retries: dict[str, int] = {}
        self.refinements: list[dict[str, Any]] = []
        self.criteria_progress: dict[str, bool] = {}
        self.seen_step_signatures: dict[str, int] = {}

    def record_observation(self, step_id: str, observation: dict[str, Any]) -> None:
        self.observations.append({"step_id": step_id, **observation})
        self.step_outputs[step_id] = observation
        self.state["last_observation"] = observation
        self.state["last_step_id"] = step_id

    def mark_retry(self, step_id: str) -> int:
        self.retries[step_id] = self.retries.get(step_id, 0) + 1
        return self.retries[step_id]

    def retry_count(self, step_id: str) -> int:
        return self.retries.get(step_id, 0)

    def record_refinement(self, payload: dict[str, Any]) -> None:
        self.refinements.append(payload)
        self.state["last_refinement"] = payload

    def mark_criteria(self, criteria: list[str], final_output: dict[str, Any]) -> dict[str, bool]:
        blob = json.dumps(final_output, sort_keys=True, default=str).lower()
        for c in criteria:
            self.criteria_progress[c] = c.lower() in blob
        return dict(self.criteria_progress)

    def step_signature(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        key = json.dumps({"tool_name": tool_name, "tool_args": tool_args}, sort_keys=True, default=str)
        sig = hashlib.sha1(key.encode("utf-8")).hexdigest()
        self.seen_step_signatures[sig] = self.seen_step_signatures.get(sig, 0) + 1
        return sig

    def signature_count(self, signature: str) -> int:
        return self.seen_step_signatures.get(signature, 0)

