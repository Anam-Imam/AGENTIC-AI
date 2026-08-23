
import os
import re
import math
import json
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import TypedDict, Literal, Any

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
KNOWLEDGE_FILE = Path(__file__).with_name("knowledge.txt")

st.set_page_config(
    page_title="LUXE FLOW — Telegram AI Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# LUXE FLOW — visual system
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&family=Playfair+Display:wght@500;600;700&display=swap');

:root{
  --ivory:#fbf6ed;
  --cream:#f5ead9;
  --sand:#ead7bc;
  --champagne:#d8b989;
  --mocha:#9b7656;
  --cocoa:#704a35;
  --espresso:#2b1c15;
  --ink:#38261d;
  --line:rgba(91,61,43,.15);
}

html,body,[class*="css"]{
  font-family:'Manrope',sans-serif;
}
.stApp{
  background:
    radial-gradient(circle at 50% 20%, rgba(216,185,137,.20), transparent 28%),
    radial-gradient(circle at 15% 70%, rgba(155,118,86,.10), transparent 25%),
    var(--ivory);
  color:var(--espresso);
}
.block-container{
  max-width:1250px;
  padding-top:1.2rem;
  padding-bottom:3rem;
}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer {visibility:hidden;}

.luxe-top{
  display:flex; justify-content:space-between; align-items:center;
  padding:10px 4px 18px; border-bottom:1px solid var(--line);
}
.brand{
  font-family:'Playfair Display',serif; font-size:27px; letter-spacing:.02em;
}
.brand small{
  font-family:'DM Mono',monospace; font-size:9px; letter-spacing:.22em;
  display:block; margin-top:2px; opacity:.55;
}
.status{
  font-family:'DM Mono',monospace; font-size:10px; letter-spacing:.12em;
  border:1px solid var(--line); padding:8px 12px; border-radius:999px;
  background:rgba(255,255,255,.32);
}
.dot{
  display:inline-block; width:7px; height:7px; border-radius:50%;
  background:#8c6b50; margin-right:7px; box-shadow:0 0 14px rgba(140,107,80,.7);
}

.hero{
  text-align:center; padding:28px 0 5px;
}
.kicker{
  font-family:'DM Mono',monospace; font-size:10px; letter-spacing:.28em;
  text-transform:uppercase; opacity:.55;
}
.hero h1{
  font-family:'Playfair Display',serif; font-size:clamp(42px,7vw,82px);
  line-height:.95; margin:10px 0 12px; font-weight:600;
}
.hero p{max-width:650px;margin:auto;opacity:.65;font-size:14px;line-height:1.7;}

.bloom-wrap{
  position:relative; height:350px; display:flex; justify-content:center; align-items:center;
  overflow:hidden; margin:12px 0 5px;
}
.bloom{
  position:relative; width:210px;height:210px;border-radius:50%;
  background:
    radial-gradient(circle at 40% 35%, #fff9ef 0 8%, transparent 9%),
    radial-gradient(circle at 52% 48%, rgba(216,185,137,.9), rgba(155,118,86,.32) 38%, transparent 67%);
  box-shadow:0 0 70px rgba(216,185,137,.34), inset 0 0 35px rgba(255,255,255,.75);
  animation:breathe 5s ease-in-out infinite;
}
.bloom:before,.bloom:after{
  content:""; position:absolute; inset:-30px; border:1px solid rgba(112,74,53,.22);
  border-radius:48% 52% 45% 55%; animation:orbit 14s linear infinite;
}
.bloom:after{inset:-58px; border-color:rgba(216,185,137,.26); animation:orbit 19s linear infinite reverse;}
.core{
  position:absolute; inset:35%; border-radius:50%;
  background:radial-gradient(circle,#fffdf8,#d8b989 55%,#9b7656);
  box-shadow:0 0 28px rgba(216,185,137,.65);
}
.spark{
  position:absolute; width:5px;height:5px;border-radius:50%;background:#b18b68;
  animation:float 6s ease-in-out infinite;
}
.s1{left:20%;top:24%}.s2{right:22%;top:18%;animation-delay:1s}.s3{left:18%;bottom:22%;animation-delay:2s}
.s4{right:18%;bottom:27%;animation-delay:3s}.s5{left:49%;top:7%;animation-delay:1.5s}
@keyframes breathe{50%{transform:scale(1.08);filter:saturate(1.12)}} 
@keyframes orbit{to{transform:rotate(360deg)}} 
@keyframes float{50%{transform:translateY(-18px) scale(1.4);opacity:.45}}

.command-row{
  display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:-12px auto 22px;
}
.pill{
  padding:10px 16px;border-radius:999px;border:1px solid var(--line);
  background:rgba(255,255,255,.42);backdrop-filter:blur(12px);
  box-shadow:0 8px 25px rgba(72,48,35,.06);font-size:12px;
}
.panel{
  background:rgba(255,255,255,.38); border:1px solid var(--line);
  border-radius:26px; padding:22px; box-shadow:0 18px 60px rgba(74,49,35,.07);
  backdrop-filter:blur(18px);
}
.section-title{
  font-family:'Playfair Display',serif;font-size:24px;margin:0 0 5px;
}
.mono{
  font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;opacity:.55;
}
div[data-testid="stButton"] > button{
  border-radius:999px!important;border:1px solid rgba(91,61,43,.18)!important;
  background:rgba(255,255,255,.48)!important;color:var(--espresso)!important;
  transition:.25s!important;
}
div[data-testid="stButton"] > button:hover{
  transform:translateY(-2px);box-shadow:0 12px 28px rgba(74,49,35,.12)!important;
  border-color:rgba(91,61,43,.35)!important;
}
.stTextArea textarea,.stTextInput input{
  border-radius:20px!important;border:1px solid var(--line)!important;
  background:rgba(255,255,255,.58)!important;color:var(--espresso)!important;
}
.chat-user,.chat-ai{
  padding:15px 18px;border-radius:20px;margin:10px 0;line-height:1.65;font-size:14px;
}
.chat-user{background:#ead7bc;margin-left:16%;}
.chat-ai{background:rgba(255,255,255,.62);border:1px solid var(--line);margin-right:16%;}
.metric{
  font-family:'Playfair Display',serif;font-size:30px;margin-top:5px;
}
.footer{
  text-align:center;opacity:.45;font-size:10px;font-family:'DM Mono',monospace;
  padding:30px 0 0;letter-spacing:.1em;
}
@media(max-width:700px){
  .block-container{padding-left:1rem;padding-right:1rem;}
  .bloom-wrap{height:280px}.bloom{width:160px;height:160px}
  .chat-user,.chat-ai{margin-left:0;margin-right:0}
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Agent tools
# -----------------------------
def load_knowledge() -> str:
    if not KNOWLEDGE_FILE.exists():
        return ""
    return KNOWLEDGE_FILE.read_text(encoding="utf-8", errors="ignore")[:12000]

def calculator(expression: str) -> str:
    """Safely evaluate basic arithmetic."""
    expression = expression.replace("^", "**")
    if not re.fullmatch(r"[0-9+\-*/(). %]+", expression):
        return "Calculator only accepts basic arithmetic."
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception:
        return "I could not calculate that expression."

def choose_tool(query: str) -> Literal["knowledge", "calculator", "none"]:
    q = query.lower()
    if any(x in q for x in ["calculate", "what is", "how much is"]) and re.search(r"\d", q):
        if re.search(r"[\d][\d\s+\-*/().%^]+", q):
            return "calculator"
    knowledge = load_knowledge().strip()
    if knowledge and any(k in q for k in ["project", "telegram", "bot", "groq", "langgraph", "feature", "how does", "knowledge"]):
        return "knowledge"
    return "none"

# -----------------------------
# LangGraph agent workflow
# -----------------------------
class AgentState(TypedDict, total=False):
    query: str
    tool: str
    tool_result: str
    answer: str
    valid: bool

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """You are LUXE FLOW, a polished agentic AI assistant inside a Telegram AI studio.
Be helpful, concise, accurate and friendly. If a tool result is supplied, use it as evidence.
Never claim you used a tool when you did not. Do not expose API keys or internal implementation details.
"""

def node_analyze(state: AgentState):
    return {"tool": choose_tool(state["query"])}

def node_tool(state: AgentState):
    tool = state.get("tool", "none")
    query = state["query"]
    if tool == "knowledge":
        return {"tool_result": load_knowledge() or "No local knowledge is available."}
    if tool == "calculator":
        # Extract a likely arithmetic expression.
        match = re.search(r"([-+*/().\d\s%^]{3,})", query)
        expr = match.group(1).strip() if match else query
        return {"tool_result": calculator(expr)}
    return {"tool_result": ""}

def node_answer(state: AgentState):
    if not client:
        return {"answer": "GROQ_API_KEY is missing. Add it to your .env file first."}
    tool_result = state.get("tool_result", "")
    user_prompt = f"""User request:
{state['query']}

Tool result (may be empty):
{tool_result}

Write the best final response. If this is a Telegram message, keep it readable and reasonably concise."""
    try:
        result = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.55,
            max_tokens=900,
        )
        return {"answer": result.choices[0].message.content.strip()}
    except Exception as e:
        return {"answer": f"I couldn't complete that request right now. Error: {e}"}

def node_validate(state: AgentState):
    answer = state.get("answer", "").strip()
    return {"valid": bool(answer)}

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("analyze", node_analyze)
    graph.add_node("tool", node_tool)
    graph.add_node("answer", node_answer)
    graph.add_node("validate", node_validate)
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "tool")
    graph.add_edge("tool", "answer")
    graph.add_edge("answer", "validate")
    graph.add_edge("validate", END)
    return graph.compile()

AGENT = build_graph()

def ask_agent(query: str) -> str:
    result = AGENT.invoke({"query": query})
    return result.get("answer", "No response generated.")

# -----------------------------
# Telegram bot — kept in app.py
# -----------------------------
telegram_loop_started = False

async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✦ Welcome to LUXE FLOW.\n\nSend me a request and the agent will analyze it, use available tools, and return a refined answer."
    )

async def tg_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Try:\n• Ask a question\n• Ask me to calculate 25 * 8\n• Ask about this project\n• Ask for ideas, explanations or summaries"
    )

async def tg_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    answer = await asyncio.to_thread(ask_agent, update.message.text)
    # Telegram has a message-size limit; split long answers safely.
    for i in range(0, len(answer), 3900):
        await update.message.reply_text(answer[i:i+3900])

def run_telegram():
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", tg_start))
        app.add_handler(CommandHandler("help", tg_help))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_message))
        app.run_polling(drop_pending_updates=True, close_loop=False)
    except Exception as e:
        print("Telegram bot stopped:", e)

def start_telegram_once():
    global telegram_loop_started
    if telegram_loop_started or not TELEGRAM_BOT_TOKEN:
        return
    telegram_loop_started = True
    threading.Thread(target=run_telegram, daemon=True).start()

# -----------------------------
# Streamlit UI
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total" not in st.session_state:
    st.session_state.total = 0
if "favorites" not in st.session_state:
    st.session_state.favorites = []

start_telegram_once()

st.markdown("""
<div class="luxe-top">
  <div class="brand">LUXE FLOW<small>TELEGRAM · AGENTIC AI STUDIO</small></div>
  <div class="status"><span class="dot"></span>AGENT ONLINE</div>
</div>
<div class="hero">
  <div class="kicker">PROJECT 06 · INTELLIGENT COMMUNICATION</div>
  <h1>Ideas, in motion.</h1>
  <p>An elegant agentic workspace where Telegram requests flow through reasoning, tools, knowledge and validation before becoming a polished response.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="bloom-wrap">
  <div class="bloom"><div class="core"></div></div>
  <div class="spark s1"></div><div class="spark s2"></div><div class="spark s3"></div>
  <div class="spark s4"></div><div class="spark s5"></div>
</div>
<div class="command-row">
  <div class="pill">✦ Ask AI</div>
  <div class="pill">01 Create</div>
  <div class="pill">02 Analyze</div>
  <div class="pill">03 Explore</div>
  <div class="pill">✧ Imagine</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="panel"><div class="mono">AGENT</div><div class="metric">01</div><div>LangGraph flow</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="panel"><div class="mono">REQUESTS</div><div class="metric">{st.session_state.total:02d}</div><div>Studio interactions</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="panel"><div class="mono">TOOLS</div><div class="metric">02</div><div>Knowledge + calculator</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="panel"><div class="mono">MODEL</div><div class="metric">GQ</div><div>Groq inference</div></div>', unsafe_allow_html=True)

st.write("")

tab_chat, tab_history, tab_sources, tab_settings = st.tabs(["✦ Smart Chat", "◌ History", "⌁ Sources", "⚙ Settings"])

with tab_chat:
    st.markdown('<div class="section-title">Floating conversation</div><div class="mono">THE BLOOM REMAINS IN THE BACKGROUND</div>', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
        <div class="panel" style="margin-top:16px;text-align:center;padding:40px;">
          <div style="font-size:28px;">✦</div>
          <div style="font-family:Playfair Display,serif;font-size:25px;margin:8px;">What shall we create?</div>
          <div style="opacity:.6;font-size:13px;">Ask anything, analyze an idea, or send a Telegram-style request.</div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        cls = "chat-user" if msg["role"] == "user" else "chat-ai"
        icon = "YOU" if msg["role"] == "user" else "LUXE FLOW"
        st.markdown(f'<div class="{cls}"><div class="mono">{icon}</div>{msg["content"]}</div>', unsafe_allow_html=True)

    with st.form("composer", clear_on_submit=True):
        query = st.text_area("Message", placeholder="Ask the agent to create, analyze, explain, calculate or explore…", label_visibility="collapsed", height=90)
        send = st.form_submit_button("Send into the flow  →", use_container_width=True)

    quick1, quick2, quick3 = st.columns(3)
    if quick1.button("✦ Explain LangGraph", use_container_width=True):
        query = "Explain how LangGraph is used in this Telegram agentic AI project."
        send = True
    if quick2.button("02 Analyze project", use_container_width=True):
        query = "Analyze the architecture of this Telegram Agentic AI project."
        send = True
    if quick3.button("✧ Calculate 125 × 24", use_container_width=True):
        query = "Calculate 125 * 24"
        send = True

    if send and query and query.strip():
        q = query.strip()
        st.session_state.messages.append({"role":"user","content":q})
        with st.spinner("The bloom is thinking…"):
            answer = ask_agent(q)
        st.session_state.messages.append({"role":"assistant","content":answer})
        st.session_state.total += 1
        st.rerun()

with tab_history:
    st.markdown('<div class="section-title">History</div><div class="mono">RECENT STUDIO FLOWS</div>', unsafe_allow_html=True)
    if st.session_state.messages:
        for i, m in enumerate(st.session_state.messages, 1):
            st.markdown(f'<div class="panel" style="margin-top:10px;"><b>{i:02d}</b> · {m["role"].upper()}<br>{m["content"][:300]}</div>', unsafe_allow_html=True)
        if st.button("Clear history"):
            st.session_state.messages = []
            st.rerun()
    else:
        st.info("No conversation history yet.")

with tab_sources:
    st.markdown('<div class="section-title">Knowledge atelier</div><div class="mono">LOCAL SOURCE MATERIAL</div>', unsafe_allow_html=True)
    knowledge = load_knowledge()
    st.markdown('<div class="panel" style="margin-top:15px;">' + (knowledge.replace("\n","<br>") if knowledge else "knowledge.txt is empty.") + '</div>', unsafe_allow_html=True)

with tab_settings:
    st.markdown('<div class="section-title">Studio settings</div><div class="mono">RUNTIME CONFIGURATION</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel" style="margin-top:15px;">', unsafe_allow_html=True)
    st.write("Groq model:", MODEL)
    st.write("Groq API:", "Connected ✓" if GROQ_API_KEY else "Missing ✕")
    st.write("Telegram bot:", "Configured ✓" if TELEGRAM_BOT_TOKEN else "Missing — add TELEGRAM_BOT_TOKEN to .env")
    dark = st.toggle("Dark mode preview", value=False)
    if dark:
        st.warning("This demo keeps the warm Luxe Flow identity; a full dark variant can be added without changing the agent backend.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="footer">LUXE FLOW · LANGGRAPH · GROQ · TELEGRAM · BUILT AS A SINGLE APP</div>', unsafe_allow_html=True)
