from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from .rag import retrieve
from .groq_client import SYSTEM_PROMPT, answer


class AgentState(TypedDict, total=False):
    query: str
    conversation: list[dict]
    top_k: int
    intent: str
    sources: list[dict]
    response: str


def analyze_query(state: AgentState) -> AgentState:
    q = state["query"].lower()

    if any(x in q for x in ["should", "recommend", "decision", "choose", "best", "whether"]):
        intent = "decision"
    elif any(x in q for x in ["summarize", "summary", "brief"]):
        intent = "summary"
    else:
        intent = "knowledge"

    return {**state, "intent": intent}


def retrieve_context(state: AgentState) -> AgentState:
    return {
        **state,
        "sources": retrieve(state["query"], state.get("top_k", 5)),
    }


def generate_answer(state: AgentState) -> AgentState:
    sources = state.get("sources", [])

    context = "\n\n".join(
        f"[Source {i + 1} — {s['source']}]\n{s['content']}"
        for i, s in enumerate(sources)
    ) or "No relevant private knowledge-base documents were retrieved."

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in state.get("conversation", [])[-8:]
        if m.get("role") in {"user", "assistant"} and m.get("content")
    ]

    prompt = f"""User request:
{state['query']}

Request type:
{state.get('intent', 'knowledge')}

Retrieved private knowledge-base context:
{context}

Answer using the private context.
If the context is insufficient, say so clearly.
For decisions, give a recommendation plus concise evidence-based rationale.
Do not expose chain-of-thought."""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    return {**state, "response": answer(messages)}


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("analyze_query", analyze_query)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_edge(START, "analyze_query")
    graph.add_edge("analyze_query", "retrieve_context")
    graph.add_edge("retrieve_context", "generate_answer")
    graph.add_edge("generate_answer", END)
    return graph.compile()


agent = build_agent()
