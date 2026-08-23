from __future__ import annotations

import time

import streamlit as st

from agents.graph import GRAPH
from core.storage import (
    add_session,
    clear_history,
    delete_session,
    load_history,
    update_favorite,
)
from ui.components import agent_cards, ai_core, render_sources
from ui.styles import inject_css

st.set_page_config(
    page_title="NEXUS // AI Command Center",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------- Session state -----------------------------
DEFAULTS = {
    "theme_light": False,
    "core_state": "idle",
    "messages": [],
    "last_trace": {},
    "pending_request": "",
    "executed_pending": False,
    "show_history": False,
    "history_search": "",
    "composer_mode": "Ask AI",
    "mission_input": "",
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

inject_css(st.session_state.theme_light)


def set_mode(mode: str, template: str = "") -> None:
    st.session_state.composer_mode = mode
    if template:
        st.session_state.mission_input = template
    st.session_state.show_history = mode in {"History", "Search"}


def new_chat() -> None:
    st.session_state.messages = []
    st.session_state.last_trace = {}
    st.session_state.core_state = "idle"
    st.session_state.pending_request = ""
    st.session_state.executed_pending = False
    st.session_state.composer_mode = "Ask AI"
    st.session_state.mission_input = ""
    st.session_state.show_history = False
    st.rerun()


# ----------------------------- Header -----------------------------
left, center, right = st.columns([1.1, 2.2, 1.1])
with left:
    st.markdown('<div class="brand">NEXUS // MULTI-AGENT OS</div>', unsafe_allow_html=True)
with center:
    st.markdown(
        '<div style="text-align:center" class="pill"><span class="pulse"></span>GROQ FABRIC · LANGGRAPH ORCHESTRATION</div>',
        unsafe_allow_html=True,
    )
with right:
    if st.button("☼ / ☾", use_container_width=True, key="theme_btn"):
        st.session_state.theme_light = not st.session_state.theme_light
        st.rerun()

st.markdown(
    '<div class="hero"><h1>Think. Delegate. Execute.</h1><p>A cinematic multi-agent command center where a Supervisor routes difficult problems to Research, Analysis and Execution agents — then merges their work into one clear result.</p></div>',
    unsafe_allow_html=True,
)

# ----------------------------- Quick actions -----------------------------
q1, q2, q3, q4, q5, q6 = st.columns(6)
quick = [
    (q1, "＋ New Chat", "new"),
    (q2, "⌁ Ask AI", "ask"),
    (q3, "◌ Analyze", "analyze"),
    (q4, "✦ Generate", "generate"),
    (q5, "⌕ Search", "search"),
    (q6, "☆ History", "history"),
]
for col, label, action in quick:
    with col:
        if st.button(label, key=f"quick_{action}", use_container_width=True):
            if action == "new":
                new_chat()
            elif action == "ask":
                set_mode("Ask AI", "Ask a difficult question and have the Supervisor decide how the agents should collaborate.")
                st.rerun()
            elif action == "analyze":
                set_mode("Analyze", "Analyze this problem, compare the main options, identify risks and recommend the strongest approach:\n\n")
                st.rerun()
            elif action == "generate":
                set_mode("Generate", "Generate a practical deliverable for the following goal. Include concrete steps, structure and implementation details:\n\n")
                st.rerun()
            elif action == "search":
                set_mode("Search")
                st.rerun()
            elif action == "history":
                st.session_state.show_history = True
                st.rerun()

# ----------------------------- AI Core -----------------------------
st.markdown('<div class="glass" style="margin-top:1rem;padding:.7rem 1rem">', unsafe_allow_html=True)
ai_core(st.session_state.core_state)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------- Telemetry -----------------------------
st.markdown("### Neural telemetry")
status = st.session_state.last_trace.get(
    "status",
    {"research": "standby", "analysis": "standby", "execution": "standby"},
)
agent_cards(status)

# ----------------------------- Mission console -----------------------------
st.markdown(f"### Mission console · {st.session_state.composer_mode}")
with st.form("mission_form", clear_on_submit=True):
    request = st.text_area(
        "",
        key="mission_input",
        placeholder="Describe a difficult problem…",
        height=150,
        label_visibility="collapsed",
    )
    c1, c2, c3 = st.columns([5, 1.4, 1.2])
    with c1:
        st.caption("The Supervisor routes the mission to the specialist agents selected for this task.")
    with c2:
        show_trace = st.checkbox("Show trace", value=True)
    with c3:
        run = st.form_submit_button("EXECUTE ◇", use_container_width=True, type="primary")

if run:
    cleaned = request.strip()
    if not cleaned:
        st.warning("Enter a mission first.")
    else:
        st.session_state.pending_request = cleaned
        st.session_state.core_state = "thinking"
        st.session_state.last_trace = {
            "status": {"research": "queued", "analysis": "queued", "execution": "queued"}
        }
        st.session_state.executed_pending = False
        st.rerun()

# ----------------------------- Deferred execution -----------------------------
if (
    st.session_state.get("pending_request")
    and st.session_state.core_state == "thinking"
    and not st.session_state.get("executed_pending")
):
    st.session_state.executed_pending = True
    mission = st.session_state.pending_request
    with st.spinner("Supervisor coordinating specialist agents…"):
        try:
            result = GRAPH.invoke({"user_request": mission})
            route = result.get("route", [])
            st.session_state.last_trace = {
                "route": route,
                "reason": result.get("supervisor_reason", ""),
                "status": {
                    "research": "complete" if result.get("research") else "skipped",
                    "analysis": "complete" if result.get("analysis") else "skipped",
                    "execution": "complete" if result.get("execution") else "skipped",
                },
                "sources": result.get("sources", []),
                "observations": result.get("observations", []),
                "errors": result.get("errors", []),
            }
            response = result.get("final", "No final response generated.")
            st.session_state.messages.append({"role": "user", "content": mission})
            st.session_state.messages.append({"role": "assistant", "content": response})
            add_session(
                title=mission,
                request=mission,
                response=response,
                agents=route,
                sources=result.get("sources", []),
            )
            st.session_state.core_state = "responding"
            st.session_state.pending_request = ""
            st.session_state.executed_pending = False
        except Exception as exc:
            message = str(exc)
            st.session_state.last_trace = {
                "status": {"research": "error", "analysis": "error", "execution": "error"},
                "errors": [message],
            }
            st.session_state.core_state = "error"
            st.session_state.pending_request = ""
            st.session_state.executed_pending = False
            st.error(message)
        else:
            st.rerun()

# ----------------------------- Output -----------------------------
if st.session_state.messages:
    st.markdown("### Output chamber")
    for msg in st.session_state.messages[-6:]:
        role = "YOU" if msg["role"] == "user" else "NEXUS"
        st.markdown(f"**{role}**")
        if msg["role"] == "assistant":
            st.markdown(msg["content"])
        else:
            st.markdown(f'<div class="result-box">{msg["content"]}</div>', unsafe_allow_html=True)
        st.markdown("")

trace = st.session_state.last_trace
if trace and show_trace:
    st.markdown("### Orchestration trace")
    if trace.get("route"):
        st.write("**Supervisor route:**", " → ".join(trace["route"]))
    if trace.get("reason"):
        st.caption(trace["reason"])
    observations = trace.get("observations", [])
    if observations:
        for item in observations:
            st.markdown(f"- {item}")
    if trace.get("errors"):
        st.warning(" · ".join(trace["errors"]))
    render_sources(trace.get("sources", []))

# ----------------------------- Search / History -----------------------------
if st.session_state.show_history:
    st.markdown("### Archive")
    search_col, clear_col = st.columns([5, 1])
    with search_col:
        st.session_state.history_search = st.text_input(
            "Search history",
            value=st.session_state.history_search,
            placeholder="Search by mission or result…",
            key="history_search_input",
        )
    with clear_col:
        st.write("")
        if st.button("Clear all", key="clear_history_btn", use_container_width=True):
            clear_history()
            st.session_state.messages = []
            st.session_state.show_history = True
            st.rerun()

    query = st.session_state.history_search.strip().lower()
    history = load_history()
    matches = []
    for index, item in enumerate(history):
        haystack = f"{item.get('title', '')} {item.get('request', '')} {item.get('response', '')}".lower()
        if not query or query in haystack:
            matches.append((index, item))

    if not matches:
        st.caption("No matching sessions.")
    else:
        for index, item in reversed(matches[-20:]):
            title = item.get("title", "Untitled mission")[:80]
            meta = ", ".join(item.get("agents", [])) or "no agents"
            a, b, c, d = st.columns([6, 1.1, 1.1, 1.1])
            with a:
                st.markdown(f"**{title}**")
                st.caption(f"Agents: {meta}")
            with b:
                if st.button("Open", key=f"open_{index}", use_container_width=True):
                    st.session_state.messages = [
                        {"role": "user", "content": item.get("request", "")},
                        {"role": "assistant", "content": item.get("response", "")},
                    ]
                    st.session_state.core_state = "responding"
                    st.session_state.last_trace = {
                        "route": item.get("agents", []),
                        "sources": item.get("sources", []),
                        "status": {
                            "research": "complete" if "research" in item.get("agents", []) else "skipped",
                            "analysis": "complete" if "analysis" in item.get("agents", []) else "skipped",
                            "execution": "complete" if "execution" in item.get("agents", []) else "skipped",
                        },
                    }
                    st.rerun()
            with c:
                favorite = bool(item.get("favorite", False))
                if st.button("★" if favorite else "☆", key=f"fav_{index}", use_container_width=True):
                    update_favorite(index, not favorite)
                    st.rerun()
            with d:
                if st.button("Delete", key=f"del_{index}", use_container_width=True):
                    delete_session(index)
                    st.rerun()

# Let the response state settle into a stable visual state.
if st.session_state.core_state == "responding":
    time.sleep(0.05)
