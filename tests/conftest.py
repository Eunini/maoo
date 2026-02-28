from __future__ import annotations

from pathlib import Path
import uuid

import pytest

from core.config import load_config
from core.logger import get_logger
from core.metrics import MetricsRegistry
from core.tracing import new_run_id, new_trace_id
from core.types import RunContext, RunTrace
from execution.monitors import Monitors
from execution.refinement import RefinementEngine
from execution.tool_registry import ToolRegistry
from memory.long_term import LongTermMemory
from memory.short_term import ShortTermMemory
from planning.planner import PlannerAgent
from planning.policy import PolicyEngine


@pytest.fixture()
def test_config():
    runtime = Path("runtime")
    unique_db = runtime / "sqlite" / f"test_{uuid.uuid4().hex}.db"
    cfg = load_config(
        {
            "runtime_dir": runtime,
            "logs_dir": runtime / "logs",
            "traces_dir": runtime / "traces",
            "workspace_dir": runtime / "workspace",
            "sqlite_dir": runtime / "sqlite",
            "sqlite_path": unique_db,
            "file_workspace_root": runtime / "workspace",
            "mock_api_base_url": "http://127.0.0.1:8001",
            "no_llm_mode": True,
            "log_to_file": False,
        }
    )
    return cfg


@pytest.fixture()
def long_term_memory(test_config):
    return LongTermMemory(
        test_config.sqlite_path,
        schema_path=Path("sql/schema.sql"),
        seed_path=Path("sql/seed_data.sql"),
    )


@pytest.fixture()
def registry():
    r = ToolRegistry()
    r.register_defaults()
    return r


@pytest.fixture()
def run_trace():
    return RunTrace(trace_id=new_trace_id(), run_id=new_run_id(), request={"raw_goal": "test", "context": {}})


def make_run_context(test_config, long_term_memory, registry, run_trace, planner=None):
    planner = planner or PlannerAgent(test_config, long_term_memory=long_term_memory)
    return RunContext(
        config=test_config,
        logger=get_logger(test_config, component="test", trace_id=run_trace.trace_id, run_id=run_trace.run_id),
        metrics=MetricsRegistry(),
        trace=run_trace,
        registry=registry,
        policy=PolicyEngine(test_config),
        short_term_memory=ShortTermMemory({}),
        long_term_memory=long_term_memory,
        planner=planner,
        monitors=Monitors(),
        refinement=RefinementEngine(),
    )


@pytest.fixture()
def run_context_factory(test_config, long_term_memory, registry):
    def _factory(run_trace, planner=None):
        return make_run_context(test_config, long_term_memory, registry, run_trace, planner=planner)

    return _factory
