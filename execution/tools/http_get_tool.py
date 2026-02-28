from __future__ import annotations

from typing import Any

import httpx

from core.exceptions import ToolExecutionError
from core.types import FailureType
from execution.tool_schemas import HTTPGetArgs, HTTPResult


def http_get_tool(args: HTTPGetArgs, ctx: Any) -> HTTPResult:
    timeout = float(args.timeout_s or getattr(ctx.config, "default_http_timeout_s", 2.0))
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(args.url, params=args.params or None, headers=args.headers or None)
    except httpx.TimeoutException as exc:
        raise ToolExecutionError(
            f"http_get timeout for {args.url}",
            failure_type=FailureType.TIMEOUT,
            diagnostics={"url": args.url, "timeout_s": timeout},
        ) from exc
    except httpx.HTTPError as exc:
        raise ToolExecutionError(
            f"http_get transport error for {args.url}: {exc}",
            failure_type=FailureType.TOOL_ERROR,
            diagnostics={"url": args.url},
        ) from exc

    headers = {k.lower(): v for k, v in resp.headers.items()}
    body: Any
    malformed = False
    if args.expect_json:
        try:
            body = resp.json()
        except Exception as exc:
            if args.allow_malformed:
                body = resp.text
                malformed = True
            else:
                raise ToolExecutionError(
                    f"http_get expected JSON but got malformed body from {args.url}",
                    failure_type=FailureType.SCHEMA_ERROR,
                    diagnostics={"url": args.url, "status_code": resp.status_code},
                ) from exc
    else:
        body = resp.text

    if resp.status_code >= 500:
        raise ToolExecutionError(
            f"http_get server error status={resp.status_code}",
            failure_type=FailureType.TOOL_ERROR,
            diagnostics={"url": args.url, "status_code": resp.status_code, "body": body if isinstance(body, dict) else str(body)[:200]},
        )

    return HTTPResult(
        ok=True,
        message="http_get completed",
        data={"url": args.url},
        status_code=resp.status_code,
        headers=headers,
        body=body,
        malformed=malformed,
    )

