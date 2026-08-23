from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    user_request: str
    route: list[str]
    supervisor_reason: str
    research: str
    analysis: str
    execution: str
    sources: list[dict[str, str]]
    observations: list[str]
    final: str
    errors: list[str]
