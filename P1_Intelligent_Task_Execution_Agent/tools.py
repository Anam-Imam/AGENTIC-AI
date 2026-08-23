import ast
import json
import math
from datetime import datetime

from langchain.tools import tool

@tool
def calculator(expression: str) -> str:
    """Safely calculate a mathematical expression. Supports numbers, +, -, *, /, %, **, parentheses, and common math functions."""
    allowed_names = {
        "abs": abs,
        "round": round,
        "sqrt": math.sqrt,
        "ceil": math.ceil,
        "floor": math.floor,
        "pi": math.pi,
        "e": math.e,
    }

    tree = ast.parse(expression, mode="eval")

    allowed_nodes = (
        ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd, ast.Call, ast.Name, ast.Load,
    )

    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError("Unsupported expression.")
        if isinstance(node, ast.Name) and node.id not in allowed_names:
            raise ValueError(f"Unknown function or name: {node.id}")
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name) or node.func.id not in allowed_names
        ):
            raise ValueError("Unsupported function.")

    value = eval(compile(tree, "<calculator>", "eval"), {"__builtins__": {}}, allowed_names)
    return str(value)

@tool
def current_time(location: str = "local") -> str:
    """Return the current local server time. The location label is informational only."""
    now = datetime.now().astimezone()
    return json.dumps({
        "location": location,
        "time": now.isoformat(),
        "formatted": now.strftime("%A, %d %B %Y at %I:%M %p"),
    })

@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the public web for current information. Use this when the user asks for recent facts, sources, or research."""
    try:
        from ddgs import DDGS
    except ImportError:
        return json.dumps({
            "error": "Web search dependency is not installed. Install the ddgs package.",
            "sources": []
        })

    results = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=max_results):
            results.append({
                "title": item.get("title", "Untitled"),
                "url": item.get("href", ""),
                "snippet": item.get("body", ""),
            })

    return json.dumps({"query": query, "sources": results}, ensure_ascii=False)

TOOLS = [calculator, current_time, web_search]
