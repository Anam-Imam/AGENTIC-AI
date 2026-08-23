from __future__ import annotations

import ast
import operator
from typing import Any, Callable


_ALLOWED_BINOPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_ALLOWED_UNARY: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return float(_ALLOWED_BINOPS[type(node.op)](left, right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        return float(_ALLOWED_UNARY[type(node.op)](_safe_eval(node.operand)))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    """Safely calculate a basic arithmetic expression."""
    tree = ast.parse(expression, mode="eval")
    value = _safe_eval(tree.body)
    return f"{value:g}"


def text_stats(text: str) -> dict[str, int]:
    """Return basic word, character and sentence counts."""
    words = text.split()
    sentences = sum(text.count(mark) for mark in ".!?" )
    return {
        "words": len(words),
        "characters": len(text),
        "sentences": sentences,
    }


def make_plan(goal: str, steps: list[str]) -> str:
    """Create a compact execution plan from a goal and step list."""
    clean = [step.strip() for step in steps if step.strip()]
    lines = [f"MISSION: {goal.strip()}"]
    lines.extend(f"{idx}. {step}" for idx, step in enumerate(clean, start=1))
    return "\n".join(lines)


TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "calculator": calculator,
    "text_stats": text_stats,
    "make_plan": make_plan,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Safely calculate a basic arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "text_stats",
            "description": "Get word, character and sentence counts for text.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_plan",
            "description": "Turn a goal and a list of steps into an execution plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string"},
                    "steps": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["goal", "steps"],
            },
        },
    },
]
