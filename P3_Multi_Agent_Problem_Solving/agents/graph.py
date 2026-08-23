from __future__ import annotations

import json
import os
import re
from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.state import AgentState
from core.groq_client import chat
from core.prompts import (
    ANALYSIS_SYSTEM,
    EXECUTION_SYSTEM,
    FINAL_SYSTEM,
    RESEARCH_SYSTEM,
    SUPERVISOR_SYSTEM,
)
from core.tools import TOOL_REGISTRY, TOOL_SCHEMAS


MAX_SECTION = int(os.getenv("AGENT_CONTEXT_CHARS", "6500"))
MAX_FINAL_INPUT = int(os.getenv("FINAL_CONTEXT_CHARS", "17000"))


def _message_text(response: Any) -> str:
    return (response.choices[0].message.content or "").strip()


def _clip(text: str, limit: int = MAX_SECTION) -> str:
    text = str(text or "")
    if len(text) <= limit:
        return text
    head = int(limit * 0.75)
    tail = max(200, limit - head - 60)
    return f"{text[:head]}\n[…clipped for context size…]\n{text[-tail:]}"


def _extract_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)\]]+", text or "")
    seen: list[str] = []
    for url in urls:
        clean = url.rstrip(".,;\"")
        if clean not in seen:
            seen.append(clean)
    return seen[:12]


def _parse_supervisor(text: str) -> tuple[list[str], str]:
    allowed = {"research", "analysis", "execution"}
    cleaned = (text or "").strip()
    candidates = [cleaned]
    if "{" in cleaned and "}" in cleaned:
        candidates.append(cleaned[cleaned.find("{") : cleaned.rfind("}") + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        route = [x for x in parsed.get("agents", []) if x in allowed]
        reason = str(parsed.get("reason", "")).strip()
        if route:
            return list(dict.fromkeys(route)), reason
    return ["research", "analysis", "execution"], "Supervisor output was not valid JSON; full-route fallback used."


def supervisor_node(state: AgentState) -> dict[str, Any]:
    request = _clip(state["user_request"], 5000)
    try:
        response = chat(
            [
                {"role": "system", "content": SUPERVISOR_SYSTEM},
                {"role": "user", "content": request},
            ],
            temperature=0.0,
            max_completion_tokens=180,
        )
        route, reason = _parse_supervisor(_message_text(response))
        return {"route": route, "supervisor_reason": reason}
    except Exception as exc:
        return {
            "route": ["research", "analysis", "execution"],
            "supervisor_reason": "Supervisor API call failed; full-route fallback used.",
            "errors": [str(exc)],
        }


def research_node(state: AgentState) -> dict[str, Any]:
    request = _clip(state["user_request"], 5000)
    research_model = os.getenv("GROQ_RESEARCH_MODEL", "groq/compound")
    try:
        response = chat(
            [
                {"role": "system", "content": RESEARCH_SYSTEM},
                {"role": "user", "content": request},
            ],
            model=research_model,
            temperature=0.15,
            max_completion_tokens=900,
        )
    except Exception as first_error:
        # If the configured compound/research model is unavailable, keep the
        # workflow usable with the standard Groq model.
        try:
            response = chat(
                [
                    {"role": "system", "content": RESEARCH_SYSTEM},
                    {"role": "user", "content": request},
                ],
                temperature=0.15,
                max_completion_tokens=900,
            )
        except Exception as second_error:
            return {
                "research": "Research unavailable.",
                "errors": state.get("errors", []) + [str(first_error), str(second_error)],
            }

    message = response.choices[0].message
    text = _clip(message.content or "")
    sources = [{"label": url, "url": url} for url in _extract_urls(text)]
    return {
        "research": text,
        "sources": sources,
        "observations": state.get("observations", [])
        + ["Research agent completed its information pass."],
    }


def _tool_loop(messages: list[dict[str, Any]], system: str) -> tuple[str, list[str]]:
    safe_messages = [
        {"role": "user", "content": _clip(m.get("content", ""), MAX_SECTION)} for m in messages
    ]
    working = [{"role": "system", "content": system}] + safe_messages
    response = chat(
        working,
        tools=TOOL_SCHEMAS,
        temperature=0.2,
        max_completion_tokens=900,
    )
    tool_notes: list[str] = []

    for _ in range(2):
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None) or []
        if not tool_calls:
            return _clip(message.content or "", MAX_SECTION), tool_notes

        assistant_tool_calls = []
        for call in tool_calls[:4]:
            fn = getattr(call, "function", None)
            if not fn:
                continue
            assistant_tool_calls.append(
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": fn.name,
                        "arguments": _clip(fn.arguments, 5000),
                    },
                }
            )
        working.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": assistant_tool_calls,
            }
        )

        for call in tool_calls[:4]:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            fn = TOOL_REGISTRY.get(name)
            if not fn:
                result = f"Unknown tool: {name}"
            else:
                try:
                    result = fn(**args)
                except Exception as exc:
                    result = f"Tool error: {exc}"
            tool_notes.append(name)
            payload = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            working.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": _clip(payload, 3000),
                }
            )

        response = chat(
            working,
            tools=TOOL_SCHEMAS,
            temperature=0.2,
            max_completion_tokens=900,
        )

    return _clip(response.choices[0].message.content or "", MAX_SECTION), tool_notes


def analysis_node(state: AgentState) -> dict[str, Any]:
    research = _clip(state.get("research", "No research pass was requested."))
    prompt = f"USER REQUEST:\n{_clip(state['user_request'], 5000)}\n\nRESEARCH FINDINGS:\n{research}"
    try:
        text, tools = _tool_loop([{"role": "user", "content": prompt}], ANALYSIS_SYSTEM)
        notes = [f"Analysis agent used tool: {name}" for name in tools]
        if not notes:
            notes = ["Analysis agent completed reasoning pass."]
        return {
            "analysis": text,
            "observations": state.get("observations", []) + notes,
        }
    except Exception as exc:
        return {
            "analysis": "Analysis unavailable.",
            "errors": state.get("errors", []) + [str(exc)],
        }


def execution_node(state: AgentState) -> dict[str, Any]:
    prompt = (
        f"USER REQUEST:\n{_clip(state['user_request'], 5000)}\n\n"
        f"RESEARCH:\n{_clip(state.get('research', ''), MAX_SECTION)}\n\n"
        f"ANALYSIS:\n{_clip(state.get('analysis', ''), MAX_SECTION)}"
    )
    try:
        text, tools = _tool_loop([{"role": "user", "content": prompt}], EXECUTION_SYSTEM)
        notes = [f"Execution agent used tool: {name}" for name in tools]
        if not notes:
            notes = ["Execution agent completed implementation pass."]
        return {
            "execution": text,
            "observations": state.get("observations", []) + notes,
        }
    except Exception as exc:
        return {
            "execution": "Execution unavailable.",
            "errors": state.get("errors", []) + [str(exc)],
        }


def final_node(state: AgentState) -> dict[str, Any]:
    sections = [
        f"USER REQUEST:\n{_clip(state['user_request'], 4500)}",
        f"RESEARCH:\n{_clip(state.get('research', ''), 4000)}",
        f"ANALYSIS:\n{_clip(state.get('analysis', ''), 4000)}",
        f"EXECUTION:\n{_clip(state.get('execution', ''), 4000)}",
        f"AGENTS USED:\n{', '.join(state.get('route', []))}",
    ]
    prompt = _clip("\n\n".join(sections), MAX_FINAL_INPUT)
    try:
        response = chat(
            [
                {"role": "system", "content": FINAL_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_completion_tokens=1200,
        )
        return {"final": _message_text(response)}
    except Exception as exc:
        fallback = (
            state.get("execution")
            or state.get("analysis")
            or state.get("research")
            or "No result."
        )
        return {
            "final": fallback,
            "errors": state.get("errors", []) + [str(exc)],
        }


def first_route(state: AgentState) -> str:
    route = state.get("route") or ["research", "analysis", "execution"]
    return route[0] if route else "final"


def next_after(current: str, state: AgentState) -> str:
    route = state.get("route") or []
    try:
        index = route.index(current)
    except ValueError:
        return "final"
    return route[index + 1] if index + 1 < len(route) else "final"


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("research", research_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("final", final_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        first_route,
        {
            "research": "research",
            "analysis": "analysis",
            "execution": "execution",
            "final": "final",
        },
    )
    for current in ("research", "analysis", "execution"):
        workflow.add_conditional_edges(
            current,
            lambda state, current=current: next_after(current, state),
            {
                "research": "research",
                "analysis": "analysis",
                "execution": "execution",
                "final": "final",
            },
        )
    workflow.add_edge("final", END)
    return workflow.compile()


GRAPH = build_graph()
