import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.groq_agent import CommunicationAgent
from services.notifications import NotificationService
from services.storage import (
    add_log,
    add_to_history,
    get_history,
    get_logs,
    get_favorites,
    toggle_favorite,
)

load_dotenv()

st.set_page_config(
    page_title="AURA • Intelligent Communication Assistant",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Session state ----------
defaults = {
    "theme": "light",
    "page": "Home",
    "messages": [],
    "last_analysis": None,
    "last_result": None,
    "notice": None,
    "request_count": 0,
    "favorite_ids": [],
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------- Styling ----------
def inject_css(theme="light"):
    dark = theme == "dark"
    bg = "#0c1017" if dark else "#f6f8fb"
    surface = "rgba(255,255,255,.075)" if dark else "rgba(255,255,255,.78)"
    text = "#f5f7fb" if dark else "#172033"
    muted = "#aab4c4" if dark else "#718096"
    border = "rgba(255,255,255,.12)" if dark else "rgba(112,132,164,.16)"
    card = "#121925" if dark else "#ffffff"
    st.markdown(f"""
    <style>
    :root {{
      --bg:{bg}; --surface:{surface}; --text:{text}; --muted:{muted};
      --border:{border}; --card:{card}; --blue:#4c8dff; --lav:#a88bff;
    }}
    .stApp {{
      background:
        radial-gradient(circle at 10% 10%, rgba(122,170,255,.13), transparent 26%),
        radial-gradient(circle at 90% 20%, rgba(184,157,255,.14), transparent 25%),
        linear-gradient(135deg, var(--bg), #eef3fa 55%, #f9f7ff);
      color:var(--text);
    }}
    .stApp::before {{
      content:""; position:fixed; inset:-30%; pointer-events:none; z-index:-1;
      background:linear-gradient(120deg,transparent 42%,rgba(110,156,255,.06),transparent 58%);
      animation:aurora 12s ease-in-out infinite alternate;
    }}
    @keyframes aurora {{ from{{transform:translateX(-8%) rotate(-2deg)}} to{{transform:translateX(8%) rotate(2deg)}} }}
    .block-container {{ max-width:1450px; padding:1.2rem 2rem 4rem; }}
    [data-testid="stSidebar"] {{
      background:rgba(255,255,255,.55);
      backdrop-filter:blur(22px); border-right:1px solid var(--border);
    }}
    .brand {{
      display:flex; align-items:center; gap:12px; padding:8px 6px 18px;
    }}
    .brand-orb {{
      width:42px;height:42px;border-radius:14px;
      background:linear-gradient(135deg,#dcecff,#ffffff 45%,#dcd0ff);
      box-shadow:0 8px 28px rgba(76,141,255,.22), inset 0 0 0 1px rgba(255,255,255,.9);
      display:grid;place-items:center;font-size:20px;
      animation:breathe 3.5s ease-in-out infinite;
    }}
    @keyframes breathe {{ 50%{{transform:scale(1.07);box-shadow:0 12px 38px rgba(76,141,255,.30)}} }}
    .brand-title {{font-weight:800;font-size:1.05rem;color:var(--text)}}
    .brand-sub {{font-size:.72rem;color:var(--muted);letter-spacing:.12em;text-transform:uppercase}}
    .hero {{
      position:relative; overflow:hidden; min-height:450px; border:1px solid var(--border);
      border-radius:34px; padding:30px; background:var(--surface);
      backdrop-filter:blur(24px); box-shadow:0 25px 70px rgba(47,66,97,.10);
    }}
    .hero-grid {{display:grid;grid-template-columns:1.1fr .9fr;gap:20px;align-items:center;min-height:390px}}
    .eyebrow {{color:#5c8de0;font-size:.78rem;font-weight:800;letter-spacing:.18em;text-transform:uppercase}}
    .hero h1 {{font-size:clamp(2.3rem,5vw,5rem);line-height:.98;margin:14px 0;
      letter-spacing:-.055em;color:var(--text)}}
    .hero p {{max-width:650px;color:var(--muted);font-size:1.03rem;line-height:1.7}}
    .orb-stage {{height:360px;position:relative;display:grid;place-items:center}}
    .orb {{
      width:190px;height:190px;border-radius:50%;position:relative;z-index:3;
      background:radial-gradient(circle at 35% 30%,#fff 0 10%,#dceaff 22%,#b9d6ff 43%,#c9b8ff 68%,#fff 100%);
      box-shadow:0 0 0 18px rgba(255,255,255,.45),0 0 70px rgba(91,142,255,.28),inset 0 -18px 40px rgba(120,99,214,.15);
      animation:orbPulse 4s ease-in-out infinite;
    }}
    .orb::after {{content:"✦";position:absolute;inset:0;display:grid;place-items:center;font-size:52px;color:#668ed9;opacity:.65}}
    @keyframes orbPulse {{0%,100%{{transform:scale(.98)}}50%{{transform:scale(1.045)}}}}
    .orbit {{position:absolute;border:1px dashed rgba(90,120,170,.24);border-radius:50%;animation:spin 16s linear infinite}}
    .orbit.one {{width:280px;height:160px;transform:rotate(22deg)}}
    .orbit.two {{width:330px;height:210px;transform:rotate(-32deg);animation-duration:22s;animation-direction:reverse}}
    .orbit.three {{width:230px;height:300px;transform:rotate(62deg);animation-duration:18s}}
    @keyframes spin {{to{{transform:rotate(382deg)}}}}
    .float {{position:absolute;font-size:22px;animation:float 5s ease-in-out infinite}}
    .f1{{top:20px;left:10%}} .f2{{top:30%;right:4%;animation-delay:1s}} .f3{{bottom:10%;left:6%;animation-delay:2s}}
    .f4{{bottom:5%;right:16%;animation-delay:.6s}} .f5{{top:8%;right:20%;animation-delay:1.7s}}
    @keyframes float {{0%,100%{{transform:translateY(0) rotate(0)}}50%{{transform:translateY(-18px) rotate(8deg)}}}}
    .glass-card {{
      border:1px solid var(--border); background:var(--surface); backdrop-filter:blur(18px);
      border-radius:24px;padding:20px;box-shadow:0 16px 45px rgba(44,61,91,.08);
      transition:transform .25s ease,box-shadow .25s ease,border-color .25s ease;
    }}
    .glass-card:hover {{transform:translateY(-5px);box-shadow:0 22px 55px rgba(44,61,91,.13);border-color:rgba(76,141,255,.28)}}
    .metric {{font-size:2rem;font-weight:850;color:var(--text);letter-spacing:-.04em}}
    .metric-label {{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em}}
    .section-title {{font-size:1.45rem;font-weight:800;color:var(--text);margin:1.4rem 0 .8rem}}
    .chip {{display:inline-block;padding:6px 10px;border-radius:999px;background:rgba(76,141,255,.09);
      color:#4e7dcc;font-size:.74rem;font-weight:750;margin:3px}}
    .status {{
      display:inline-flex;align-items:center;gap:7px;padding:7px 11px;border-radius:999px;
      background:rgba(78,196,137,.10);color:#2f9a6a;font-size:.76rem;font-weight:800;
    }}
    .status-dot {{width:7px;height:7px;border-radius:50%;background:#4bc58b;box-shadow:0 0 12px #4bc58b}}
    .message {{
      border:1px solid var(--border);border-radius:20px;padding:16px 18px;margin:10px 0;
      background:var(--card);box-shadow:0 10px 30px rgba(44,61,91,.05)
    }}
    .message.user {{margin-left:12%;background:linear-gradient(135deg,#edf5ff,#f7f3ff)}}
    .message.ai {{margin-right:12%}}
    .message-meta {{font-size:.7rem;color:var(--muted);margin-bottom:7px;font-weight:750}}
    .tiny {{font-size:.78rem;color:var(--muted)}}
    .action-card {{
      min-height:130px; border:1px solid var(--border); border-radius:22px; padding:18px;
      background:linear-gradient(145deg,rgba(255,255,255,.78),rgba(237,243,251,.62));
      transition:.25s; 
    }}
    .action-card:hover {{transform:translateY(-4px) rotateX(2deg);box-shadow:0 18px 40px rgba(76,141,255,.12)}}
    .stButton>button {{
      border-radius:14px !important;border:1px solid rgba(76,141,255,.15) !important;
      background:linear-gradient(135deg,#ffffff,#eef4ff) !important;color:#315c9d !important;
      font-weight:750 !important;box-shadow:0 8px 22px rgba(76,141,255,.09);
      transition:transform .18s ease,box-shadow .18s ease !important;
    }}
    .stButton>button:hover {{transform:translateY(-2px) !important;box-shadow:0 12px 28px rgba(76,141,255,.18) !important}}
    .stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"] {{
      border-radius:15px !important;border:1px solid var(--border) !important;
      background:rgba(255,255,255,.72) !important;
    }}
    .action-btn-dark button {{
    background: linear-gradient(135deg,#172235,#2d3f5d) !important;
    color: white !important;
    border: 1px solid #172235 !important;
    box-shadow: 0 10px 26px rgba(23,34,53,.25) !important;
}}

.action-btn-dark button:hover {{
    background: linear-gradient(135deg,#101a2b,#243652) !important;
    color: white !important;
    transform: translateY(-2px) !important;
}}
    [data-testid="stSidebar"] .stButton>button[kind="primary"] {{
  background:linear-gradient(135deg,#172235,#2b3c58) !important;
  color:#ffffff !important;
  border:1px solid #172235 !important;
  box-shadow:0 10px 26px rgba(23,34,53,.24) !important;
}}

[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover {{
  background:linear-gradient(135deg,#111a2a,#263650) !important;
  color:#ffffff !important;
  transform:translateY(-2px) !important;
  box-shadow:0 14px 32px rgba(23,34,53,.30) !important;
}}
    .streaming {{overflow:hidden;white-space:nowrap;border-right:2px solid #6595e8;animation:typing 1.8s steps(30,end)}}
    @keyframes typing {{from{{width:0}}to{{width:100%}}}}
    @media(max-width:900px) {{
      .hero-grid{{grid-template-columns:1fr}} .orb-stage{{height:280px}} .hero{{padding:22px}}
      .message.user,.message.ai{{margin-left:0;margin-right:0}}
    }}
    </style>
    """, unsafe_allow_html=True)

inject_css(st.session_state.theme)

# ---------- Helpers ----------
def nav_button(label, icon, key):
    active = st.session_state.page == label

    if st.sidebar.button(
        f"{icon}  {label}",
        key=key,
        use_container_width=True,
        type="primary" if active else "secondary",
    ):
        st.session_state.page = label
        st.rerun()

with st.sidebar:
    st.markdown("""
    <div class="brand">
      <div class="brand-orb">✦</div>
      <div><div class="brand-title">AURA</div><div class="brand-sub">Communication Intelligence</div></div>
    </div>
    """, unsafe_allow_html=True)

    nav_button("Home", "⌂", "nav_home")
    nav_button("Workspace", "◈", "nav_workspace")
    nav_button("History", "◌", "nav_history")
    nav_button("Favorites", "☆", "nav_favorites")
    nav_button("Logs", "▣", "nav_logs")
    nav_button("Settings", "⚙", "nav_settings")

    st.sidebar.divider()
    theme_label = "☾  Dark mode" if st.session_state.theme == "light" else "☀  Light mode"
    if st.sidebar.button(theme_label, use_container_width=True, key="theme_toggle"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

    st.sidebar.markdown('<div class="tiny">Groq runs server-side • keys stay in .env</div>', unsafe_allow_html=True)

# ---------- Services ----------
agent = CommunicationAgent()
notifier = NotificationService()

def render_stats():
    logs = get_logs()
    history = get_history()
    cols = st.columns(4)
    metrics = [
        ("AI requests", st.session_state.request_count),
        ("Decisions logged", len(logs)),
        ("Saved scenarios", len(history)),
        ("Favorites", len(get_favorites())),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(f'<div class="glass-card"><div class="metric">{value}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

def run_analysis(situation, channel, audience, urgency, tone):
    if not situation.strip():
        st.warning("Describe the situation first.")
        return

    st.session_state.request_count += 1
    with st.spinner("AURA is analyzing the situation…"):
        result = agent.analyze(
            situation=situation,
            channel=channel,
            audience=audience,
            urgency=urgency,
            tone=tone,
        )
    st.session_state.last_analysis = result
    st.session_state.last_result = result
    add_to_history(result)
    add_log("ANALYZE", result)
    st.session_state.notice = "Analysis completed."
    st.rerun()

def show_result(result):
    if not result:
        return

    decision = result.get("decision", {})
    comm = result.get("communication", {})

    st.markdown("### ✦ Decision")

    st.markdown(f"""
    <div class="glass-card">
        <span class="chip">{decision.get("channel", "—")}</span>
        <span class="chip">{decision.get("urgency", "—")}</span>
        <span class="chip">{decision.get("tone", "—")}</span>
        <h3>{decision.get("title", "Recommended communication")}</h3>
        <div class="tiny">{decision.get("reason", "")}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ✉ Prepared communication")

    st.markdown(f"""
    <div class="message ai">
        <div class="message-meta">
            AURA • {comm.get("subject", "Communication")}
        </div>
        {comm.get("body", "").replace(chr(10), "<br>")}
    </div>
    """, unsafe_allow_html=True)

    recipient = st.text_input(
        "Recipient email",
        value=comm.get("recipient", "") if "@" in comm.get("recipient", "") else "",
        placeholder="example@gmail.com",
        key=f"recipient_{result.get('id', '')}"
    )

    st.markdown("### ◇ Action")

    c1, c2, c3 = st.columns(3)

    # EMAIL
    with c1:
        if st.button(
            "✉ Send Email Now",
            key=f"send_email_{result.get('id', '')}",
            use_container_width=True
        ):
            if not recipient or "@" not in recipient or "." not in recipient.split("@")[-1]:
                st.error("Enter a valid recipient email address.")
            else:
                outcome = notifier.send_email(
                    to=recipient.strip(),
                    subject=comm.get("subject", "AURA Communication"),
                    body=comm.get("body", "")
                )

                add_log("SMTP", {
                    "result": outcome,
                    "recipient": recipient.strip(),
                    "communication": comm
                })

                if outcome["ok"]:
                    st.success(outcome["message"])
                    st.toast("Email sent successfully.", icon="✉️")
                else:
                    st.error(outcome["message"])

    # PUSH
    with c2:
        if st.button(
            "🔔 Push Notification",
            key=f"send_push_{result.get('id', '')}",
            use_container_width=True
        ):
            outcome = notifier.send_push(
                title=comm.get("subject", "AURA Notification"),
                message=comm.get(
                    "short_message",
                    comm.get("body", "")
                )[:1000]
            )

            add_log("PUSHOVER", {
                "result": outcome,
                "communication": comm
            })

            if outcome["ok"]:
                st.success(outcome["message"])
            else:
                st.error(outcome["message"])

    # FAVORITE
    with c3:
        if st.button(
            "☆ Save / Favorite",
            key=f"fav_{result.get('id', '')}",
            use_container_width=True
        ):
            toggle_favorite(result.get("id", ""))
            st.success("Favorite status updated.")

    if result.get("alternatives"):
        st.markdown("### ⟡ Alternatives")

        for alt in result["alternatives"]:
            st.markdown(
                f'<span class="chip">{alt}</span>',
                unsafe_allow_html=True
            )
# ---------- Pages ----------
page = st.session_state.page

if page == "Home":
    st.markdown("""
    <div class="hero">
      <div class="hero-grid">
        <div>
          <div class="eyebrow">Intelligent Communication Assistant</div>
          <h1>Turn situations<br>into the right message.</h1>
          <p>AURA analyzes context, chooses an appropriate communication path, prepares the message, and can trigger email or push notifications through tools.</p>
          <div style="margin-top:22px">
            <span class="chip">Groq Intelligence</span>
            <span class="chip">Email Automation</span>
            <span class="chip">Push Notifications</span>
            <span class="chip">Decision Logging</span>
          </div>
        </div>
        <div class="orb-stage">
          <div class="orbit one"></div><div class="orbit two"></div><div class="orbit three"></div>
          <div class="orb"></div>
          <div class="float f1">✨</div><div class="float f2">💡</div><div class="float f3">✉️</div>
          <div class="float f4">↗</div><div class="float f5">🔔</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Quick intelligence")
    render_stats()

    st.markdown("### ✦ Start with a situation")
    q = st.text_area(
        "What happened?",
        placeholder="Example: A project deadline moved to tomorrow and the whole team needs an urgent update.",
        height=110,
        label_visibility="collapsed",
    )
    a, b, c = st.columns(3)
    with a:
        channel = st.selectbox("Preferred channel", ["Auto", "Email", "Push notification"])
    with b:
        audience = st.selectbox("Audience", ["Team", "Customer", "Manager", "Student", "General"])
    with c:
        urgency = st.selectbox("Urgency", ["Auto", "Low", "Normal", "High", "Critical"])
    tone = st.select_slider("Tone", options=["Friendly", "Professional", "Concise", "Warm", "Formal"], value="Professional")
    if st.button(
    "✦ Analyze & Prepare Communication",
    type="primary",
    use_container_width=True
):
     run_analysis(q, channel, audience, urgency, tone)

if st.session_state.last_analysis:
    show_result(st.session_state.last_analysis)
elif page == "Workspace":
    st.markdown('<div class="section-title">◈ Communication Workspace</div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, .85])
    with left:
        st.markdown('<div class="glass-card"><div class="eyebrow">Event / Request</div><h2>What should AURA handle?</h2></div>', unsafe_allow_html=True)
        situation = st.text_area("Situation", height=170, placeholder="Describe the event, people involved, deadline, and desired outcome.")
        channel = st.selectbox("Channel", ["Auto", "Email", "Push notification"])
        audience = st.selectbox("Audience type", ["Team", "Customer", "Manager", "Student", "General"])
        urgency = st.selectbox("Urgency level", ["Auto", "Low", "Normal", "High", "Critical"])
        tone = st.selectbox("Communication tone", ["Professional", "Friendly", "Concise", "Warm", "Formal"])
        if st.button("Analyze situation", type="primary", use_container_width=True):
            run_analysis(situation, channel, audience, urgency, tone)
    with right:
        st.markdown('<div class="action-card"><div style="font-size:2rem">🧠</div><h3>Decision engine</h3><div class="tiny">Groq evaluates context, urgency, audience and tone before selecting a communication action.</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="action-card"><div style="font-size:2rem">🛠️</div><h3>Tool calling</h3><div class="tiny">SMTP and Pushover are invoked only after the user chooses an action.</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="action-card"><div style="font-size:2rem">▣</div><h3>Confirmation & logs</h3><div class="tiny">Every analysis and tool result is recorded locally in the project data folder.</div></div>', unsafe_allow_html=True)
    if st.session_state.last_analysis:
        show_result(st.session_state.last_analysis)

elif page == "History":
    st.markdown('<div class="section-title">◌ Communication History</div>', unsafe_allow_html=True)
    history = get_history()
    if not history:
        st.info("No scenarios yet. Run an analysis from Home or Workspace.")
    for item in reversed(history):
        with st.expander(f'{item.get("decision",{}).get("title","Scenario")} • {item.get("created_at","")}'):
            st.write(item.get("input", {}).get("situation", ""))
            show_result(item)

elif page == "Favorites":
    st.markdown('<div class="section-title">☆ Favorites</div>', unsafe_allow_html=True)
    favorites = get_favorites()
    if not favorites:
        st.info("Your saved communication scenarios will appear here.")
    for item in reversed(favorites):
        with st.expander(item.get("decision",{}).get("title","Favorite")):
            show_result(item)

elif page == "Logs":
    st.markdown('<div class="section-title">▣ Confirmation / Tool Logs</div>', unsafe_allow_html=True)
    logs = get_logs()
    if not logs:
        st.info("No logs yet.")
    for log in reversed(logs):
        st.markdown(f"""
        <div class="glass-card" style="margin-bottom:10px">
          <span class="chip">{log.get("event","UNKNOWN")}</span>
          <span class="tiny">{log.get("timestamp","")}</span>
          <div style="margin-top:8px"><pre style="white-space:pre-wrap">{log.get("summary","")}</pre></div>
        </div>
        """, unsafe_allow_html=True)

elif page == "Settings":
    st.markdown('<div class="section-title">⚙ Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write("### Connection status")
    groq_ok = bool(os.getenv("GROQ_API_KEY"))
    smtp_ok = bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"))
    push_ok = bool(os.getenv("PUSHOVER_TOKEN") and os.getenv("PUSHOVER_USER"))
    for name, ok in [("Groq API", groq_ok), ("SMTP Email", smtp_ok), ("Pushover", push_ok)]:
        status = "Ready" if ok else "Not configured"
        st.markdown(f'<div class="status"><span class="status-dot"></span>{name}: {status}</div>', unsafe_allow_html=True)
    st.write("")
    st.caption("API keys are read only on the Streamlit server from .env. Never put secrets in frontend JavaScript or source code.")
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.notice:
    st.toast(st.session_state.notice, icon="✨")
    st.session_state.notice = None
