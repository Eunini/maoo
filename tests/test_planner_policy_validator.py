from __future__ import annotations

import pytest

from core.exceptions import PlanValidationError
from llm.heuristic_provider import HeuristicProvider
from perception.agent import PerceptionAgent
from planning.plan_validator import validate_plan
from planning.planner import PlannerAgent
from planning.policy import PolicyEngine


def test_planner_generates_valid_plan_for_happy_request(test_config, long_term_memory, registry):
    perception = PerceptionAgent(HeuristicProvider(test_config), long_term_memory).run("Fetch mock data and summarize")
    planner = PlannerAgent(test_config, long_term_memory)
    plan = planner.build_plan(perception, registry.catalog())
    validated = validate_plan(plan, registry, PolicyEngine(test_config))
    assert validated.plan.steps


def test_policy_blocks_external_http_host(test_config, long_term_memory, registry):
    perception = PerceptionAgent(HeuristicProvider(test_config), long_term_memory).run("Fetch http://example.com")
    planner = PlannerAgent(test_config, long_term_memory)
    plan = planner.build_plan(perception, registry.catalog())
    with pytest.raises(PlanValidationError):
        validate_plan(plan, registry, PolicyEngine(test_config))
