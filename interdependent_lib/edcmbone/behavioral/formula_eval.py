"""Safe evaluator for canon-resident behavioral formulas."""
from __future__ import annotations

import ast
import operator as op
from typing import Any, Mapping

_BINOPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}
_UNARYOPS = {ast.UAdd: op.pos, ast.USub: op.neg, ast.Not: op.not_}
_CMPOPS = {
    ast.Lt: op.lt,
    ast.LtE: op.le,
    ast.Gt: op.gt,
    ast.GtE: op.ge,
    ast.Eq: op.eq,
    ast.NotEq: op.ne,
}
_FUNCS = {"min": min, "max": max, "abs": abs, "sum": sum, "len": len}


def evaluate(expression: str, variables: Mapping[str, Any]) -> Any:
    """Evaluate a restricted arithmetic formula against explicit bindings.

    The evaluator accepts only literal numeric/bool constants, named variables,
    arithmetic, comparisons, boolean operations, and direct calls to a small
    whitelist of pure builtins. It rejects attributes, imports, lambdas,
    comprehensions, indexing, assignment, and any other AST node by default.
    """
    return _walk(ast.parse(expression, mode="eval").body, variables)


def _walk(node: ast.AST, env: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool)):
            return node.value
        raise ValueError(f"non-numeric constant: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise NameError(f"unknown variable: {node.id}")
    if isinstance(node, ast.BinOp):
        fn = _BINOPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"forbidden binop: {type(node.op).__name__}")
        return fn(_walk(node.left, env), _walk(node.right, env))
    if isinstance(node, ast.UnaryOp):
        fn = _UNARYOPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"forbidden unaryop: {type(node.op).__name__}")
        return fn(_walk(node.operand, env))
    if isinstance(node, ast.Compare):
        left = _walk(node.left, env)
        for op_node, right_node in zip(node.ops, node.comparators):
            fn = _CMPOPS.get(type(op_node))
            if fn is None:
                raise ValueError(f"forbidden cmpop: {type(op_node).__name__}")
            right = _walk(right_node, env)
            if not fn(left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        vals = [_walk(v, env) for v in node.values]
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("only direct function calls allowed")
        if node.func.id not in _FUNCS:
            raise NameError(f"unknown function: {node.func.id}")
        return _FUNCS[node.func.id](*[_walk(a, env) for a in node.args])
    raise ValueError(f"forbidden node type: {type(node).__name__}")


__all__ = ["evaluate"]
