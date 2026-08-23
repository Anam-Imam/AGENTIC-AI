import json
import uuid
from datetime import datetime
import streamlit as st

from utils.document_loader import load_document
from core.processor import DocumentProcessor
from core.config import GROQ_MODEL

st.set_page_config(page_title="AURELIA", page_icon="✦", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []
if "current" not in st.session_state:
    st.session_state.current = None

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*{font-family:Inter,sans-serif}
.stApp{background:radial-gradient(circle at 80% 5%,rgba(112,96,220,.14),transparent 28%),#0a0b0e;color:#f4f4f5}
section[data-testid="stSidebar"]{background:#101115;border-right:1px solid #282b33}
.block-container{max-width:1250px;padding-top:2.2rem}
.hero h1{font-size:clamp(2.6rem,5vw,4.8rem);line-height:1.02;letter-spacing:-.055em}
.muted{color:#92959f}
.kicker{font-size:.72rem;letter-spacing:.15em;color:#aaa5d7;font-weight:700}
.card{background:linear-gradient(145deg,#1a1c22,#101115);border:1px solid #292c34;border-radius:20px;padding:22px;transition:.2s}
.card:hover{transform:translateY(-3px);border-color:#41444e}
.orb{width:125px;height:125px;border-radius:50%;margin:28px auto 35px;background:radial-gradient(circle at 32% 27%,#fff 0 6%,#b8b0ff 16%,#7769dc 38%,#282542 64%,#111318 79%);box-shadow:0 0 55px rgba(119,105,220,.34);animation:breathe 3.7s ease-in-out infinite}
@keyframes breathe{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
.result{background:#101216;border:1px solid #292c34;border-radius:22px;padding:26px}
.badge{display:inline-block;padding:5px 10px;border-radius:99px;border:1px solid #4b437f;background:#17152b;color:#c3bdff;font-size:.74rem}
.source{background:#15171c;border:1px solid #292c34;border-radius:14px;padding:14px;margin:8px 0;color:#b9bbc2}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ✦ AURELIA")
    st.caption("AUTOMATED DOCUMENT INTELLIGENCE")
    st.divider()

    if "page" not in st.session_state:
        st.session_state.page = "Home"

    page = st.radio(
        "WORKSPACE",
        ["Home", "Process", "History", "Analytics"],
        key="page",
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("**SYSTEM STATUS**")
    st.caption("● Groq · Connected")
    st.caption("● ChromaDB · Ready")
    st.caption("● Pydantic · Active")
    st.caption(f"● {GROQ_MODEL}")
    st.divider()
    st.caption("AURELIA v1.0 · Project 4")

def go_to_process():
    st.session_state.page = "Process"

if page == "Home":
    st.markdown("""
    <div class="hero">
      <div class="kicker">DOCUMENT INTELLIGENCE SYSTEM</div>
      <h1>Turn documents into<br>structured intelligence.</h1>
      <p class="muted">Parse. Retrieve. Extract. Validate. Re-process. Transform everyday documents into reliable structured results.</p>
    </div>
    <div class="orb"></div>
    """, unsafe_allow_html=True)

    a,b,c = st.columns(3)
    with a:
        st.markdown('<div class="card"><div class="kicker">RETRIEVAL</div><h2>ChromaDB</h2><span class="muted">Context-aware document</span></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card"><div class="kicker">INTELLIGENCE</div><h2>Groq LLM</h2><span class="muted">Fast structured extraction</span></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="card"><div class="kicker">VALIDATION</div><h2>Pydantic</h2><span class="muted">Schema-controlled output</span></div>', unsafe_allow_html=True)

    st.write("")
    st.subheader("Quick actions")
if st.button(
    "✦ Process a document",
    type="primary",
    use_container_width=True,
    on_click=go_to_process
):
    st.rerun()

elif page == "Process":
    st.markdown('<div class="kicker">PROCESSING WORKSPACE</div><h1>Analyze a document</h1>', unsafe_allow_html=True)
    st.write("Upload → parse → chunk → retrieve → extract → validate → re-process if needed → structured output.")

    uploaded = st.file_uploader("Drop PDF, DOCX or TXT here", type=["pdf","docx","txt"])
    instruction = st.text_area("Extraction focus (optional)", placeholder="Example: Extract invoice number, customer, dates, totals, and action items.")

    if uploaded:
        st.markdown(f'<div class="card"><span class="badge">READY</span><h3>{uploaded.name}</h3><span class="muted">{uploaded.size/1024:.1f} KB</span></div>', unsafe_allow_html=True)
        st.write("")
        if st.button("✦ Run intelligent processing", type="primary", use_container_width=True):
            try:
                with st.status("Running AURELIA pipeline...", expanded=True) as status:
                    st.write("Parsing document")
                    text = load_document(uploaded)
                    st.write("Chunking and indexing in ChromaDB")
                    processor = DocumentProcessor()
                    st.write("Retrieving relevant context")
                    st.write("Calling Groq extraction agent")
                    output = processor.process(text, str(uuid.uuid4()), uploaded.name, instruction)
                    st.write("Validating with Pydantic schema")
                    status.update(label="Pipeline complete", state="complete")

                record = {"name":uploaded.name, "time":datetime.now().strftime("%Y-%m-%d %H:%M"), "output":output}
                st.session_state.current = record
                st.session_state.history.append(record)
                st.rerun()
            except Exception as e:
                st.error(str(e))
                st.info("Check your .env file and GROQ_API_KEY.")

    if st.session_state.current:
        o = st.session_state.current["output"]
        r = o["result"]
        st.divider()
        st.markdown("## Structured intelligence")
        st.markdown(f'<span class="badge">{"VALIDATED" if o["valid"] else "VALIDATION WARNING"}</span>', unsafe_allow_html=True)
        st.write("")
        a,b,c,d = st.columns(4)
        a.metric("Type", r.document_type)
        b.metric("Confidence", f"{r.confidence:.0%}")
        c.metric("Chunks", o["chunks"])
        d.metric("Attempts", len(o["attempts"]))

        st.markdown(f'<div class="result"><div class="kicker">EXTRACTED RESULT</div><h2>{r.title}</h2><p class="muted">{r.summary}</p></div>', unsafe_allow_html=True)
        left,right = st.columns(2)
        with left:
            st.subheader("Key entities")
            for x in r.key_entities or ["None found"]:
                st.write("•",x)
            st.subheader("Important dates")
            for x in r.important_dates or ["None found"]:
                st.write("•",x)
        with right:
            st.subheader("Important amounts")
            for x in r.important_amounts or ["None found"]:
                st.write("•",x)
            st.subheader("Action items")
            for x in r.action_items or ["None found"]:
                st.write("☐",x)

        if o["issues"]:
            st.warning("Validation feedback: " + " | ".join(o["issues"]))

        st.subheader("Pipeline attempts")
        for x in o["attempts"]:
            st.write(("✓" if x["valid"] else "↻"), f"Attempt {x['attempt']}: " + ("Valid" if x["valid"] else "Re-process"))

        with st.expander("Sources / RAG context"):
            for i,x in enumerate(o["sources"],1):
                st.markdown(f'<div class="source"><b>Source chunk {i}</b><br>{x}</div>', unsafe_allow_html=True)

        st.download_button("↓ Download structured JSON", json.dumps(r.model_dump(),indent=2,ensure_ascii=False), "aurelia_result.json", "application/json", use_container_width=True)

elif page == "History":
    st.markdown('<div class="kicker">WORKSPACE MEMORY</div><h1>Processing history</h1>', unsafe_allow_html=True)
    if not st.session_state.history:
        st.info("No documents processed in this session.")
    for item in reversed(st.session_state.history):
        r=item["output"]["result"]
        st.markdown(f'<div class="card"><b>{item["name"]}</b><br><span class="muted">{item["time"]} · {r.document_type} · confidence {r.confidence:.0%}</span></div>', unsafe_allow_html=True)
        st.write("")

elif page == "Analytics":
    st.markdown('<div class="kicker">SYSTEM INSIGHTS</div><h1>Analytics</h1>', unsafe_allow_html=True)
    total=len(st.session_state.history)
    valid=sum(x["output"]["valid"] for x in st.session_state.history)
    avg=sum(x["output"]["result"].confidence for x in st.session_state.history)/total if total else 0
    a,b,c=st.columns(3)
    a.metric("Documents",total)
    b.metric("Validated",valid)
    c.metric("Avg confidence",f"{avg:.0%}")
    st.write("")
    for step in ["01 · Upload & parse","02 · Chunk & index","03 · Chroma retrieval","04 · Groq extraction","05 · Pydantic validation","06 · Automatic re-processing","07 · Structured output"]:
        st.markdown(f'<div class="card" style="margin-bottom:10px">✓ &nbsp; {step}</div>', unsafe_allow_html=True)
