from __future__ import annotations

from fastapi.testclient import TestClient
import importlib
import pytest

from core.exceptions import ToolExecutionError
from core.types import ToolExecutionContext
from execution.tool_schemas import HTTPGetArgs, HTTPPostArgs
from execution.tools.http_get_tool import http_get_tool
from execution.tools.http_post_tool import http_post_tool
from mock_api.server import create_app


class _PatchedHTTPXClient:
    def __init__(self, test_client: TestClient, *args, **kwargs) -> None:
        self.test_client = test_client

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def _strip(self, url: str) -> str:
        if "://" in url:
            idx = url.find("/", url.find("://") + 3)
            return url[idx:] if idx != -1 else "/"
        return url

    def get(self, url, params=None, headers=None):
        return self.test_client.get(self._strip(url), params=params, headers=headers)

    def post(self, url, json=None, headers=None):
        return self.test_client.post(self._strip(url), json=json, headers=headers)


def _ctx(test_config):
    return ToolExecutionContext(
        trace_id="t",
        run_id="r",
        step_id="s1",
        attempt=1,
        config=test_config,
        logger=None,
        short_term_memory=None,
        long_term_memory=None,
        metrics=None,
    )


def test_http_tools_with_mock_api_routes(monkeypatch, test_config):
    client = TestClient(create_app())

    http_get_mod = importlib.import_module("execution.tools.http_get_tool")
    http_post_mod = importlib.import_module("execution.tools.http_post_tool")

    monkeypatch.setattr(http_get_mod.httpx, "Client", lambda *a, **k: _PatchedHTTPXClient(client))
    monkeypatch.setattr(http_post_mod.httpx, "Client", lambda *a, **k: _PatchedHTTPXClient(client))

    get_res = http_get_tool(HTTPGetArgs(url="http://127.0.0.1:8001/data"), _ctx(test_config))
    assert get_res.ok is True
    assert get_res.body["sum"] == 14

    post_res = http_post_tool(HTTPPostArgs(url="http://127.0.0.1:8001/submit", json_body={"message": "hi"}), _ctx(test_config))
    assert post_res.ok is True
    assert post_res.body["accepted"] is True

    with pytest.raises(ToolExecutionError):
        http_get_tool(HTTPGetArgs(url="http://127.0.0.1:8001/malformed?kind=json_text", expect_json=True), _ctx(test_config))
