from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from .faults import flaky_should_fail, slow_sleep
from .models import SubmitPayload
from .state import STATE

router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "mock-api"}


@router.get("/data")
def data() -> dict[str, object]:
    return {
        "ok": True,
        "numbers": [2, 4, 8],
        "message": "mock data",
        "sum": 14,
    }


@router.post("/submit")
def submit(payload: SubmitPayload) -> dict[str, object]:
    count = STATE.bump("submit")
    return {
        "ok": True,
        "accepted": True,
        "count": count,
        "echo": payload.model_dump(),
        "status": "submitted",
    }


@router.get("/flaky")
def flaky(fail_first: int = 1, key: str = "default") -> dict[str, object]:
    if flaky_should_fail(key=key, fail_first=fail_first):
        raise HTTPException(status_code=500, detail={"ok": False, "error": "transient failure"})
    return {"ok": True, "status": "recovered", "key": key, "attempts": STATE.get(f"flaky:{key}")}


@router.get("/slow")
def slow(delay_ms: int = 1500) -> dict[str, object]:
    slow_sleep(delay_ms)
    return {"ok": True, "delay_ms": delay_ms, "status": "slow response completed"}


@router.get("/malformed")
def malformed(kind: str = "json_text") -> Response:
    if kind == "json_text":
        return Response(content="this is not json", media_type="application/json", status_code=200)
    if kind == "truncated":
        return Response(content='{"ok": true', media_type="application/json", status_code=200)
    return Response(content="MALFORMED", media_type="text/plain", status_code=200)


@router.get("/scenario/{scenario_id}")
def scenario_route(scenario_id: str) -> dict[str, object]:
    return {"ok": True, "scenario_id": scenario_id, "message": f"scenario payload for {scenario_id}"}

