from __future__ import annotations

from llm.heuristic_provider import HeuristicProvider
from perception.agent import PerceptionAgent


def test_perception_pipeline_extracts_structured_fields(test_config, long_term_memory):
    agent = PerceptionAgent(HeuristicProvider(test_config), long_term_memory=long_term_memory)
    result = agent.run("Fetch flaky endpoint and summarize result")
    assert result.intent
    assert result.task_type.value in {"data_retrieval", "composite"}
    assert "raw_goal" in result.entities
    assert isinstance(result.constraints, list)
    assert isinstance(result.success_criteria, list)

