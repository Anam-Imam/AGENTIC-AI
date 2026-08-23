from __future__ import annotations

import json
from html import escape

import streamlit as st
import streamlit.components.v1 as components


def ai_core(state: str = "idle") -> None:
    label = {"idle": "STANDBY", "thinking": "THINKING", "responding": "RESPONDING", "error": "ERROR"}.get(state, "STANDBY")
    html = f"""
<!doctype html><html><head><style>
*{{box-sizing:border-box}} body{{margin:0;background:transparent;font-family:Inter,system-ui,sans-serif;color:#f4f4f5;overflow:hidden}}
.wrap{{height:470px;display:grid;place-items:center;position:relative}}
.core{{width:240px;height:240px;border-radius:50%;position:relative;display:grid;place-items:center;background:radial-gradient(circle at 35% 28%,#fff, #cfd2d7 13%,#777d87 34%,#292d34 60%,#0a0b0d 100%);box-shadow:0 0 55px rgba(255,255,255,.12), inset -30px -25px 55px rgba(0,0,0,.55), inset 20px 15px 35px rgba(255,255,255,.18);animation:breathe 4.5s ease-in-out infinite;z-index:3}}
.core:after{{content:"";position:absolute;inset:22px;border-radius:50%;border:1px solid rgba(255,255,255,.2);box-shadow:inset 0 0 35px rgba(255,255,255,.08)}}
.orbit{{position:absolute;width:330px;height:140px;border:1px solid rgba(255,255,255,.17);border-radius:50%;transform:rotate(-18deg);animation:spin 8s linear infinite}}
.orbit.o2{{width:390px;height:170px;transform:rotate(58deg);animation-duration:11s;animation-direction:reverse;opacity:.7}}
.orbit.o3{{width:460px;height:210px;transform:rotate(2deg);animation-duration:16s;opacity:.32}}
.sphere-label{{position:relative;z-index:5;text-align:center;letter-spacing:.2em;font-size:11px;color:#1a1b1f;font-weight:700}}
.sphere-label b{{display:block;font-size:20px;letter-spacing:.11em}}
.halo{{position:absolute;width:560px;height:560px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.06),transparent 60%);filter:blur(20px);animation:halo 6s ease-in-out infinite}}
.particle{{position:absolute;width:3px;height:3px;border-radius:50%;background:#fff;opacity:.7;animation:float 5s ease-in-out infinite}}
.p1{{left:18%;top:30%}} .p2{{right:15%;top:38%;animation-delay:-1.2s}} .p3{{left:26%;bottom:26%;animation-delay:-2s}} .p4{{right:24%;bottom:21%;animation-delay:-3.3s}}
@keyframes spin{{to{{transform:rotate(342deg)}}}} @keyframes breathe{{50%{{transform:scale(1.035);box-shadow:0 0 85px rgba(255,255,255,.18),inset -30px -25px 55px rgba(0,0,0,.55),inset 20px 15px 35px rgba(255,255,255,.2)}}}}
@keyframes halo{{50%{{transform:scale(1.12);opacity:.7}}}} @keyframes float{{50%{{transform:translateY(-18px) translateX(8px);opacity:1}}}}
.thinking .core{{animation:breathe .9s ease-in-out infinite}} .thinking .orbit{{animation-duration:2.4s}} .responding .core{{box-shadow:0 0 110px rgba(255,255,255,.24),inset -30px -25px 55px rgba(0,0,0,.5)}}
@media(max-width:700px){{.wrap{{height:380px}}.core{{width:190px;height:190px}}.orbit{{width:270px;height:120px}}.orbit.o2{{width:320px;height:140px}}.orbit.o3{{width:380px;height:170px}}.halo{{width:430px;height:430px}}}}
</style></head><body>
<div class="wrap {state}"><div class="halo"></div><div class="orbit"></div><div class="orbit o2"></div><div class="orbit o3"></div>
<div class="particle p1"></div><div class="particle p2"></div><div class="particle p3"></div><div class="particle p4"></div>
<div class="core"><div class="sphere-label"><b>AI</b>{escape(label)}</div></div></div>
</body></html>
"""
    components.html(html, height=490, scrolling=False)


def agent_cards(status: dict[str, str]) -> None:
    cards = [
        ("research", "AGENT A", "RESEARCH", "External facts + references"),
        ("analysis", "AGENT B", "ANALYSIS", "Reasoning + synthesis"),
        ("execution", "AGENT C", "EXECUTION", "Action + implementation"),
    ]
    cols = st.columns(3)
    for col, key, name, role, sub in [(cols[i], *cards[i]) for i in range(3)]:
        value = status.get(key, "standby")
        with col:
            st.markdown(
                f'<div class="agent-card"><div class="small"><span class="agent-dot"></span>{role}</div>'
                f'<h3 style="margin:.35rem 0 .25rem">{name}</h3><div class="small">{sub}</div>'
                f'<div style="margin-top:.85rem;font-size:.72rem;letter-spacing:.1em;color:#A7ABB5">{value.upper()}</div></div>',
                unsafe_allow_html=True,
            )


def render_sources(sources: list[dict[str, str]]) -> None:
    if not sources:
        return
    st.markdown("#### Sources")
    for source in sources:
        label = escape(source.get("label", "Source"))
        url = source.get("url", "")
        if url:
            st.markdown(f"- [{label}]({url})")
        else:
            st.markdown(f"- {label}")


def compact_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
