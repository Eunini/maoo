from __future__ import annotations

import pytest


def test_tool_registry_registers_required_tools(registry):
    names = {t.name for t in registry.catalog()}
    assert names == {"http_get", "http_post", "db_query", "file_write", "calc", "summarize"}


def test_calc_schema_rejects_non_string_expression(registry):
    with pytest.raises(Exception):
        registry.validate_args("calc", {"expression": {"bad": "shape"}})

