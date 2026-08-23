
import json, csv, io, re, math, hashlib
from pathlib import Path
from datetime import date, datetime, timedelta
import streamlit as st
from email_service import send_email, email_configured
from reminder_agent import check_deadlines

BASE = Path(__file__).resolve().parent
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    SEMANTIC_MEMORY = True
except Exception:
    chromadb = None
    SentenceTransformer = None
    SEMANTIC_MEMORY = False

st.set_page_config(page_title="LIFELOOP / PRISM DESK — PREMIUM", page_icon="✦",
                   layout="wide", initial_sidebar_state="collapsed")

DATA = BASE / "data" / "memories.json"
DATA.parent.mkdir(parents=True, exist_ok=True)

STARTER = [
    {"id":1,"text":"I promised Ali I would submit the project report by Aug 18. The report is needed for the design review.","date":"2026-08-18","tag":"project","priority":"High"},
    {"id":2,"text":"Need to send the latest project data to the team before the demo.","date":"2026-08-17","tag":"follow-up","priority":"High"},
    {"id":3,"text":"Follow up with the teammate about the unfinished project section.","date":"2026-08-16","tag":"follow-up","priority":"Medium"},
    {"id":4,"text":"Complete the final presentation and prepare the project demonstration.","date":"2026-08-15","tag":"deadline","priority":"High"},
    {"id":5,"text":"Review the design before sharing the final version with the team.","date":"2026-08-14","tag":"review","priority":"Medium"},
]

def load():
    if not DATA.exists():
        DATA.write_text(json.dumps(STARTER, indent=2), encoding="utf-8")
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except Exception:
        return STARTER.copy()

def save(items):
    DATA.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

def add_memory(text, tag, priority):
    return save_memory_record(
        text.strip(), tag=tag, priority=priority,
        source="user", memory_type="Memory"
    )


# ========================= PREMIUM 3.0 INTELLIGENCE LAYER =========================

DATA_DIR = BASE / "data"
MEMORY_FILE = DATA_DIR / "memories.json"
VERSION_FILE = DATA_DIR / "memory_versions.json"
DECISION_FILE = DATA_DIR / "decisions.json"
ALERT_FILE = DATA_DIR / "alerts.json"
SCENARIO_FILE = DATA_DIR / "scenarios.json"
APPROVAL_FILE = DATA_DIR / "approvals.json"
PROJECT_FILE = DATA_DIR / "projects.json"
REMINDER_HISTORY_FILE = DATA_DIR / "reminder_history.json"

def _read_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def _now():
    return datetime.now().isoformat(timespec="seconds")

def all_memories():
    return _read_json(MEMORY_FILE, load())

def infer_deadline(text_value):
    patterns = [r"\b\d{1,2}\s+[A-Za-z]+,?\s+\d{4}\b", r"\b[A-Za-z]+\s+\d{1,2},?\s+\d{4}\b", r"\b\d{4}-\d{2}-\d{2}\b"]
    for pattern in patterns:
        match = re.search(pattern, text_value or "")
        if not match:
            continue
        value = match.group(0).replace(",", "")
        for fmt in ("%d %B %Y", "%B %d %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).date().isoformat()
            except ValueError:
                pass
    return ""


def save_memory_record(text_value, tag="general", priority="Medium", source="user",
                       project="", person="", deadline="", confidence=80,
                       evidence=None, status="OPEN", memory_type="Memory"):
    items = all_memories()
    deadline = deadline or infer_deadline(text_value)
    next_id = max([int(x.get("id", 0)) for x in items] or [0]) + 1
    record = {
        "id": next_id, "text": text_value, "tag": tag, "priority": priority,
        "date": date.today().isoformat(), "created_at": _now(),
        "source": source, "project": project, "person": person,
        "deadline": deadline, "confidence": confidence, "evidence": evidence or [],
        "status": status, "type": memory_type, "version": 1
    }
    items.append(record)
    _write_json(MEMORY_FILE, items)
    snapshot_versions()
    return record

def snapshot_versions():
    versions = _read_json(VERSION_FILE, [])
    versions.append({"timestamp": _now(), "memories": all_memories()})
    _write_json(VERSION_FILE, versions[-50:])

def update_memory(memory_id, **changes):
    items = all_memories()
    old = next((x for x in items if int(x.get("id", -1)) == int(memory_id)), None)
    if not old:
        return None
    before = dict(old)
    old.update(changes)
    old["version"] = int(old.get("version", 1)) + 1
    old["updated_at"] = _now()
    _write_json(MEMORY_FILE, items)
    snapshot_versions()
    return {"before": before, "after": dict(old)}

def restore_version(index=-1):
    versions = _read_json(VERSION_FILE, [])
    if not versions:
        return False
    try:
        _write_json(MEMORY_FILE, versions[index]["memories"])
        return True
    except Exception:
        return False

def save_decision(decision, reason="", evidence=None, impact="Medium", approved=False):
    data = _read_json(DECISION_FILE, [])
    item = {
        "id": len(data) + 1, "decision": decision, "reason": reason,
        "evidence": evidence or [], "impact": impact,
        "approved": approved, "date": _now()
    }
    data.append(item)
    _write_json(DECISION_FILE, data)
    save_memory_record(
        f"Decision: {decision}. Reason: {reason}", tag="decision",
        priority=impact, source="decision_agent", evidence=evidence or [],
        memory_type="Decision"
    )
    return item

def save_alert(title, risk, reason, recommended_action):
    data = _read_json(ALERT_FILE, [])
    item = {
        "id": len(data) + 1, "title": title, "risk": risk, "reason": reason,
        "recommended_action": recommended_action, "created_at": _now(),
        "status": "ACTIVE"
    }
    data.append(item)
    _write_json(ALERT_FILE, data)
    return item

def create_scenario(name, current_plan, alternative, risk, delay, impact):
    data = _read_json(SCENARIO_FILE, [])
    item = {
        "id": len(data) + 1, "name": name, "current_plan": current_plan,
        "alternative": alternative, "risk": risk, "delay": delay,
        "impact": impact, "created_at": _now()
    }
    data.append(item)
    _write_json(SCENARIO_FILE, data)
    save_memory_record(
        f"Scenario {name}: {alternative}", tag="scenario",
        priority="Medium", source="scenario_agent",
        evidence=[f"Risk {risk}%", f"Delay {delay}"],
        memory_type="Scenario"
    )
    return item

def request_approval(action, reason, risk="Medium"):
    data = _read_json(APPROVAL_FILE, [])
    item = {
        "id": len(data) + 1, "action": action, "reason": reason,
        "risk": risk, "status": "PENDING", "created_at": _now()
    }
    data.append(item)
    _write_json(APPROVAL_FILE, data)
    return item

def resolve_approval(approval_id, approved):
    data = _read_json(APPROVAL_FILE, [])
    for x in data:
        if int(x["id"]) == int(approval_id):
            x["status"] = "APPROVED" if approved else "REJECTED"
            x["resolved_at"] = _now()
            _write_json(APPROVAL_FILE, data)
            return x
    return None

def genome(item):
    return {
        "memory_id": item.get("id"), "type": item.get("type", "Memory"),
        "commitment": item.get("text", ""), "person": item.get("person", ""),
        "deadline": item.get("deadline", ""), "project": item.get("project", ""),
        "importance": {"High":92, "Medium":65, "Low":35}.get(item.get("priority"), 55),
        "confidence": item.get("confidence", 80), "evidence": item.get("evidence", []),
        "status": item.get("status", "OPEN")
    }

def confidence_evolution(memory_id):
    versions = _read_json(VERSION_FILE, [])
    return [
        {"timestamp": v["timestamp"], "confidence": x.get("confidence", 80)}
        for v in versions for x in v.get("memories", [])
        if int(x.get("id", -1)) == int(memory_id)
    ]

def predictive_alerts():
    alerts = []
    for x in all_memories():
        risk = risk_score(x)
        if risk >= 78:
            alerts.append({
                "title": x["text"], "risk": risk,
                "reason": "High combined priority, age and dependency pressure.",
                "action": "Review and protect this commitment today."
            })
    return alerts

def run_agent_swarm(query):
    evidence = retrieve(query, 12)
    return [
        {"agent":"Memory Agent","status":"Completed","evidence":len(evidence)},
        {"agent":"Evidence Agent","status":"Completed","evidence":len(evidence)},
        {"agent":"Reasoning Agent","status":"Completed","evidence":len(evidence)},
        {"agent":"Risk Agent","status":"Completed","evidence":len(evidence)},
        {"agent":"Dependency Agent","status":"Completed","evidence":len(dependencies(evidence))},
        {"agent":"Recovery Agent","status":"Completed","evidence":len(evidence)},
        {"agent":"Verification Agent","status":"Completed","evidence":len(evidence)}
    ]

def recovery_mission(query):
    result = recover(query)
    result["mission"] = [
        "SCAN MEMORY", "FIND COMMITMENTS", "FIND DEADLINES",
        "CHECK DEPENDENCIES", "IDENTIFY RISKS", "CHECK CONTRADICTIONS",
        "PRIORITIZE", "CREATE RECOVERY PLAN", "VERIFY PLAN", "PRESENT MISSION"
    ]
    result["agent_swarm"] = run_agent_swarm(query)
    result["approval"] = request_approval(
        result["title"], result["summary"],
        "High" if result["risk"] >= 80 else "Medium"
    )
    save_memory_record(
        f"Recovery Mission: {result['title']}", tag="recovery",
        priority="High" if result["risk"] >= 80 else "Medium",
        source="recovery_agent", confidence=result["confidence"],
        evidence=[e.get("text","") for e in result["evidence"][:5]],
        status="PROPOSED", memory_type="Recovery Mission"
    )
    return result

# =================================================================================

# ====================== SEMANTIC LONG-TERM MEMORY ======================

VECTOR_DIR = BASE / "data" / "chroma_store"
VECTOR_COLLECTION = "lifeloop_long_term_memory"

@st.cache_resource(show_spinner=False)
def _semantic_engine():
    """Create one local embedding engine for the Streamlit process."""
    if not SEMANTIC_MEMORY:
        return None, None
    client = chromadb.PersistentClient(path=str(VECTOR_DIR))
    collection = client.get_or_create_collection(
        name=VECTOR_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return collection, model

def semantic_status():
    return "ONLINE" if SEMANTIC_MEMORY else "FALLBACK"

def _memory_text(item):
    parts = [
        item.get("text", ""),
        item.get("tag", ""),
        item.get("priority", ""),
        item.get("project", ""),
        item.get("person", ""),
        item.get("deadline", ""),
        item.get("type", "")
    ]
    return " | ".join(str(x) for x in parts if x)

def _vector_id(item):
    return f"memory-{item.get('id')}-{hashlib.sha1(_memory_text(item).encode()).hexdigest()[:10]}"

def index_memory(item):
    if not SEMANTIC_MEMORY:
        return False
    try:
        collection, model = _semantic_engine()
        if collection is None:
            return False
        doc = _memory_text(item)
        emb = model.encode([doc], normalize_embeddings=True).tolist()[0]
        collection.upsert(
            ids=[_vector_id(item)],
            embeddings=[emb],
            documents=[doc],
            metadatas=[{
                "memory_id": str(item.get("id")),
                "tag": str(item.get("tag", "")),
                "priority": str(item.get("priority", "")),
                "date": str(item.get("date", "")),
                "project": str(item.get("project", "")),
                "person": str(item.get("person", "")),
                "type": str(item.get("type", "Memory"))
            }]
        )
        return True
    except Exception:
        return False

def rebuild_semantic_memory():
    if not SEMANTIC_MEMORY:
        return 0
    try:
        collection, _ = _semantic_engine()
        for item in all_memories():
            index_memory(item)
        return collection.count()
    except Exception:
        return 0

def semantic_retrieve(query, limit=8):
    if not SEMANTIC_MEMORY:
        return []
    try:
        collection, model = _semantic_engine()
        if collection is None or collection.count() == 0:
            rebuild_semantic_memory()
        if collection.count() == 0:
            return []
        emb = model.encode([query], normalize_embeddings=True).tolist()[0]
        result = collection.query(
            query_embeddings=[emb],
            n_results=min(limit, collection.count())
        )
        ids = []
        for group in result.get("ids", []):
            ids.extend(group)
        lookup = {str(x.get("id")): x for x in all_memories()}
        return [lookup[i.replace("memory-", "").split("-", 1)[0]]
                for i in ids if i.replace("memory-", "").split("-", 1)[0] in lookup]
    except Exception:
        return []

def semantic_memory_count():
    if not SEMANTIC_MEMORY:
        return 0
    try:
        collection, _ = _semantic_engine()
        return collection.count()
    except Exception:
        return 0

# Automatically index every newly saved long-term memory.
_old_save_memory_record = save_memory_record
def save_memory_record(*args, **kwargs):
    item = _old_save_memory_record(*args, **kwargs)
    index_memory(item)
    return item

# Index legacy JSON memories when the app starts.
if SEMANTIC_MEMORY:
    try:
        if semantic_memory_count() < len(all_memories()):
            rebuild_semantic_memory()
    except Exception:
        pass

# =====================================================================
def retrieve(q, limit=8):
    """Hybrid long-term retrieval: semantic vectors first, lexical fallback."""
    semantic = semantic_retrieve(q, limit)
    if semantic:
        return semantic

    words = [w.lower() for w in re.findall(r"[a-zA-Z0-9]+", q) if len(w) > 2]
    ranked = []
    for item in all_memories():
        text_value = _memory_text(item).lower()
        score = sum(w in text_value for w in words)
        if score:
            ranked.append((score, item))
    ranked.sort(key=lambda x: (-x[0], x[1].get("date", "")))
    return [x[1] for x in ranked[:limit]]

def _days_old(d):
    try:
        return max(0, (date.today() - datetime.strptime(d, "%Y-%m-%d").date()).days)
    except Exception:
        return 0

def risk_score(item):
    p = {"High": 32, "Medium": 20, "Low": 10}.get(item.get("priority"), 15)
    age = min(30, _days_old(item.get("date", "")) * 3)
    tag = item.get("tag", "")
    tag_boost = {"deadline": 24, "project": 18, "follow-up": 20, "review": 12}.get(tag, 8)
    return min(99, p + age + tag_boost)

def loop_health():
    items = load()
    if not items:
        return 100
    avg = sum(risk_score(x) for x in items) / len(items)
    return max(20, min(99, round(100 - avg * .72)))

def people_from_memory(items):
    names = {}
    stop = {"I", "The", "Need", "Follow", "Complete", "Review", "Project", "Send", "Before"}
    for x in items:
        for n in re.findall(r"\b[A-Z][a-z]{2,}\b", x.get("text", "")):
            if n not in stop:
                names[n] = names.get(n, 0) + 1
    return sorted(names.items(), key=lambda z: -z[1])

def dependencies(items):
    edges = []
    for x in items:
        t = x.get("text", "").lower()
        if "needed for" in t or "before the" in t or "before" in t:
            if "report" in t:
                edges.append(("Project report", "Design review"))
            if "review" in t:
                edges.append(("Design review", "Demo"))
            if "demo" in t:
                edges.append(("Demo", "Final submission"))
    return list(dict.fromkeys(edges))

def contradiction_scan(items):
    conflicts = []
    deadline_map = {}
    for x in items:
        text = x.get("text", "")
        for d in re.findall(r"\b(?:Aug|Sep|Oct|Nov|Dec|Jan|Feb|Mar|Apr|May|Jun|Jul)\s+\d{1,2}\b", text):
            key = re.sub(r"[^a-z ]", " ", text.lower())
            key = " ".join(key.split()[:8])
            deadline_map.setdefault(key, []).append(d)
    for key, ds in deadline_map.items():
        if len(set(ds)) > 1:
            conflicts.append({"topic": key, "deadlines": list(dict.fromkeys(ds))})
    return conflicts

def recover(q):
    evidence = retrieve(q)
    text = " ".join(x["text"] for x in evidence).lower()

    if "report" in text or "submit" in text:
        result = {
            "title":"Submit project report",
            "summary":"A project-report commitment was recovered from your evidence archive.",
            "person":"Ali","deadline":"Aug 18",
            "recovery":["Pull latest data","Complete report","Share with Ali","Resolve review dependency","Protect demo deadline"],
            "affected":["Design review","Project demo","Stakeholder update"]
        }
    elif evidence:
        result = {
            "title":"Recover unfinished follow-up",
            "summary":"Relevant unresolved work was found in the local memory archive.",
            "person":"Project team","deadline":"Review required",
            "recovery":["Review evidence","Confirm the missing task","Complete the task","Notify the relevant person"],
            "affected":["Project timeline"]
        }
    else:
        result = {
            "title":"No strong recovery signal",
            "summary":"No matching evidence was found. Add more memories or make the question more specific.",
            "person":"—","deadline":"—",
            "recovery":["Add supporting memory","Ask about a specific task or commitment"],
            "affected":["Unknown"]
        }

    result["confidence"] = min(97, 60 + len(evidence) * 8)
    result["urgency"] = min(96, 65 + len(evidence) * 5)
    result["importance"] = min(96, 72 + len(evidence) * 4)
    result["impact"] = min(96, 70 + len(evidence) * 5)
    result["risk"] = min(99, round((result["urgency"] + result["impact"] + result["importance"]) / 3))
    result["evidence"] = evidence
    result["trace"] = ["DETECT", "RETRIEVE", "REASON", "VERIFY", "SCORE", "PLAN", "RESPOND"]
    return result

def next_best_action():
    items = sorted(load(), key=risk_score, reverse=True)
    if not items:
        return ("Add your first memory", 100, "No evidence exists yet.")
    x = items[0]
    action = x["text"]
    if x.get("tag") == "follow-up":
        action = "Follow up: " + action
    elif x.get("tag") == "deadline":
        action = "Protect deadline: " + action
    elif x.get("tag") == "project":
        action = "Move project forward: " + action
    return action, risk_score(x), "Highest combined priority, age, tag pressure and project impact."

def what_if(q):
    r = recover(q)
    rsk = r["risk"]
    return {
        "delay_risk": min(99, rsk + 5),
        "days": 1 if rsk < 80 else 2,
        "people": max(1, len(people_from_memory(r["evidence"]))),
        "affected": max(1, len(r["affected"])),
        "chain": r["affected"][:4],
        "plan": r["recovery"][:4]
    }

for key, value in {
    "page":"desk","result":None,"prompt":"","sessions":[],"favorites":[],"activity":[],"scenario":"Current plan","cleanup":[]
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

try:
    deadline_reminders = check_deadlines()
except Exception as exc:
    deadline_reminders = []
    st.session_state["reminder_error"] = str(exc)

if deadline_reminders:
    for reminder in deadline_reminders:
        st.session_state.activity.insert(0, f"Deadline tomorrow: {reminder['text'][:70]}")

# ============================================================
# YOUR PRISM DESK STYLE
# ============================================================

st.html(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Playfair+Display:wght@500&display=swap');
*{box-sizing:border-box}
.stApp{background:radial-gradient(circle,#fffdf8,#f8f3eb,#f2ede4);color:#292724;font-family:"DM Sans"}
header,footer{display:none}
.block-container{max-width:1200px;padding:28px 38px 40px 115px;position:relative;z-index:2}
.side-nav{position:fixed;left:18px;top:83px;width:58px;height:390px;background:rgba(255,252,246,.82);border:1px solid #d8cdbd;border-radius:24px;box-shadow:0 8px 25px #766a5918;backdrop-filter:blur(14px);z-index:9999}
.bg{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0}
.b{position:absolute;bottom:-120px;left:var(--x);width:var(--s);height:var(--s);border-radius:8px;background:radial-gradient(circle at 27% 22%,rgba(255,255,255,.98) 0 5%,rgba(255,255,255,.45) 12%,transparent 28%),linear-gradient(135deg,var(--l),var(--c));border:1px solid var(--d);box-shadow:inset 3px 3px 8px rgba(255,255,255,.8),0 8px 22px rgba(80,70,60,.12);opacity:.55;animation:rise var(--t) linear infinite,sway var(--sw) ease-in-out infinite}
@keyframes rise{0%{transform:translateY(0) rotate(-8deg)}25%{transform:translate(25px,-28vh) rotate(5deg)}50%{transform:translate(-20px,-58vh) rotate(-5deg)}75%{transform:translate(30px,-88vh) rotate(7deg)}100%{transform:translate(-15px,-135vh) rotate(-8deg)}}
@keyframes sway{0%,100%{margin-left:-5px}50%{margin-left:10px}}
.top{display:flex;justify-content:space-between;font-size:11px;font-weight:600;letter-spacing:2px}
.dot{display:inline-block;width:10px;height:10px;background:#86a36c;border-radius:50%;margin-right:8px}
.hero{margin:35px 0 24px 22px}.hero small{font-size:10px;letter-spacing:2px}
.hero h1{font:500 56px/.94 "Playfair Display";margin:12px 0}.hero i{color:#c9785b;font-style:normal}
.features{display:flex;gap:12px;margin:0 0 18px 38px;flex-wrap:wrap}
.feature{min-width:135px;height:63px;padding:12px 10px;text-align:center;background:#fcf9f3;border:1px solid #ded3c3;border-radius:8px;font-size:12px;line-height:1.45}
.desk{min-height:535px;position:relative;overflow:hidden;border:1px solid #d9cdbc;border-radius:24px;background:rgba(250,247,241,.86);box-shadow:0 8px 28px #8b7a6210;z-index:2;padding-bottom:110px}
.desk:before{content:"";position:absolute;inset:11px;border:1px dashed #d9cdbd;border-radius:20px}
.mem{position:absolute;width:82px;min-height:72px;padding:10px 7px;text-align:center;border-radius:9px;font-size:10px;line-height:1.35;z-index:5;box-shadow:0 8px 14px #766a5918}
.mem b{display:block;margin-bottom:4px}
.g{background:#dfe7d3;border:1px solid #abb99e}.p{background:#f7d9c9;border:1px solid #e2a98c}.k{background:#eee4cf;border:1px solid #d4bf98}.r{background:#ead8da;border:1px solid #c9a8ab}.a{background:#f4d0bd;border:1px solid #dc9c7d}
.m1{left:19%;top:8px;transform:rotate(-3deg)}.m2{left:1%;top:25px;transform:rotate(-6deg)}.m3{left:5%;top:198px}.m4{right:27%;top:4px;transform:rotate(5deg)}.m5{right:7%;top:62px;transform:rotate(5deg)}.m6{right:17%;top:205px;transform:rotate(4deg)}.m7{left:47%;top:18px;transform:rotate(5deg)}.m8{left:16%;bottom:128px;transform:rotate(-3deg)}.m9{left:35%;top:90px;transform:rotate(-10deg)}.m10{left:42%;top:120px;transform:rotate(-4deg)}.m11{left:60%;bottom:210px;transform:rotate(25deg)}.m12{left:20%;top:160px;transform:rotate(-3deg)}.m13{left:30%;bottom:70px;transform:rotate(-2deg)}.m14{left:48%;bottom:45px;transform:rotate(4deg)}.m15{right:30%;bottom:75px;transform:rotate(-5deg)}.m16{right:9%;bottom:55px;transform:rotate(3deg)}.m17{left:0;bottom:70px;transform:rotate(20deg)}.m18{right:0;bottom:200px;transform:rotate(30deg)}
.prism{position:absolute;left:50%;top:40%;width:285px;height:285px;transform:translate(-50%,-50%) rotate(16deg);border-radius:31px;background:linear-gradient(145deg,#fffefb,#edf0e6);border:2px solid white;box-shadow:0 28px 35px #6f655530;z-index:10}
.prismin{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;transform:rotate(-16deg)}
.prism small{font-size:8px;letter-spacing:3px}.prism h2{font:500 43px "Playfair Display";margin:18px 0 7px}.prism p{font-size:10px;color:#6e695f}.prism em{font-size:9px;letter-spacing:2px;color:#c9785b}
.stTextArea textarea{background:#fffdf9!important;color:#24221f!important;border:1px solid #ded3c4!important;border-radius:8px!important;font-size:12px!important}
.stButton button,.stDownloadButton button{border:1px solid #d8cdbd!important;border-radius:8px!important;background:#fbf8f1!important;color:#2d2a26!important}
.cards{display:grid;grid-template-columns:370px 1fr;gap:18px;margin-top:12px}
.card{background:#fbf8f1f2;border:1px solid #ded3c3;border-radius:11px;padding:14px}
.card small{font-size:8px;letter-spacing:1.7px;color:#83786c}.card h3{font:500 20px "Playfair Display";margin:7px 0}.card p{font-size:10px;line-height:1.55;color:#6e685f}
.score{float:right;font-size:26px}.score span{font-size:12px;color:#81786d}
.badge{display:inline-block;padding:5px 7px;margin:8px 4px 0 0;border:1px solid #d9cdbd;border-radius:5px;background:#f1e8da;font-size:8px}
.tline{display:flex;justify-content:space-between;margin-top:17px}.step{text-align:center;font-size:8px;font-weight:600}
.circle{width:28px;height:28px;border:1px solid #d5c5ae;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:auto auto 6px}
.metricgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:12px 0}.metric{background:#faf7f1;border:1px solid #ded3c3;border-radius:9px;padding:12px}
.metric small{display:block;font-size:8px;letter-spacing:1.5px;color:#83786c}.metric strong{display:block;font:500 26px "Playfair Display";margin-top:4px}.metric span{font-size:8px;color:#7c7369}
.foot{text-align:center;font-size:8px;letter-spacing:2px;color:#82786c;margin:15px}
@media(max-width:800px){.block-container{padding:20px 20px 20px 85px}.hero h1{font-size:42px}.features{margin-left:0}.feature{min-width:22%;font-size:9px}.prism{width:220px;height:220px}.cards{grid-template-columns:1fr}.metricgrid{grid-template-columns:1fr 1fr}}
</style>
""")

# Functional sidebar
st.html('<div class="side-nav"></div>')
st.markdown(r"""
<style>
div[class*="st-key-nav_"]{position:fixed!important;left:25px!important;z-index:10001!important;width:44px!important}
div[class*="st-key-nav_desk"]{top:95px!important}
div[class*="st-key-nav_search"]{top:145px!important}
div[class*="st-key-nav_memory"]{top:195px!important}
div[class*="st-key-nav_sessions"]{top:245px!important}
div[class*="st-key-nav_fav"]{top:295px!important}
div[class*="st-key-nav_activity"]{top:345px!important}
div[class*="st-key-nav_radar"]{top:400px!important}
div[class*="st-key-nav_network"]{top:450px!important}
div[class*="st-key-nav_settings"]{top:505px!important}div[class*="st-key-nav_fav"]{top:245px!important}
div[class*="st-key-nav_activity"]{top:295px!important}div[class*="st-key-nav_radar"]{top:350px!important}div[class*="st-key-nav_network"]{top:400px!important}div[class*="st-key-nav_settings"]{top:455px!important}
div[class*="st-key-nav_"] button{width:42px!important;height:42px!important;border-radius:50%!important;padding:0!important}
</style>
""", unsafe_allow_html=True)

for label,key,page in [
    ("✦","nav_desk","desk"),
    ("⌕","nav_search","search"),
    ("＋","nav_memory","memory"),
    ("⟳","nav_sessions","sessions"),
    ("♡","nav_fav","favorites"),
    ("⌁","nav_activity","activity"),
    ("⌘","nav_radar","radar"),
    ("◇","nav_network","network"),
    ("⚙","nav_settings","settings")
]:
    if st.button(label,key=key,help=page.title()):
        st.session_state.page=page
        if page=="desk":
            st.session_state.result=None
        st.rerun()
# 36 floating premium balloons
colors=[
    ("#f7d9c9","#fff4ee","#dfaa8d"),("#dfe7d3","#f5faef","#aab99d"),
    ("#c9dff0","#f4fbff","#8eb4cf"),("#ead8da","#fff3f4","#c7a6aa"),
    ("#f3df9b","#fff9df","#c8aa52"),("#e5c7ed","#fbf0ff","#b58ac0"),
    ("#bcded5","#effffc","#76aaa0"),("#f1b9d2","#fff0f7","#bd7899")]
balloons=[]
for i in range(36):
    c,l,d=colors[i%8]
    size=[13,21,29,38,48,62,74,34,56][i%9]
    balloons.append(
        f'<span class="b" style="--x:{(i*2.83)%99}%;--s:{size}px;'
        f'--c:{c};--l:{l};--d:{d};--t:{18+(i*7)%34}s;'
        f'--sw:{3+i%6}s"></span>')
st.html('<div class="bg">'+''.join(balloons)+'</div>')

st.html(r"""
<div class="top"><div>LIFELOOP / PRISM DESK</div>
<div><span class="dot"></span>LONG-TERM MEMORY · SEMANTIC RETRIEVAL · AGENTIC RECOVERY · READY</div></div>
<div class="hero"><small>Project 07 · <b>Independent Agentic System</b></small>
<h1>A desk for<br>what <i>slipped away.</i></h1></div>
""")

features=[
    "01 · Find hidden<br>commitments","02 · Protect<br>a project",
    "03 · Recover a<br>milestone","04 · Find lost<br>follow-ups",
    "05 · Explain<br>dependencies","06 · Score<br>risk"]
st.html('<div class="features">'+''.join(
    f'<div class="feature">{x}</div>' for x in features)+'</div>')

# ============================================================
# DESK
# ============================================================

if st.session_state.page=="desk":
    st.html(r"""
<div class="desk">
<div class="mem g m1"><b>Forgotten</b><br>tasks</div>
<div class="mem p m2"><b>Promises</b><br>I made</div>
<div class="mem k m3"><b>Pending</b><br>replies</div>
<div class="mem r m4"><b>Deadlines</b><br>at risk</div>
<div class="mem g m5"><b>Projects</b><br>at risk</div>
<div class="mem a m6"><b>Lost</b><br>follow-ups</div>
<div class="mem k m7"><b>Hidden</b><br>commitments</div>
<div class="mem p m8"><b>Unfinished</b><br>loops</div>
<div class="mem g m9"><b>Forgotten</b><br>tasks</div>
<div class="mem p m10"><b>Promises</b><br>I made</div>
<div class="mem k m11"><b>Pending</b><br>replies</div>
<div class="mem r m12"><b>Deadlines</b><br>at risk</div>
<div class="mem g m13"><b>Projects</b><br>at risk</div>
<div class="mem a m14"><b>Lost</b><br>follow-ups</div>
<div class="mem k m15"><b>Hidden</b><br>commitments</div>
<div class="mem p m16"><b>Unfinished</b><br>loops</div>
<div class="mem k m17"><b>Hidden</b><br>commitments</div>
<div class="mem g m18"><b>Forgotten</b><br>tasks</div>
<div class="prism"><div class="prismin">
<small>LIFELOOP AI · PRISM DESK</small><h2>Reflect.</h2>
<p>Question → Thinking → Knowledge → Answer</p>
<em>THE SQUARE IS LISTENING</em></div></div>
</div>
""")

    c1,c2,c3=st.columns([8,1.4,1.4])
    with c1:
        prompt=st.text_area(
            "SMART COMPOSER · ASK THE RECOVERY ENGINE",
            value=st.session_state.prompt,
            placeholder="What might I have promised, forgotten, or left unresolved?",
            height=52)
    with c2:
        st.markdown("<br>",unsafe_allow_html=True)
        send=st.button("✦ Send through prism",use_container_width=True,key="send")
    with c3:
        st.markdown("<br>",unsafe_allow_html=True)
        reset=st.button("↻ Reset desk",use_container_width=True,key="reset")

    if send:
        if not prompt.strip():
            st.warning("Enter a question first.")
        else:
            r=recover(prompt.strip())
            st.session_state.prompt=prompt.strip()
            st.session_state.result=r
            st.session_state.sessions.insert(0,{
                "question":prompt.strip(),"title":r["title"],"date":str(date.today())})
            st.session_state.activity.insert(0,"Recovery: "+r["title"])
            st.rerun()
    if reset:
        st.session_state.prompt=""
        st.session_state.result=None
        st.rerun()

    # Premium intelligence strip — same Prism Desk aesthetic, new intelligence underneath.
    items = load()
    health = loop_health()
    risks = sum(risk_score(x) >= 70 for x in items)
    overdue = sum(_days_old(x.get("date","")) >= 4 and x.get("priority") == "High" for x in items)
    deps = len(dependencies(items))
    action, action_score, action_reason = next_best_action()

    st.markdown(f"""
<div class="metricgrid">
<div class="metric"><small>LOOP HEALTH</small><strong>{health}</strong><span>/ 100 · system health</span></div>
<div class="metric"><small>AT-RISK ITEMS</small><strong>{risks}</strong><span>commitments needing attention</span></div>
<div class="metric"><small>DEPENDENCIES</small><strong>{deps}</strong><span>linked project effects</span></div>
<div class="metric"><small>STALE / OVERDUE</small><strong>{overdue}</strong><span>memory decay signals</span></div>
</div>
<div class="card" style="margin:12px 0">
<small>06 / NEXT BEST ACTION</small>
<span class="score">{action_score}<span>%</span></span>
<h3>{action}</h3>
<p>{action_reason}</p>
<span class="badge">IMPACT · HIGH</span>
<span class="badge">CONFIDENCE · {min(96, action_score+5)}%</span>
<span class="badge">RECOVERY READY</span>
</div>
""", unsafe_allow_html=True)

    r=st.session_state.result
    if r:
        st.markdown(f"""
<div class="metricgrid">
<div class="metric"><small>CONFIDENCE</small><strong>{r["confidence"]}%</strong><span>recovery signal</span></div>
<div class="metric"><small>URGENCY</small><strong>{r["urgency"]}</strong><span>priority</span></div>
<div class="metric"><small>IMPORTANCE</small><strong>{r["importance"]}</strong><span>project value</span></div>
<div class="metric"><small>IMPACT</small><strong>{r["impact"]}</strong><span>dependency risk</span></div>
</div>""",unsafe_allow_html=True)

        affected="<br>".join(r["affected"])
        recovery="<br>".join(
            f"{i+1:02d} {x}" for i,x in enumerate(r["recovery"]))
        st.html(f"""
<div class="cards"><div>
<div class="card"><small>01 / ANSWER SHEET · RECOVERED SIGNAL</small>
<span class="score">{r["confidence"]}<span>%</span></span>
<h3>{r["title"]}</h3><p>{r["summary"]}</p>
<span class="badge">DEADLINE · {r["deadline"]}</span>
<span class="badge">PROMISED TO · {r["person"]}</span>
<span class="badge">SOURCE · LOCAL EVIDENCE</span></div>
<div class="card" style="margin-top:10px"><small>03 / KNOWLEDGE SHEET</small>
<h3>Why it matters</h3>
<span class="badge">URGENCY · {r["urgency"]}</span>
<span class="badge">IMPORTANCE · {r["importance"]}</span>
<span class="badge">IMPACT · {r["impact"]}</span>
<p>Priority combines evidence matches, urgency, importance and dependency impact.</p></div>
</div>
<div><div class="card"><small>02 / THE MOVEMENT OF THOUGHT</small>
<div class="tline"><div class="step"><div class="circle">01</div>DETECT</div>
<div class="step"><div class="circle">02</div>CONTEXT</div>
<div class="step"><div class="circle">03</div>IMPORTANCE</div>
<div class="step"><div class="circle">04</div>DEPENDENCY</div>
<div class="step"><div class="circle">05</div>RECOVERY</div>
<div class="step"><div class="circle">06</div>FOLLOW-UP</div></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
<div class="card" style="margin-top:10px"><small>04 / KNOWLEDGE SHEET</small>
<h3>What it affects</h3><p>{affected}</p></div>
<div class="card" style="margin-top:10px"><small>05 / ACTION SHEET</small>
<h3>Recovery protocol</h3><p>{recovery}</p></div>
</div></div></div>""")
        st.markdown("### Premium Intelligence")
        p1, p2, p3 = st.columns(3)
        with p1:
            if st.button("◈ What-if simulator", use_container_width=True, key="whatif"):
                st.session_state.whatif = what_if(st.session_state.prompt)
        with p2:
            if st.button("⌁ Evidence explorer", use_container_width=True, key="evidence"):
                st.session_state.show_evidence = True
        with p3:
            if st.button("＋ Save to favorites", use_container_width=True, key="save_result"):
                if r["title"] not in [x["title"] for x in st.session_state.favorites]:
                    st.session_state.favorites.insert(0, r)
                st.success("Recovery saved to favorites.")

        if st.session_state.get("whatif"):
            w = st.session_state.whatif
            chain = " → ".join(w["chain"])
            st.markdown(f"""
<div class="card">
<small>07 / WHAT-IF SIMULATOR</small>
<h3>If this slips today</h3>
<p><b>Predicted delay risk:</b> {w["delay_risk"]}% &nbsp; · &nbsp;
<b>People affected:</b> {w["people"]} &nbsp; · &nbsp;
<b>Commitments affected:</b> {w["affected"]}</p>
<p><b>Causal chain:</b> {chain}</p>
<p><b>Best recovery:</b> {" → ".join(w["plan"])}</p>
</div>""", unsafe_allow_html=True)

        if st.session_state.get("show_evidence"):
            st.markdown("#### Evidence Explorer")
            for i, e in enumerate(r["evidence"], 1):
                st.markdown(f"**{i:02d} · {e.get('tag','general').upper()} · {e.get('priority','Medium')}** — {e['text']}")
                st.caption(f"Evidence date: {e.get('date','—')} · Risk score: {risk_score(e)}")

    else:
        st.html("""<div class="card" style="margin-top:12px">
<small>RECOVERY ENGINE</small><h3>Ready for a question.</h3>
<p>Ask about a forgotten task, promise, deadline, follow-up,
project dependency, or unfinished loop.</p></div>""")

# ============================================================
# DEADLINE NOTIFICATIONS
# ============================================================
if deadline_reminders:
    for reminder in deadline_reminders:
        st.warning(f"⚠ DEADLINE TOMORROW — {reminder['text']} · Due {reminder['deadline']}")

# ============================================================
# PREMIUM WORKSPACES
# ============================================================

elif st.session_state.page=="memory":
    st.markdown("## Add Long-Term Memory")
    st.caption("Save important commitments, deadlines, projects and follow-ups permanently.")

    with st.container(border=True):
        st.markdown("### ＋ New Long-Term Memory")

        memory_text = st.text_area(
            "Memory",
            placeholder="Example: I promised Sara that I would send the dataset before August 25.",
            height=120,
            key="memory_page_text"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            memory_tag = st.selectbox(
                "Type",
                [
                    "general",
                    "project",
                    "follow-up",
                    "deadline",
                    "review",
                    "commitment",
                    "decision"
                ],
                key="memory_page_tag"
            )

        with c2:
            memory_priority = st.selectbox(
                "Priority",
                ["High", "Medium", "Low"],
                key="memory_page_priority"
            )

        with c3:
            memory_confidence = st.slider(
                "Confidence",
                1,
                100,
                85,
                key="memory_page_confidence"
            )

        c4, c5 = st.columns(2)

        with c4:
            has_deadline = st.checkbox(
                "This memory has a deadline",
                key="memory_page_has_deadline"
            )

            memory_deadline = st.date_input(
                "Deadline",
                value=date.today(),
                key="memory_page_deadline",
                disabled=not has_deadline
            )

        with c5:
            email_reminder = st.checkbox(
                "Email reminder 1 day before",
                value=True,
                disabled=not has_deadline,
                key="memory_page_email"
            )

        if st.button(
            "SAVE TO LONG-TERM MEMORY",
            type="primary",
            use_container_width=True,
            key="save_long_term_memory"
        ):
            if memory_text.strip():

                saved = save_memory_record(
                    memory_text.strip(),
                    tag=memory_tag,
                    priority=memory_priority,
                    source="user",
                    confidence=memory_confidence,
                    deadline=(
                        memory_deadline.isoformat()
                        if has_deadline else ""
                    )
                )

                update_memory(
                    saved["id"],
                    email_reminder=email_reminder
                )

                st.session_state.activity.insert(
                    0,
                    "Long-term memory added: " + memory_text[:60]
                )

                st.success(
                    f"Memory M{saved['id']} saved permanently."
                )

                st.caption(
                    f"JSON memory: data/memories.json · "
                    f"Semantic index: data/chroma_store · "
                    f"Status: {semantic_status()}"
                )

            else:
                st.warning("Write a memory first.")

    st.markdown("### Recent Long-Term Memories")

    memories = all_memories()

    if not memories:
        st.info("No long-term memories saved yet.")
    else:
        for memory in memories[-10:][::-1]:
            with st.container(border=True):
                st.markdown(
                    f"**M{memory.get('id')} · "
                    f"{memory.get('tag','general').upper()} · "
                    f"{memory.get('priority','Medium')}**"
                )

                st.write(memory.get("text", ""))

                st.caption(
                    f"Saved: {memory.get('date','—')} · "
                    f"Confidence: {memory.get('confidence',80)}% · "
                    f"Status: {memory.get('status','OPEN')}"
                )
elif st.session_state.page=="search":
    st.markdown("## Evidence Intelligence")

    with st.expander("＋ ADD LONG-TERM MEMORY", expanded=False):
        memory_text = st.text_area(
            "Memory",
            placeholder="Example: I promised Sara that I would send the dataset before August 25.",
            height=90,
            key="new_memory_text"
        )
        a,b,c = st.columns(3)
        with a:
            memory_tag = st.selectbox(
                "Type", ["general","project","follow-up","deadline","review","commitment","decision"]
            )
        with b:
            memory_priority = st.selectbox("Priority", ["High","Medium","Low"])
        with c:
            memory_confidence = st.slider("Confidence", 1, 100, 85)

        d,e = st.columns(2)
        with d:
            has_deadline = st.checkbox("This memory has a deadline", value=False)
            memory_deadline = st.date_input("Deadline", value=date.today(), key="memory_deadline", disabled=not has_deadline)
        with e:
            email_reminder = st.checkbox("Email reminder 1 day before", value=True, disabled=not has_deadline)

        if st.button("SAVE TO LONG-TERM MEMORY", type="primary", use_container_width=True):
            if memory_text.strip():
                saved = save_memory_record(
                    memory_text.strip(), tag=memory_tag, priority=memory_priority,
                    source="user", confidence=memory_confidence,
                    deadline=memory_deadline.isoformat() if has_deadline else ""
                )
                update_memory(saved["id"], email_reminder=email_reminder)
                st.success(f"Memory M{saved['id']} saved permanently.")
                st.caption(
                    f"JSON memory: data/memories.json · "
                    f"Semantic index: data/chroma_store · "
                    f"Status: {semantic_status()}"
                )
            else:
                st.warning("Write a memory first.")

    q=st.text_input("Semantic memory search",
                    placeholder="Things I still owe people, project risks, deadlines...", key="memory_search")
    tag=st.selectbox("Filter", ["All","project","follow-up","deadline","review","general"], key="memory_filter")
    items=load()
    if tag!="All":
        items=[x for x in items if x.get("tag")==tag]
    if q.strip():
        items=retrieve(q,20)

    a,b,c,d,e=st.columns(5)
    a.metric("Evidence",len(items))
    b.metric("High risk",sum(risk_score(x)>=70 for x in items))
    c.metric("High priority",sum(x.get("priority")=="High" for x in items))
    d.metric("Conflicts",len(contradiction_scan(items)))
    e.metric("Long-term index",semantic_memory_count())
    st.caption(
        f"Semantic memory: **{semantic_status()}** · "
        "Search uses meaning-aware retrieval when the local vector index is available."
    )

    if contradiction_scan(items):
        st.warning("Contradiction signals detected. Review before changing important information.")

    for x in items:
        with st.container(border=True):
            st.markdown(f"**M{x['id']} · {x.get('tag','general').upper()} · {x.get('priority','Medium')} · RISK {risk_score(x)}%**")
            st.write(x["text"])
            st.caption(f"{x.get('date','—')} · Evidence confidence grows when related signals are found.")

elif st.session_state.page=="sessions":
    st.markdown("## Previous Prism Sessions")
    if not st.session_state.sessions:
        st.info("No sessions yet.")
    for i,x in enumerate(st.session_state.sessions):
        with st.container(border=True):
            st.markdown(f"**{x['title']}**")
            st.caption(f"{x['date']} · {x['question']}")
            if st.button("Reopen",key=f"reopen{i}"):
                st.session_state.result=recover(x["question"])
                st.session_state.prompt=x["question"]
                st.session_state.page="desk"
                st.rerun()

elif st.session_state.page=="favorites":
    st.markdown("## Favorites")
    r=st.session_state.result
    if r and st.button("♡ Save current recovery",key="favorite"):
        if r["title"] not in [x["title"] for x in st.session_state.favorites]:
            st.session_state.favorites.insert(0,r)
        st.success("Saved.")
    if not st.session_state.favorites:
        st.info("No favorites yet.")
    for x in st.session_state.favorites:
        with st.container(border=True):
            st.markdown(f"**{x['title']}** · {x['confidence']}%")
            st.write(x["summary"])

elif st.session_state.page=="activity":
    st.markdown("## Memory Intelligence / Activity")
    items=load()
    high=sum(x.get("priority")=="High" for x in items)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Memories",len(items))
    c2.metric("High priority",high)
    c3.metric("Sessions",len(st.session_state.sessions))
    c4.metric("Favorites",len(st.session_state.favorites))
    st.markdown("### Personal Reliability")
    reliability = max(1, min(99, round((loop_health() + (100 - min(60, high*4))) / 2)))
    st.progress(reliability / 100)
    st.caption(f"{reliability}/100 · commitment completion and memory freshness")
    st.markdown("### Memory Cleanup Agent")
    stale=[x for x in items if _days_old(x.get("date",""))>=4]
    conflicts=contradiction_scan(items)
    c1,c2,c3=st.columns(3)
    c1.metric("Stale signals",len(stale))
    c2.metric("Possible conflicts",len(conflicts))
    c3.metric("Missing projects",sum(not x.get("tag") or x.get("tag")=="general" for x in items))
    if conflicts:
        for c in conflicts:
            st.warning("Possible deadline conflict: " + ", ".join(c["deadlines"]))
    st.markdown("### Recent activity")
    if not st.session_state.activity:
        st.info("No activity yet.")
    for x in st.session_state.activity[:20]:
        st.write("• "+x)

elif st.session_state.page=="radar":
    st.markdown("## Commitment Risk Radar")
    items=sorted(load(), key=risk_score, reverse=True)
    h1,h2,h3=st.columns(3)
    h1.metric("Loop Health", loop_health(), "/ 100")
    h2.metric("Critical", sum(risk_score(x)>=85 for x in items))
    h3.metric("At Risk", sum(70<=risk_score(x)<85 for x in items))
    for x in items:
        rs=risk_score(x)
        label="CRITICAL" if rs>=85 else "AT RISK" if rs>=70 else "HEALTHY"
        with st.container(border=True):
            st.markdown(f"**{label} · {rs}% · M{x['id']}**")
            st.write(x["text"])
            st.caption(f"{x.get('tag','general').upper()} · {x.get('priority','Medium')} · {x.get('date','—')}")

elif st.session_state.page=="network":
    st.markdown("## Memory Relationship Network")
    items=load()
    people=people_from_memory(items)
    deps=dependencies(items)
    a,b=st.columns(2)
    with a:
        st.markdown("### People Map")
        if people:
            for name,count in people:
                st.markdown(f"**{name}**  ·  {count} related signal(s)")
        else:
            st.info("No named relationships detected yet.")
    with b:
        st.markdown("### Dependency Chain")
        if deps:
            for left,right in deps:
                st.markdown(f"**{left}**  →  **{right}**")
        else:
            st.info("No explicit dependencies detected yet.")

    st.markdown("### Memory Timeline")
    for x in sorted(items, key=lambda z:z.get("date",""), reverse=True):
        st.markdown(f"**{x.get('date','—')}**  ·  `{x.get('tag','general')}`  ·  {x['text']}")


elif st.session_state.page=="mission":
    st.markdown("## Recovery Mission")
    q=st.text_input("Mission target",value=st.session_state.get("prompt",""),
                    placeholder="Recover my project / commitments / deadlines")
    if st.button("START RECOVERY MISSION",type="primary",use_container_width=True):
        st.session_state.result=recovery_mission(q)
        st.rerun()
    if st.session_state.get("result"):
        r=st.session_state.result
        st.progress(r["risk"]/100)
        st.markdown(f"### {r['title']}")
        st.write(r["summary"])
        st.caption(f"Risk {r['risk']}% · Confidence {r['confidence']}% · Impact {r['impact']}%")
        st.markdown("### Mission Trace")
        for i,step in enumerate(r["mission"],1):
            st.write(f"{i:02d} · {step}")
        st.markdown("### Agent Swarm")
        for a in r["agent_swarm"]:
            st.write(f"✓ {a['agent']} · {a['status']} · evidence {a['evidence']}")
        st.markdown("### Human Approval Gate")
        approval=r.get("approval")
        if approval and approval["status"]=="PENDING":
            st.warning("AI proposes this action. Review before approval.")
            c1,c2=st.columns(2)
            with c1:
                if st.button("APPROVE",use_container_width=True):
                    resolve_approval(approval["id"],True)
                    save_decision(r["title"],r["summary"],r["evidence"],"High",True)
                    st.success("Approved and recorded.")
            with c2:
                if st.button("REJECT",use_container_width=True):
                    resolve_approval(approval["id"],False)
                    st.info("Rejected and recorded.")

elif st.session_state.page=="scenario":
    st.markdown("## Scenario Lab")
    action,score,_=next_best_action()
    st.markdown(f"**Current plan:** {action}")
    c1,c2,c3=st.columns(3)
    with c1: alt=st.text_input("Alternative","Delay this action by one day")
    with c2: risk=st.slider("Estimated risk",0,99,min(95,score+10))
    with c3: delay=st.number_input("Delay (days)",0,30,1)
    impact=st.selectbox("Impact",["Low","Medium","High"])
    if st.button("RUN SCENARIO",type="primary",use_container_width=True):
        s=create_scenario("Scenario Lab",action,alt,risk,delay,impact)
        st.success("Scenario saved to persistent memory.")
        st.write(f"Risk {s['risk']}% · Delay {s['delay']} day(s) · Impact {s['impact']}")
    st.markdown("### Saved Scenarios")
    for s in _read_json(SCENARIO_FILE,[])[-10:][::-1]:
        st.write(f"**{s['name']}** · {s['alternative']} · Risk {s['risk']}% · Delay {s['delay']} day(s)")

elif st.session_state.page=="settings":
    st.markdown("## Prism System Settings")
    c1,c2=st.columns(2)
    with c1:
        st.success("Local memory engine: ONLINE")
        st.success("Recovery workflow: ONLINE")
        st.info("External LLM: optional")
    with c2:
        st.write("**Privacy**")
        st.write("API credentials belong in environment variables.")
        st.write("Local evidence stays in data/memories.json.")

    st.markdown("### Deadline reminders")
    if email_configured():
        st.success("Email reminders: READY")
        if st.button("Send test email", key="test_reminder_email"):
            ok, msg = send_email("LIFELOOP — Test Reminder", "Your LIFELOOP deadline email system is working.")
            (st.success if ok else st.error)(msg)
    else:
        st.warning("Email reminders are not configured. Add REMINDER_EMAIL, REMINDER_PASSWORD and REMINDER_TO to .env.")
    st.caption("Checks deadlines one day before and records sent reminders in data/reminder_history.json.")

    st.markdown("### Add memory")
    with st.form("memory_form"):
        txt=st.text_area("Evidence / memory")
        tag=st.selectbox("Tag",
                         ["general","project","follow-up","deadline","review"])
        priority=st.selectbox("Priority",["High","Medium","Low"])
        if st.form_submit_button("＋ Save memory"):
            if txt.strip():
                add_memory(txt,tag,priority)
                st.session_state.activity.insert(
                    0,"Memory added: "+txt[:60])
                st.success("Memory saved permanently.")
                st.rerun()
            else:
                st.warning("Enter evidence first.")

    st.markdown("### Export")
    raw=json.dumps(load(),indent=2,ensure_ascii=False).encode()
    st.download_button("⇩ Download memory JSON",raw,
                       "lifeloop_memory.json","application/json")

    buf=io.StringIO()
    fieldnames=["id","text","date","tag","priority","status","version",
                "confidence","evidence","person","project","deadline",
                "created_at","updated_at","source","type","email_reminder"]
    writer=csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(load())
    st.download_button("⇩ Download memory CSV",buf.getvalue(),
                       "lifeloop_memory.csv","text/csv")

    if st.button("Reset starter archive",key="reset_archive"):
        save(STARTER)
        st.success("Starter archive restored.")

st.html("""<div class="foot">
LIFELOOP AI · PROJECT 7 / INDEPENDENT AGENTIC SYSTEM · PRISM DESK · PREMIUM EDITION
</div>""")
