from __future__ import annotations

import streamlit as st


def inject_css(light: bool = False) -> None:
    bg = "#F4F4F5" if light else "#07080A"
    panel = "#FFFFFF" if light else "#0D0F12"
    text = "#111217" if light else "#F4F4F5"
    muted = "#5F636D" if light else "#8B909B"
    border = "rgba(17,18,23,.12)" if light else "rgba(255,255,255,.08)"
    st.markdown(
        f"""
<style>
:root {{ --bg:{bg}; --panel:{panel}; --text:{text}; --muted:{muted}; --border:{border}; }}
html, body, [data-testid="stAppViewContainer"] {{ background: radial-gradient(circle at 50% 10%, rgba(255,255,255,.055), transparent 32%), var(--bg); color:var(--text); }}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stToolbar"] {{ visibility:hidden; }}
.block-container {{ max-width:1500px; padding-top:1rem; padding-bottom:3rem; }}
.glass {{ background:linear-gradient(145deg, rgba(255,255,255,.065), rgba(255,255,255,.018)); border:1px solid var(--border); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); box-shadow:0 24px 80px rgba(0,0,0,.25); border-radius:24px; }}
.brand {{ letter-spacing:.22em; font-size:.72rem; text-transform:uppercase; color:var(--muted); }}
.hero {{ text-align:center; padding:2rem 1rem 1rem; }}
.hero h1 {{ font-size:clamp(2.4rem,6vw,5.5rem); line-height:.95; margin:.4rem 0 1rem; letter-spacing:-.06em; font-weight:650; }}
.hero p {{ color:var(--muted); font-size:1rem; max-width:760px; margin:0 auto; }}
.pill {{ display:inline-flex; align-items:center; gap:.5rem; border:1px solid var(--border); background:rgba(255,255,255,.035); border-radius:999px; padding:.45rem .7rem; color:var(--muted); font-size:.75rem; }}
.pulse {{ width:8px; height:8px; border-radius:999px; background:#F4F4F5; box-shadow:0 0 0 0 rgba(244,244,245,.55); animation:pulse 2s infinite; }}
@keyframes pulse {{ 70% {{ box-shadow:0 0 0 12px rgba(244,244,245,0); }} 100% {{ box-shadow:0 0 0 0 rgba(244,244,245,0); }} }}
.metric {{ padding:1rem; border-radius:18px; border:1px solid var(--border); background:rgba(255,255,255,.025); }}
.metric .n {{ font-size:1.8rem; font-weight:650; }}
.metric .l {{ color:var(--muted); font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; }}
.agent-card {{ padding:1rem 1.1rem; border-radius:20px; border:1px solid var(--border); background:linear-gradient(160deg, rgba(255,255,255,.055), rgba(255,255,255,.018)); transition:transform .25s ease,border-color .25s ease; }}
.agent-card:hover {{ transform:translateY(-3px); border-color:rgba(255,255,255,.18); }}
.agent-dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:.5rem; box-shadow:0 0 18px rgba(255,255,255,.22); }}
.small {{ color:var(--muted); font-size:.82rem; }}
.result-box {{ padding:1.4rem; border-radius:24px; border:1px solid var(--border); background:linear-gradient(145deg, rgba(255,255,255,.05), rgba(255,255,255,.012)); }}
footer {{ visibility:hidden; }}
button[kind="secondary"] {{ border-radius:14px !important; border:1px solid var(--border) !important; }}
@media (max-width: 800px) {{ .hero h1 {{ font-size:3rem; }} .block-container {{ padding-left:.8rem; padding-right:.8rem; }} }}
</style>
""",
        unsafe_allow_html=True,
    )
