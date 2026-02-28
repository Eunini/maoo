from __future__ import annotations

from typing import Any

import httpx

from core.exceptions import ToolExecutionError
from core.types import FailureType
from execution.tool_schemas import HTTPPostArgs, HTTPResult


def http_post_tool(args: HTTPPostArgs, ctx: Any) -> HTTPResult:
    timeout = float(args.timeout_s or getattr(ctx.config, "default_http_timeout_s", 2.0))
    headers = dict(args.headers or {})
    if args.idempotency_key:
        headers.setdefault("Idempotency-Key", args.idempotency_key)
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(args.url, json=args.json_body or {}, headers=headers or None)
    except httpx.TimeoutException as exc:
        raise ToolExecutionError(
            f"http_post timeout for {args.url}",
            failure_type=FailureType.TIMEOUT,
            diagnostics={"url": args.url, "timeout_s": timeout},
        ) from exc
    except httpx.HTTPError as exc:
        raise ToolExecutionError(
            f"http_post transport error for {args.url}: {exc}",
            failure_type=FailureType.TOOL_ERROR,
            diagnostics={"url": args.url},
        ) from exc

    normalized_headers = {k.lower(): v for k, v in resp.headers.items()}
    body: Any
    malformed = False
    if args.expect_json:
        try:
            body = resp.json()
        except Exception as exc:
            raise ToolExecutionError(
                f"http_post expected JSON but got malformed body from {args.url}",
                failure_type=FailureType.SCHEMA_ERROR,
                diagnostics={"url": args.url, "status_code": resp.status_code},
            ) from exc
    else:
        body = resp.text

    if resp.status_code >= 500:
        raise ToolExecutionError(
            f"http_post server error status={resp.status_code}",
            failure_type=FailureType.TOOL_ERROR,
            diagnostics={"url": args.url, "status_code": resp.status_code},
        )

    return HTTPResult(
        ok=True,
        message="http_post completed",
        data={"url": args.url},
        status_code=resp.status_code,
        headers=normalized_headers,
        body=body,
        malformed=malformed,
    )

