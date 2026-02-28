from __future__ import annotations

from typing import Any

from core.config import Config
from core.types import BudgetGuard, PerceptionResult, Plan, PlanStep, ToolCatalogEntry
from memory.long_term import LongTermMemory
from memory.retrieval import retrieve_memory


class PlannerAgent:
    def __init__(self, config: Config, long_term_memory: LongTermMemory | None = None) -> None:
        self.config = config
        self.long_term_memory = long_term_memory

    def build_plan(
        self,
        perception: PerceptionResult,
        tool_catalog: list[ToolCatalogEntry],
        scratchpad: dict[str, Any] | None = None,
    ) -> Plan:
        scratchpad = scratchpad or {}
        raw_goal = str(perception.entities.get("raw_goal", ""))
        lower = raw_goal.lower()
        steps: list[PlanStep] = []
        notes: list[str] = []
        tool_names = {t.name for t in tool_catalog}

        if self.long_term_memory:
            recalled = retrieve_memory(self.long_term_memory, "facts", raw_goal, limit=2)
            if recalled:
                notes.append(f"Retrieved {len(recalled)} prior memory entries")

        failure_context = scratchpad.get("failure_context") or {}
        if failure_context:
            notes.append(f"Replanning after {failure_context.get('failure_type')} on {failure_context.get('step_id')}")

        if perception.entities.get("force_invalid_tool"):
            return self._plan_with(
                [
                    PlanStep(
                        step_id="s1",
                        objective="Intentional invalid tool for eval",
                        tool_name="non_existent_tool",
                        tool_args={},
                        expected_observation="validator blocks",
                        fallback_strategy="abort",
                    )
                ],
                notes,
            )
        if perception.entities.get("force_invalid_args"):
            return self._plan_with(
                [
                    PlanStep(
                        step_id="s1",
                        objective="Intentional invalid args for eval",
                        tool_name="calc",
                        tool_args={"expression": {"bad": "shape"}},
                        expected_observation="validator blocks",
                        fallback_strategy="abort",
                    )
                ],
                notes,
            )

        def next_step_id() -> str:
            return f"s{len(steps)+1}"

        def mock_url_for(lower_text: str) -> str:
            base = self.config.mock_api_base_url.rstrip("/")
            if "flaky" in lower_text:
                return f"{base}/flaky?fail_first=1&key=demo"
            if "slow" in lower_text:
                return f"{base}/slow?delay_ms=1500"
            if "malformed" in lower_text:
                return f"{base}/malformed?kind=json_text"
            if "post" in lower_text or "submit" in lower_text:
                return f"{base}/submit"
            return f"{base}/data"

        http_url = perception.entities.get("url") or perception.entities.get("external_url")
        if not http_url and any(t in lower for t in ["fetch", "get", "post", "submit", "flaky", "slow", "malformed"]):
            http_url = mock_url_for(lower)

        if "post" in lower or "submit" in lower:
            if "http_post" in tool_names:
                steps.append(
                    PlanStep(
                        step_id=next_step_id(),
                        objective="Submit data to API",
                        tool_name="http_post",
                        tool_args={
                            "url": http_url or mock_url_for("submit"),
                            "json_body": {"message": "hello from maoo"},
                            "timeout_s": self.config.default_http_timeout_s,
                            "expect_json": True,
                        },
                        expected_observation="submission response captured",
                        fallback_strategy="retry_with_backoff",
                    )
                )

        if http_url and "http_get" in tool_names and not ("/submit" in str(http_url) and ("post" in lower or "submit" in lower)):
            fallback = "replan_to_alternate_endpoint" if "malformed" in lower else "retry_with_backoff"
            args = {"url": http_url, "timeout_s": self.config.default_http_timeout_s, "expect_json": True}
            if "malformed" in lower:
                args["allow_malformed"] = False
            steps.append(
                PlanStep(
                    step_id=next_step_id(),
                    objective="Fetch data from API",
                    tool_name="http_get",
                    tool_args=args,
                    expected_observation="response body captured",
                    fallback_strategy=fallback,
                )
            )

        if perception.entities.get("db_requested") or any(t in lower for t in ["db", "database", "sql"]):
            sql = "SELECT id, label, value FROM demo_numbers ORDER BY id LIMIT 3"
            if perception.entities.get("unsafe_sql"):
                sql = "DELETE FROM demo_numbers WHERE id = 1"
            steps.append(
                PlanStep(
                    step_id=next_step_id(),
                    objective="Run sqlite query",
                    tool_name="db_query",
                    tool_args={"sql": sql, "readonly": True, "limit": 10},
                    expected_observation="rows returned",
                    fallback_strategy="abort_on_policy_violation",
                )
            )

        if perception.entities.get("calc_requested") or any(t in lower for t in ["calc", "calculate"]):
            expr = perception.entities.get("expression", "2 + 2")
            if perception.entities.get("unsafe_calc"):
                expr = "__import__('os').system('bad')"
            steps.append(
                PlanStep(
                    step_id=next_step_id(),
                    objective="Evaluate arithmetic",
                    tool_name="calc",
                    tool_args={"expression": expr},
                    expected_observation="numeric result",
                    fallback_strategy="abort_on_invalid_expression",
                )
            )

        if perception.entities.get("write_requested") or any(t in lower for t in ["write", "save"]):
            rel_path = "../escape.txt" if perception.entities.get("unsafe_path") else "reports/output.txt"
            steps.append(
                PlanStep(
                    step_id=next_step_id(),
                    objective="Write output to sandbox file",
                    tool_name="file_write",
                    tool_args={"relative_path": rel_path, "content": "MAOO output placeholder", "overwrite": True},
                    expected_observation="file write acknowledged",
                    fallback_strategy="abort_on_policy_violation",
                )
            )

        if perception.entities.get("summarize_requested") or "summary" in lower or "summarize" in lower or not steps:
            steps.append(
                PlanStep(
                    step_id=next_step_id(),
                    objective="Summarize observations",
                    tool_name="summarize",
                    tool_args={"text": "Summarize run observations", "max_sentences": 3, "style": "brief"},
                    expected_observation="summary text",
                    fallback_strategy="deterministic_fallback",
                )
            )

        if perception.entities.get("force_long_plan"):
            for i in range(10):
                steps.append(
                    PlanStep(
                        step_id=next_step_id(),
                        objective=f"Long-plan calc step {i+1}",
                        tool_name="calc",
                        tool_args={"expression": "1 + 1"},
                        expected_observation="numeric result",
                        fallback_strategy="abort",
                    )
                )

        if perception.entities.get("force_extra_steps_after_success"):
            steps.append(
                PlanStep(
                    step_id=next_step_id(),
                    objective="Extra summary after likely success",
                    tool_name="summarize",
                    tool_args={"text": "Extra step", "max_sentences": 1, "style": "brief"},
                    expected_observation="summary text",
                    fallback_strategy="skip_if_success_already_met",
                )
            )

        if failure_context.get("failure_type") in {"schema_error", "bad_response"}:
            for step in steps:
                if step.tool_name == "http_get" and "/malformed" in str(step.tool_args.get("url", "")):
                    step.tool_args["url"] = self.config.mock_api_base_url.rstrip("/") + "/data"
                    notes.append("Replanned malformed endpoint to /data")
        if failure_context.get("failure_type") == "timeout":
            for step in steps:
                if step.tool_name in {"http_get", "http_post"}:
                    step.tool_args["timeout_s"] = max(float(step.tool_args.get("timeout_s", 2.0)), 3.5)
                    notes.append("Increased timeout during replan")
        return self._plan_with(steps, notes)

    def replan_remaining(
        self,
        perception: PerceptionResult,
        remaining_steps: list[PlanStep],
        tool_catalog: list[ToolCatalogEntry],
        scratchpad: dict[str, Any] | None = None,
    ) -> list[PlanStep]:
        scratchpad = scratchpad or {}
        new_plan = self.build_plan(perception, tool_catalog, scratchpad=scratchpad)
        return new_plan.steps if new_plan.steps else remaining_steps

    def _plan_with(self, steps: list[PlanStep], notes: list[str]) -> Plan:
        return Plan(
            steps=steps,
            max_steps=self.config.default_max_steps,
            max_retries_per_step=self.config.default_max_retries_per_step,
            budget_guard=BudgetGuard(max_cost_units=self.config.default_budget_units),
            planner_notes=notes,
        )

