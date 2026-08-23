import json
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

FAVORITES_FILE = Path(__file__).parent / "favorites.json"


def load_favorites():
    if not FAVORITES_FILE.exists():
        return []

    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_favorites(favorites):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=4, ensure_ascii=False)


def add_favorite(favorite):
    favorites = load_favorites()

    exists = any(
        item.get("goal") == favorite["goal"]
        and item.get("answer") == favorite["answer"]
        for item in favorites
    )

    if not exists:
        favorites.append(favorite)
        save_favorites(favorites)

    st.session_state.favorites = favorites


from agent import run_agent, extract_tool_events, extract_sources

st.set_page_config(
    page_title="Nexa AI — Intelligent Task Agent",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS_PATH = Path(__file__).parent / "styles.css"
base_css = CSS_PATH.read_text(encoding="utf-8")
dark_css = """
<style>
.stApp {
  background: radial-gradient(circle at 85% 5%, rgba(26,112,102,.20), transparent 28%), #0b1716 !important;
  color: #e8f3f0 !important;
}
section[data-testid="stSidebar"] { background: rgba(9,24,22,.88) !important; border-right-color: rgba(188,239,224,.10) !important; }
.topbar h1, .hero h2, .feature-card h3, .metric-value, .empty-state h3 { color: #e8f3f0 !important; }
.topbar p, .hero p, .feature-card p, .prompt-card p, .metric-label, .source-snippet, .favorite-card p { color: #a9bbb7 !important; }
.prompt-card, .feature-card, .metric-card, .source-card, .history-card, .favorite-card, .top-pill {
  background: rgba(20,39,36,.78) !important;
  border-color: rgba(188,239,224,.10) !important;
}
.status-card { background: rgba(188,239,224,.08) !important; }
.brand-name { color: #e8f3f0 !important; }
.source-url, .history-card small, .metric-caption { color: #81928e !important; }
</style>
"""
st.markdown(
    f"<style>{base_css}</style>{dark_css if st.session_state.get('theme') == 'dark' else ''}",
    unsafe_allow_html=True,
)

# ---------- Session state ----------
defaults = {
    "messages": [],
    "history": [],
    "favorites": [],
    "theme": "light",
    "active_page": "Chat",
    "last_sources": [],
    "last_tools": [],
    "stats": {"tasks": 0, "tool_calls": 0, "successful": 0},
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = (
            value.copy()
            if isinstance(value, dict)
            else list(value)
            if isinstance(value, list)
            else value
        )

st.session_state.favorites = load_favorites()

# ---------- Helpers ----------
def metric_card(label, value, caption, icon):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div>
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-caption">{caption}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def source_card(source):
    title = source.get("title") or source.get("url") or "Reference"
    url = source.get("url", "")
    snippet = source.get("snippet", "")

    if url:
        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-top">
                    <span class="source-dot"></span>
                    <a href="{url}" target="_blank">{title}</a>
                </div>
                <div class="source-url">{url}</div>
                <div class="source-snippet">{snippet[:260]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="source-card"><b>{title}</b><div class="source-snippet">{snippet[:260]}</div></div>',
            unsafe_allow_html=True,
        )


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">✦</div>
            <div>
                <div class="brand-name">Nexa AI</div>
                <div class="brand-sub">Intelligent Task Agent</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("＋  New task", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.last_sources = []
        st.session_state.last_tools = []
        st.session_state.active_page = "Chat"
        st.rerun()

    st.markdown(
        '<div class="side-label">WORKSPACE</div>',
        unsafe_allow_html=True,
    )

    pages = ["Chat", "Dashboard", "History", "Favorites"]
    icons = {"Chat": "◌", "Dashboard": "▦", "History": "◷", "Favorites": "☆"}

    for page in pages:
        active = st.session_state.active_page == page

        if st.button(
            f"{icons[page]}  {page}",
            key=f"nav_{page}",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.active_page = page
            st.rerun()

    st.markdown(
        '<div class="side-label">AGENT STATUS</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="status-card">
            <span class="pulse"></span>
            <div>
                <b>Agent online</b>
                <small>Ready for task execution</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="side-label">PREFERENCES</div>',
        unsafe_allow_html=True,
    )

    dark = st.toggle(
        "Dark mode",
        value=st.session_state.theme == "dark",
    )

    new_theme = "dark" if dark else "light"

    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    st.markdown(
        '<div class="sidebar-footer">ReAct-style loop · LangChain · Tool Calling</div>',
        unsafe_allow_html=True,
    )


# ---------- Header ----------
st.markdown(
    """
    <div class="topbar">
        <div>
            <div class="eyebrow">INTELLIGENT TASK EXECUTION</div>
            <h1>AI Workspace</h1>
            <p>Give Nexa a goal. It will analyze, select tools, observe results, and return a useful answer.</p>
        </div>
        <div class="top-pill"><span class="pulse"></span> Live agent</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------- Dashboard ----------
if st.session_state.active_page == "Dashboard":
    st.markdown(
        '<div class="section-title">Overview</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Tasks executed",
            st.session_state.stats["tasks"],
            "This session",
            "↗",
        )

    with c2:
        metric_card(
            "Tool calls",
            st.session_state.stats["tool_calls"],
            "Agent actions",
            "⚙",
        )

    with c3:
        metric_card(
            "Successful",
            st.session_state.stats["successful"],
            "Completed tasks",
            "✓",
        )

    with c4:
        rate = (
            0
            if not st.session_state.stats["tasks"]
            else round(
                st.session_state.stats["successful"]
                / st.session_state.stats["tasks"]
                * 100
            )
        )

        metric_card(
            "Success rate",
            f"{rate}%",
            "Current session",
            "◔",
        )

    st.markdown(
        '<div class="dashboard-grid">',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">◎</div>
            <h3>Plan → Act → Observe</h3>
            <p>The agent decomposes goals, selects tools, evaluates their outputs, and continues until it can provide a final response.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⌁</div>
            <h3>Tool calling</h3>
            <p>Built-in calculator, time, and optional web search tools demonstrate practical agent actions.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">◈</div>
            <h3>Production UI</h3>
            <p>Responsive layout, loading states, empty states, errors, history, favorites, references, and theme switching.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )


# ---------- History ----------
elif st.session_state.active_page == "History":
    st.markdown(
        '<div class="section-title">Task history</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.history:
        st.markdown(
            '<div class="empty-state"><div class="empty-icon">◷</div><h3>No tasks yet</h3><p>Your completed tasks will appear here.</p></div>',
            unsafe_allow_html=True,
        )
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            st.markdown(
                f"""
                <div class="history-card">
                    <div class="history-icon">✦</div>
                    <div>
                        <b>{item["goal"][:100]}</b>
                        <small>{item["timestamp"]} · {item["tool_count"]} tool calls</small>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------- Favorites ----------
elif st.session_state.active_page == "Favorites":

    st.markdown(
        '<div class="section-title">Favorites</div>',
        unsafe_allow_html=True,
    )

    favorites = load_favorites()
    st.session_state.favorites = favorites

    if not favorites:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-icon">☆</div>
                <h3>No favorites yet</h3>
                <p>Add a response to Favorites from the Chat page.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            f"### ★ {len(favorites)} Saved Favorite"
            + ("s" if len(favorites) != 1 else "")
        )

        for index, favorite in enumerate(reversed(favorites)):

            goal = favorite.get("goal", "Untitled task")
            answer = favorite.get("answer", "")
            timestamp = favorite.get("timestamp", "")

            with st.container(border=True):

                st.markdown(f"### ★ {goal}")

                st.markdown(answer)

                st.caption(timestamp)

                if st.button(
                    "🗑 Remove",
                    key=f"remove_favorite_{index}",
                ):
                    real_index = len(favorites) - 1 - index

                    favorites.pop(real_index)

                    save_favorites(favorites)

                    st.session_state.favorites = favorites

                    st.rerun()


# ---------- Chat ----------
else:
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="hero">
                <div class="hero-orb">✦</div>
                <div class="hero-kicker">YOUR AI EXECUTION PARTNER</div>
                <h2>What would you like<br><span>Nexa to accomplish?</span></h2>
                <p>Ask a goal, not just a question. The agent can break it down and use tools when needed.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        examples = [
            (
                "Research",
                "Research the latest trends in AI agents and summarize them.",
            ),
            (
                "Calculate",
                "Calculate the monthly cost if I spend 1200, 850 and 975 each week.",
            ),
            (
                "Plan",
                "Create a practical 7-step plan for learning Python and LangChain.",
            ),
        ]

        cols = st.columns(3)

        for col, (tag, example_prompt) in zip(cols, examples):
            with col:
                st.markdown(
                    f"""
                    <div class="prompt-card">
                        <span>{tag}</span>
                        <p>{example_prompt}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ---------- Chat history ----------
    for message in st.session_state.messages:
        role = message["role"]

        with st.chat_message(role):
            st.markdown(message["content"])

            if role == "assistant" and message.get("sources"):
                with st.expander(
                    f"References · {len(message['sources'])}",
                    expanded=False,
                ):
                    for source in message["sources"]:
                        source_card(source)

    # ---------- Chat input ----------
    prompt = st.chat_input(
        "Give the agent a goal…",
        max_chars=8000,
    )

    if prompt:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            status = st.empty()

            status.markdown(
                """
                <div class="thinking">
                    <span></span>
                    <span></span>
                    <span></span>
                    Agent is analyzing the task…
                </div>
                """,
                unsafe_allow_html=True,
            )

            progress = st.status(
                "Executing agent workflow",
                expanded=True,
            )

            try:
                # ---------- Run agent ----------
                result = run_agent(prompt)

                events = extract_tool_events(result)
                sources = extract_sources(result)
                answer = result["answer"]

                # ---------- Task completed ----------
                progress.update(
                    label="Task completed",
                    state="complete",
                    expanded=False,
                )

                status.empty()

                st.markdown(answer)

                # ---------- Favorite ----------
                favorite = {
                    "goal": prompt,
                    "answer": answer,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                }

                favorites = load_favorites()

                is_saved = any(
                    item.get("goal") == favorite["goal"]
                    and item.get("answer") == favorite["answer"]
                    for item in favorites
                )

                if is_saved:
                    st.success("★ Already in Favorites")
                else:
                    st.button(
                        "☆ Add to Favorites",
                        key=f"favorite_{hash(prompt)}",
                        on_click=add_favorite,
                        args=(favorite,),
                    )

                # ---------- Execution trace ----------
                if events:
                    with st.expander(
                        f"Execution trace · {len(events)} tool call(s)",
                        expanded=False,
                    ):
                        for event in events:
                            st.markdown(
                                f"""
                                <div class="trace-row">
                                    <b>{event["tool"]}</b>
                                    <span>{event["input"][:180]}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                # ---------- References ----------
                if sources:
                    with st.expander(
                        f"References · {len(sources)}",
                        expanded=False,
                    ):
                        for source in sources:
                            source_card(source)

                # ---------- Save conversation ----------
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    }
                )

                # ---------- Last execution data ----------
                st.session_state.last_sources = sources
                st.session_state.last_tools = events

                # ---------- Statistics ----------
                st.session_state.stats["tasks"] += 1
                st.session_state.stats["tool_calls"] += len(events)
                st.session_state.stats["successful"] += 1

                # ---------- History ----------
                st.session_state.history.append(
                    {
                        "goal": prompt,
                        "answer": answer,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                        "tool_count": len(events),
                    }
                )

            except Exception as exc:
                progress.update(
                    label="Task failed",
                    state="error",
                    expanded=True,
                )

                status.empty()

                st.error("Agent execution failed.")

                with st.expander(
                    "🔍 Technical error",
                    expanded=True,
                ):
                    st.exception(exc)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"Error: {exc}",
                        "sources": [],
                    }
                )