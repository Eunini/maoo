from __future__ import annotations

import ast
import operator
from typing import Any

from core.exceptions import ToolExecutionError
from core.types import FailureType
from execution.tool_schemas import CalcArgs, CalcResult


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval(node.operand))
    raise ToolExecutionError(
        "Unsafe or unsupported calc expression",
        failure_type=FailureType.POLICY_VIOLATION,
        diagnostics={"node": type(node).__name__},
    )


def calc_tool(args: CalcArgs, ctx: Any) -> CalcResult:
    try:
        tree = ast.parse(args.expression, mode="eval")
        result = _eval(tree)
    except ToolExecutionError:
        raise
    except Exception as exc:
        raise ToolExecutionError(
            f"calc failed: {exc}",
            failure_type=FailureType.TOOL_ERROR,
            diagnostics={"expression": args.expression},
        ) from exc
    return CalcResult(
        ok=True,
        message="calc completed",
        data={"expression": args.expression},
        result=result,
    )

