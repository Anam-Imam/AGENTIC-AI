import os, json, html
import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Nexa",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- STATE -----------------------------------------
defaults = dict(
    messages=[], conversation_id=None, conversation_title="New conversation",
    page="Dashboard", dark=False, conversations=[], favorite_ids=set(),
    search_query="", backend_online=False, pending_prompt=None
)
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


# ----------------------------- API -------------------------------------------
def api(method, path, **kwargs):
    try:
        r = httpx.request(method, BACKEND + path, timeout=30, **kwargs)
        r.raise_for_status()
        st.session_state.backend_online = True
        return r.json() if r.content else {}
    except Exception:
        st.session_state.backend_online = False
        return None


def refresh():
    data = api("GET", "/api/conversations") or []
    if isinstance(data, list):
        st.session_state.conversations = data
        st.session_state.favorite_ids = {
            c["id"] for c in data if c.get("id") and c.get("favorite")
        }
    return st.session_state.conversations


def health():
    return api("GET", "/health")


def find_chat(cid):
    refresh()
    for c in st.session_state.conversations:
        if str(c.get("id")) == str(cid):
            return c
    return api("GET", f"/api/conversations/{cid}")


def save_chat():
    if not st.session_state.messages or not st.session_state.conversation_id:
        return False

    first = next(
        (m.get("content", "") for m in st.session_state.messages
         if m.get("role") == "user"),
        ""
    )
    title = (first.strip().replace("\n", " ")[:70]
             or st.session_state.conversation_title
             or "New conversation")
    st.session_state.conversation_title = title

    data = {
        "id": st.session_state.conversation_id,
        "title": title,
        "messages": st.session_state.messages,
        "favorite": st.session_state.conversation_id in st.session_state.favorite_ids,
    }
    ok = api("POST", "/api/conversations", json=data)
    if ok is not None:
        refresh()
        return True
    return False


def open_chat(cid):
    c = find_chat(cid)
    if not c:
        st.error("This conversation could not be found.")
        return
    st.session_state.messages = c.get("messages", [])
    st.session_state.conversation_id = c.get("id")
    st.session_state.conversation_title = c.get("title") or "Conversation"
    if c.get("favorite"):
        st.session_state.favorite_ids.add(c.get("id"))
    else:
        st.session_state.favorite_ids.discard(c.get("id"))
    st.session_state.page = "Chat"
    st.rerun()


def new_workspace():
    # Save current chat, then open a completely clean Dashboard workspace.
    save_chat()
    st.session_state.messages = []
    st.session_state.conversation_id = None
    st.session_state.conversation_title = "New conversation"
    st.session_state.pending_prompt = None
    st.session_state.page = "Dashboard"
    st.rerun()


def go_dashboard():
    # Dashboard is always clean. The previous chat is saved in history.
    if st.session_state.messages:
        save_chat()
    st.session_state.messages = []
    st.session_state.conversation_id = None
    st.session_state.conversation_title = "New conversation"
    st.session_state.pending_prompt = None
    st.session_state.page = "Dashboard"
    st.rerun()


def favorite(cid=None, conversation=None):
    cid = cid or conversation.get("id")
    if not cid:
        st.warning("Send at least one message before adding this chat to favorites.")
        return

    c = conversation or find_chat(cid) or {}
    current = cid in st.session_state.favorite_ids
    new_value = not current

    if new_value:
        st.session_state.favorite_ids.add(cid)
    else:
        st.session_state.favorite_ids.discard(cid)

    payload = {
        "id": cid,
        "title": st.session_state.conversation_title if not conversation else c.get("title", "New conversation"),
        "messages": st.session_state.messages if not conversation else c.get("messages", []),
        "favorite": new_value,
    }
    ok = api("POST", "/api/conversations", json=payload)

    if ok is not None:
        refresh()
        st.toast(
            "Added to favorites" if new_value else "Removed from favorites",
            icon="✅",
        )
    else:
        (st.session_state.favorite_ids.add(cid)
         if not new_value else st.session_state.favorite_ids.discard(cid))
        st.error("Could not update favorites. Check the backend.")


def delete_chat(cid):
    if api("DELETE", f"/api/conversations/{cid}") is None:
        st.error("Could not delete the conversation.")
        return
    if str(st.session_state.conversation_id) == str(cid):
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.session_state.conversation_title = "New conversation"
    refresh()
    st.session_state.page = "Conversations"
    st.toast("Conversation deleted", icon="✅")
    st.rerun()


# ----------------------------- CHAT ------------------------------------------
def send(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})

    payload = {
        "message": prompt,
        "conversation": st.session_state.messages[:-1],
        "conversation_id": st.session_state.conversation_id,
        "top_k": 5,
    }

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        box = st.empty()
        answer, sources, event = "", [], None

        try:
            with httpx.stream(
                "POST", BACKEND + "/api/chat/stream",
                json=payload, timeout=180
            ) as r:
                r.raise_for_status()

                for line in r.iter_lines():
                    if not line:
                        continue
                    if line.startswith("event:"):
                        event = line[6:].strip()
                        continue
                    if not line.startswith("data:"):
                        continue

                    data = json.loads(line[5:].strip())

                    if event == "meta":
                        st.session_state.conversation_id = data.get(
                            "conversation_id", st.session_state.conversation_id
                        )
                        sources = data.get("sources", [])
                        event = None
                    elif event == "error":
                        raise RuntimeError(data.get("detail", "Backend error"))
                    else:
                        answer += data.get("token", "")
                        box.markdown(answer + "▌")

            answer = answer.strip() or "I could not generate an answer."
            box.markdown(answer)
            st.session_state.messages.append({
                "role": "assistant", "content": answer, "sources": sources
            })
            save_chat()

        except Exception as e:
            st.error(f"Could not complete the request: {e}")
            st.caption("Check that the FastAPI backend and GROQ_API_KEY are available.")


# ----------------------------- STYLE -----------------------------------------
def theme():
    bg, surface, surface2, text, muted, border = (
        ("#071b19", "rgba(12,39,36,.92)", "rgba(16,49,45,.92)", "#effff8", "#a6c2bc", "rgba(174,235,216,.14)")
        if st.session_state.dark else
        ("#f5fcf9", "rgba(255,255,255,.82)", "rgba(239,251,246,.95)", "#102725", "#68807c", "rgba(13,79,74,.10)")
    )

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif}}
.stApp{{background:radial-gradient(circle at 82% 8%,rgba(167,243,208,.25),transparent 28%),radial-gradient(circle at 10% 88%,rgba(13,79,74,.08),transparent 30%),{bg};color:{text}}}
[data-testid="stSidebar"]{{background:{surface};border-right:1px solid {border};backdrop-filter:blur(24px)}}
.brand{{display:flex;gap:.75rem;align-items:center;margin-bottom:1.3rem}}
.logo{{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;color:#fff;font-weight:800;background:linear-gradient(145deg,#0d4f4a,#38a89c);box-shadow:0 10px 30px rgba(13,79,74,.25)}}
.brand-title{{font-family:'Space Grotesk';font-weight:700;color:{text}}}
.brand-sub,.action-sub,.metric-label,.conversation-meta,.source-meta,.source-preview{{color:{muted}}}
.hero,.action-card,.metric,.source,.conversation-card,.chat-toolbar{{border:1px solid {border};border-radius:18px;background:{surface};box-shadow:0 12px 34px rgba(15,67,61,.06)}}
.hero{{padding:2.3rem;border-radius:28px;background:linear-gradient(135deg,{surface},{surface2})}}
.eyebrow{{color:#328c80;font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase}}
.hero h1{{font-family:'Space Grotesk';font-size:clamp(2rem,4vw,3.6rem);line-height:1.03;color:{text};margin:.55rem 0 .75rem}}
.hero p{{color:{muted};max-width:700px}}
.orb-wrap{{display:flex;justify-content:center;min-height:180px;align-items:center}}
.orb{{width:135px;height:135px;border-radius:50%;background:radial-gradient(circle at 35% 28%,#effff8 0 6%,transparent 7%),radial-gradient(circle,#b8f8db 0 16%,#42bca7 37%,#0d4f4a 70%,#092f2d);box-shadow:0 0 70px rgba(73,196,165,.35),0 24px 55px rgba(13,79,74,.25);animation:float 4s ease-in-out infinite}}
@keyframes float{{50%{{transform:translateY(-8px) scale(1.02)}}}}
.section-title{{font-family:'Space Grotesk';font-weight:700;color:{text};margin:1.6rem 0 .8rem}}
.action-card{{padding:1rem;min-height:108px}}
.action-title,.conversation-title,.source-title{{font-weight:700;color:{text}}}
.metric{{padding:1rem;min-height:82px}}
.metric-value{{font-family:'Space Grotesk';font-size:1.4rem;font-weight:700;color:#0d8b7d}}
.source{{padding:.8rem;background:{surface2}}}
.source-preview{{font-size:.74rem;margin-top:.35rem;line-height:1.4}}
.conversation-card{{padding:1rem;margin-bottom:.7rem}}
.conversation-meta,.source-meta{{font-size:.7rem;margin-top:.2rem}}
.chat-toolbar{{padding:.8rem 1rem;margin-bottom:1rem}}
.favorite-row{{margin-top:.55rem}}
div.stButton>button{{border-radius:14px;border:1px solid {border};transition:.2s}}
div.stButton>button:hover{{transform:translateY(-1px);box-shadow:0 8px 20px rgba(13,79,74,.08)}}
</style>
""", unsafe_allow_html=True)


# ----------------------------- UI HELPERS -----------------------------------
def sources_ui(sources):
    if not sources:
        return
    st.markdown("**Sources used**")
    for col, s in zip(st.columns(min(3, len(sources))), sources):
        with col:
            st.markdown(
                f"""<div class="source">
                <div class="source-title">◉ {html.escape(str(s.get("title","Knowledge Base")))}</div>
                <div class="source-meta">{html.escape(str(s.get("source","private document")))} • relevance {html.escape(str(s.get("score","—")))}</div>
                <div class="source-preview">{html.escape(str(s.get("preview","")))}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def favorite_button():
    cid = st.session_state.conversation_id
    if not cid:
        return
    label = "★  Favorited" if cid in st.session_state.favorite_ids else "☆  Add to favorites"
    if st.button(label, key="favorite_current_chat"):
        favorite(cid)
        st.rerun()


def chat_ui():
    if st.session_state.messages:
        st.markdown(f"### {html.escape(st.session_state.conversation_title)}")
        if st.session_state.conversation_id:
            st.markdown(
                f'<div class="chat-toolbar"><b>Active conversation</b> • '
                f'{"★ Favorite" if st.session_state.conversation_id in st.session_state.favorite_ids else "☆ Not favorite"} • '
                f'{len(st.session_state.messages)} messages</div>',
                unsafe_allow_html=True,
            )

    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m.get("role", "assistant")):
            st.markdown(m.get("content", ""))
            if m.get("role") == "assistant":
                sources_ui(m.get("sources", []))
                if i == len(st.session_state.messages) - 1:
                    favorite_button()

    prompt = st.chat_input("Ask your private knowledge-based decision agent…")
    if prompt:
        send(prompt)
        st.rerun()


def conversation_list(items, prefix, mode="normal"):
    for c in items:
        cid, title = c.get("id"), c.get("title", "New conversation")
        fav = cid in st.session_state.favorite_ids or c.get("favorite")
        st.markdown(
            f'<div class="conversation-card"><div class="conversation-title">'
            f'{"★ " if fav else ""}{html.escape(str(title))}</div>'
            f'<div class="conversation-meta">{len(c.get("messages", []))} messages</div></div>',
            unsafe_allow_html=True,
        )

        cols = st.columns([5, 1, 1] if mode == "normal" else [5, 1])

        with cols[0]:
            if st.button("Open conversation", key=f"{prefix}open_{cid}",
                         use_container_width=True, type="primary"):
                open_chat(cid)

        with cols[1]:
            if mode == "favorites":
                if st.button("Remove", key=f"{prefix}remove_{cid}",
                             use_container_width=True):
                    favorite(conversation=c)
                    st.rerun()
            elif mode == "normal":
                if st.button("★" if fav else "☆", key=f"{prefix}fav_{cid}",
                             use_container_width=True):
                    favorite(conversation=c)
                    st.rerun()
            else:
                if st.button("★" if fav else "☆", key=f"{prefix}fav_{cid}",
                             use_container_width=True):
                    favorite(conversation=c)
                    st.rerun()

        if mode == "normal":
            with cols[2]:
                if st.button("🗑", key=f"{prefix}del_{cid}",
                             use_container_width=True):
                    delete_chat(cid)


# ----------------------------- APP -------------------------------------------
theme()
health_data = health()
refresh()

with st.sidebar:
    st.markdown("""
    <div class="brand">
      <div class="logo">✦</div>
      <div><div class="brand-title">NEXA</div><div class="brand-sub">AI Command Center</div></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("＋  New workspace", use_container_width=True, type="primary"):
        new_workspace()

    st.markdown("### Workspace")
    for label, page in [
        ("⌂  Dashboard", "Dashboard"), ("◈  Chat", "Chat"),
        ("▣  Conversations", "Conversations"), ("★  Favorites", "Favorites"),
        ("⌕  Search", "Search"), ("◌  History", "History")
    ]:
        if st.button(label, use_container_width=True,
                     type="primary" if st.session_state.page == page else "secondary",
                     key=f"nav_{page}"):
            if page == "Dashboard":
                go_dashboard()
            else:
                st.session_state.page = page
                st.rerun()

    st.markdown("---\n### Knowledge Base")
    if health_data:
        st.success("● Vector store online")
        st.caption(f"Chroma • Private RAG • {health_data.get('model','Groq')}")
    else:
        st.error("● Backend offline")
        st.caption("Start the FastAPI backend to enable AI requests.")

    st.markdown("---\n### Appearance")
    dark = st.toggle("Dark mode", st.session_state.dark, key="dark_toggle")
    if dark != st.session_state.dark:
        st.session_state.dark = dark
        st.rerun()

    st.markdown("---")
    st.caption("Groq • LangGraph • Chroma")


# ----------------------------- PAGES -----------------------------------------
page = st.session_state.page
chats = st.session_state.conversations

if page == "Dashboard":
    # Dashboard is always a fresh workspace. Previous chats remain saved.
    st.markdown(
        '<div class="hero"><div class="eyebrow">Knowledge-based intelligence</div>'
        '<h1>What would you like<br>to accomplish today?</h1>'
        '<p>Ask questions, retrieve private knowledge, and receive evidence-backed recommendations from your AI decision agent.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="orb-wrap"><div class="orb"></div></div>', unsafe_allow_html=True)

    # Ask a question directly from the Dashboard.
    dashboard_prompt = st.chat_input(
        "Ask your knowledge-based decision agent anything…",
        key="dashboard_chat_input",
    )
    if dashboard_prompt:
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.session_state.conversation_title = "New conversation"
        st.session_state.pending_prompt = dashboard_prompt
        st.session_state.page = "Chat"
        st.rerun()

    st.markdown('<div class="section-title">Quick AI actions</div>', unsafe_allow_html=True)
    actions = [
        ("✨", "Analyze information", "Find evidence and key facts", "Analyze the available information and summarize the key facts."),
        ("🧠", "Make a decision", "Compare options with context", "Help me make a decision using the available knowledge base."),
        ("📚", "Ask knowledge base", "Retrieve private information", "What important information is available in the private knowledge base?"),
        ("📝", "Summarize", "Turn documents into concise insights", "Summarize the most important information from the knowledge base."),
    ]
    for col, (icon, title, sub, prompt) in zip(st.columns(4), actions):
        with col:
            st.markdown(
                f'<div class="action-card"><div>{icon}</div><div class="action-title">{title}</div><div class="action-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Use action", key=f"qa_{title}", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_id = None
                st.session_state.conversation_title = "New conversation"
                st.session_state.pending_prompt = prompt
                st.session_state.page = "Chat"
                st.rerun()

    st.markdown('<div class="section-title">Workspace overview</div>', unsafe_allow_html=True)
    requests = sum(m.get("role") == "user" for c in chats for m in c.get("messages", []))
    favorites = sum(c.get("id") in st.session_state.favorite_ids or c.get("favorite") for c in chats)
    completed = sum(any(m.get("role") == "assistant" for m in c.get("messages", [])) for c in chats)

    for col, (v, label) in zip(
        st.columns(4),
        [(len(chats), "Conversations"), (requests, "AI requests"), (favorites, "Favorites"), (completed, "Completed chats")]
    ):
        with col:
            st.markdown(
                f'<div class="metric"><div class="metric-value">{v}</div><div class="metric-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-title">Recent conversations</div>', unsafe_allow_html=True)
    if chats:
        for c in chats[:5]:
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(
                    f'**{html.escape(str(c.get("title","New conversation")))}**  \\n'
                    f'<small>{len(c.get("messages",[]))} messages</small>',
                    unsafe_allow_html=True,
                )
            with col2:
                if st.button("Open", key=f"dash_{c.get('id')}"):
                    open_chat(c.get("id"))
    else:
        st.info("No conversations yet. Start your first AI task.")

elif page == "Chat":
    # A Dashboard question is executed in a new Chat workspace.
    if st.session_state.pending_prompt and not st.session_state.messages:
        p = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        send(p)
        st.rerun()
    else:
        chat_ui()

elif page == "Conversations":
    st.markdown("### Conversations")
    st.caption("Every saved conversation can be reopened exactly where you left it.")
    conversation_list(chats, "conv_", "normal") if chats else st.info("No saved conversations yet. Start a chat to create one.")

elif page == "Favorites":
    st.markdown("### Favorites")
    favs = [c for c in chats if c.get("id") in st.session_state.favorite_ids or c.get("favorite")]
    conversation_list(favs, "fav_", "favorites") if favs else st.info("No favorite conversations yet. Use ☆ Add to favorites below an AI answer.")

elif page == "Search":
    st.markdown("### Search")
    q = st.text_input("Search conversations", value=st.session_state.search_query, placeholder="Try: policy, recommendation, pricing...")
    st.session_state.search_query = q
    if q.strip():
        q = q.lower().strip()
        results = [
            c for c in chats
            if q in str(c.get("title","")).lower()
            or q in json.dumps(c.get("messages", []), ensure_ascii=False).lower()
        ]
        if results:
            st.success(f"Found {len(results)} matching conversation(s).")
            conversation_list(results, "search_", "search")
        else:
            st.info("No matching conversations found.")
    else:
        st.info("Enter a word or phrase to search your conversation history.")

elif page == "History":
    st.markdown("### History")
    st.caption("All saved conversations, newest first.")
    conversation_list(chats, "history_", "history") if chats else st.info("Your conversation history is empty.")
