from __future__ import annotations

import csv
import io
import json
import re
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from deen_ai.prayer_agent import (
    get_prayer_summary,
    get_city_prayer_summary,
)

from deen_ai.deen_utils import (
    next_prayer,
    countdown,
)

from deen_ai.quran_agent import search_quran

from deen_ai.research_agent import research



# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="LIFELOOP / PRISM DESK",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# APP / DATA
# ============================================================

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

MEMORY_FILE = DATA_DIR / "memories.json"
VERSION_FILE = DATA_DIR / "memory_versions.json"
SCENARIO_FILE = DATA_DIR / "scenarios.json"
DECISION_FILE = DATA_DIR / "decisions.json"
APPROVAL_FILE = DATA_DIR / "approvals.json"
ACTIVITY_FILE = DATA_DIR / "activity.json"


# ============================================================
# STARTER MEMORY
# ============================================================

STARTER = [
    {
        "id": 1,
        "text": "I promised Ali I would submit the Project 7 report by August 18, 2026. The report is needed for the design review.",
        "date": "2026-08-18",
        "tag": "commitment",
        "priority": "High",
        "person": "Ali",
        "project": "Project 7",
        "deadline": "2026-08-18",
        "status": "OPEN",
        "confidence": 92,
        "source": "starter",
        "type": "Commitment",
        "evidence": [
            "Explicit promise",
            "Explicit deadline",
        ],
        "created_at": "2026-08-18T09:00:00",
        "version": 1,
    },
    {
        "id": 2,
        "text": "Send the latest Project 7 data to the team before the demo.",
        "date": "2026-08-17",
        "tag": "follow-up",
        "priority": "High",
        "person": "team",
        "project": "Project 7",
        "deadline": "",
        "status": "OPEN",
        "confidence": 84,
        "source": "starter",
        "type": "Follow-up",
        "evidence": [
            "Follow-up statement",
        ],
        "created_at": "2026-08-17T09:00:00",
        "version": 1,
    },
    {
        "id": 3,
        "text": "Complete the final presentation and prepare the Project 7 demonstration.",
        "date": "2026-08-15",
        "tag": "deadline",
        "priority": "High",
        "person": "",
        "project": "Project 7",
        "deadline": "",
        "status": "OPEN",
        "confidence": 88,
        "source": "starter",
        "type": "Deadline",
        "evidence": [
            "Project milestone",
        ],
        "created_at": "2026-08-15T09:00:00",
        "version": 1,
    },
    {
        "id": 4,
        "text": "Review the design before sharing the final version with the team.",
        "date": "2026-08-14",
        "tag": "review",
        "priority": "Medium",
        "person": "team",
        "project": "Project 7",
        "deadline": "",
        "status": "OPEN",
        "confidence": 78,
        "source": "starter",
        "type": "Review",
        "evidence": [
            "Review dependency",
        ],
        "created_at": "2026-08-14T09:00:00",
        "version": 1,
    },
]


# ============================================================
# JSON HELPERS
# ============================================================

def read_json(path: Path, default):
    try:
        if path.exists():
            value = json.loads(path.read_text(encoding="utf-8"))
            return value
    except Exception:
        pass

    return default


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def memories():
    if not MEMORY_FILE.exists():
        write_json(MEMORY_FILE, STARTER)

    value = read_json(MEMORY_FILE, STARTER)

    return value if isinstance(value, list) else []


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def snapshot():
    versions = read_json(VERSION_FILE, [])

    versions.append(
        {
            "timestamp": now_iso(),
            "memories": memories(),
        }
    )

    write_json(
        VERSION_FILE,
        versions[-50:],
    )


# ============================================================
# DEADLINE
# ============================================================

def infer_deadline(text: str):
    patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b",
    ]

    formats = [
        "%Y-%m-%d",
        "%B %d %Y",
        "%d %B %Y",
        "%b %d %Y",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text or "",
            flags=re.I,
        )

        if match:
            raw = match.group(0).replace(",", "")

            for fmt in formats:
                try:
                    return datetime.strptime(
                        raw,
                        fmt,
                    ).date().isoformat()
                except ValueError:
                    pass

    return ""


# ============================================================
# MEMORY OPERATIONS
# ============================================================

def save_memory(
    text,
    tag="general",
    priority="Medium",
    project="",
    person="",
    deadline="",
    confidence=80,
    source="user",
    memory_type="Memory",
    evidence=None,
):
    items = memories()

    next_id = (
        max(
            [
                int(x.get("id", 0))
                for x in items
            ]
            or [0]
        )
        + 1
    )

    record = {
        "id": next_id,
        "text": text.strip(),
        "date": date.today().isoformat(),
        "tag": tag,
        "priority": priority,
        "person": person,
        "project": project,
        "deadline": deadline or infer_deadline(text),
        "status": "OPEN",
        "confidence": int(confidence),
        "source": source,
        "type": memory_type,
        "evidence": evidence or [],
        "created_at": now_iso(),
        "version": 1,
    }

    items.append(record)

    write_json(
        MEMORY_FILE,
        items,
    )

    snapshot()

    return record


def update_memory(memory_id, **changes):
    items = memories()

    for item in items:
        if int(item.get("id", -1)) == int(memory_id):

            item.update(changes)

            item["version"] = (
                int(item.get("version", 1)) + 1
            )

            item["updated_at"] = now_iso()

            write_json(
                MEMORY_FILE,
                items,
            )

            snapshot()

            return item

    return None


def delete_memory(memory_id):
    items = memories()

    remaining = [
        x
        for x in items
        if int(x.get("id", -1)) != int(memory_id)
    ]

    if len(remaining) == len(items):
        return False

    write_json(
        MEMORY_FILE,
        remaining,
    )

    snapshot()

    return True


def delete_all_memories():
    write_json(
        MEMORY_FILE,
        [],
    )

    snapshot()

    return True


def restore_starter():
    write_json(
        MEMORY_FILE,
        STARTER,
    )

    snapshot()


# ============================================================
# MEMORY ANALYSIS
# ============================================================

def _days_old(value):
    try:
        return max(
            0,
            (
                date.today()
                - datetime.strptime(
                    value,
                    "%Y-%m-%d",
                ).date()
            ).days,
        )
    except Exception:
        return 0


def risk_score(item):
    if item.get("status") in {
        "DONE",
        "COMPLETED",
    }:
        return 8

    base = {
        "High": 34,
        "Medium": 22,
        "Low": 10,
    }.get(
        item.get("priority"),
        15,
    )

    age = min(
        28,
        _days_old(
            item.get("date", "")
        )
        * 3,
    )

    tag = {
        "deadline": 22,
        "commitment": 24,
        "follow-up": 20,
        "project": 18,
        "review": 12,
    }.get(
        item.get("tag"),
        7,
    )

    deadline_boost = (
        15
        if item.get("deadline")
        else 0
    )

    return min(
        99,
        base
        + age
        + tag
        + deadline_boost,
    )


def loop_health():
    items = memories()

    if not items:
        return 100

    avg = sum(
        risk_score(x)
        for x in items
    ) / len(items)

    return max(
        20,
        min(
            99,
            round(
                100 - avg * 0.72
            ),
        ),
    )


def keyword_retrieve(query, limit=10):
    words = [
        w.lower()
        for w in re.findall(
            r"[A-Za-z0-9]+",
            query,
        )
        if len(w) > 2
    ]

    scored = []

    for item in memories():

        text = " ".join(
            str(item.get(k, ""))
            for k in [
                "text",
                "tag",
                "project",
                "person",
                "deadline",
                "type",
            ]
        ).lower()

        score = sum(
            1
            for word in words
            if word in text
        )

        if score:
            scored.append(
                (
                    score,
                    risk_score(item),
                    item,
                )
            )

    scored.sort(
        key=lambda x: (
            -x[0],
            -x[1],
        )
    )

    return [
        x[2]
        for x in scored[:limit]
    ]


# ============================================================
# DEPENDENCIES / PEOPLE
# ============================================================

def dependencies(items):
    edges = []

    for item in items:

        t = item.get(
            "text",
            "",
        ).lower()

        if (
            "needed for" in t
            or "before" in t
            or "depends on" in t
        ):

            if "report" in t:
                edges.append(
                    (
                        "Project report",
                        "Design review",
                    )
                )

            if "review" in t:
                edges.append(
                    (
                        "Design review",
                        "Demo",
                    )
                )

            if "demo" in t:
                edges.append(
                    (
                        "Demo",
                        "Final submission",
                    )
                )

        if (
            item.get("project")
            and item.get("tag")
            == "follow-up"
        ):
            edges.append(
                (
                    item.get(
                        "text",
                        "Follow-up",
                    )[:30],
                    f'{item.get("project")} timeline',
                )
            )

    return list(
        dict.fromkeys(edges)
    )


def people_from_memory(items):
    counts = {}

    for item in items:

        person = str(
            item.get(
                "person",
                "",
            )
        ).strip()

        if person:
            counts[person] = (
                counts.get(
                    person,
                    0,
                )
                + 1
            )

        for name in re.findall(
            r"\b[A-Z][a-z]{2,}\b",
            item.get(
                "text",
                "",
            ),
        ):

            if name not in {
                "Project",
                "Complete",
                "Review",
                "Before",
                "August",
                "January",
                "February",
            }:

                counts[name] = (
                    counts.get(
                        name,
                        0,
                    )
                    + 1
                )

    return sorted(
        counts.items(),
        key=lambda x: -x[1],
    )


# ============================================================
# INTELLIGENCE
# ============================================================

def contradiction_scan(items):
    groups = {}

    for item in items:

        text = item.get(
            "text",
            "",
        ).lower()

        subject = re.sub(
            r"\b\d{4}-\d{2}-\d{2}\b",
            "DATE",
            text,
        )

        subject = re.sub(
            r"\b(?:aug|sep|oct|nov|dec|jan|feb|mar|apr|may|jun|jul)\w*\s+\d{1,2},?\s+\d{4}\b",
            "DATE",
            subject,
        )

        if item.get("deadline"):

            key = " ".join(
                subject.split()[:10]
            )

            groups.setdefault(
                key,
                [],
            ).append(
                item.get(
                    "deadline"
                )
            )

    return [
        {
            "topic": k,
            "deadlines": list(
                dict.fromkeys(v)
            ),
        }
        for k, v in groups.items()
        if len(set(v)) > 1
    ]


def promise_radar(items):
    patterns = [
        r"\bi['’]?ll\b",
        r"\bpromised\b",
        r"\bpromise\b",
        r"\bneed to\b",
        r"\bremind me\b",
        r"\bi have to\b",
        r"\bi must\b",
    ]

    hits = []

    for item in items:

        text = item.get(
            "text",
            "",
        )

        if any(
            re.search(
                p,
                text,
                re.I,
            )
            for p in patterns
        ):
            hits.append(item)

    return hits


def genome(item):
    return {
        "memory_id": item.get("id"),
        "type": item.get(
            "type",
            "Memory",
        ),
        "commitment": item.get(
            "text",
            "",
        ),
        "person": item.get(
            "person",
            "",
        ),
        "deadline": item.get(
            "deadline",
            "",
        ),
        "project": item.get(
            "project",
            "",
        ),
        "importance": {
            "High": 92,
            "Medium": 65,
            "Low": 35,
        }.get(
            item.get("priority"),
            55,
        ),
        "confidence": item.get(
            "confidence",
            80,
        ),
        "evidence": item.get(
            "evidence",
            [],
        ),
        "status": item.get(
            "status",
            "OPEN",
        ),
    }


# ============================================================
# RECOVERY ENGINE
# ============================================================

def recovery_engine(query):

    evidence = keyword_retrieve(
        query,
        10,
    )

    if not evidence:
        evidence = sorted(
            memories(),
            key=risk_score,
            reverse=True,
        )[:3]

    if not evidence:

        return {
            "title": "No strong recovery signal",
            "summary": (
                "No saved evidence is available yet. "
                "Add a memory or make the question more specific."
            ),
            "person": "—",
            "deadline": "—",
            "recovery": [
                "Add supporting memory",
                "Ask about a specific commitment or project",
            ],
            "affected": [
                "Unknown"
            ],
            "evidence": [],
            "confidence": 45,
            "urgency": 35,
            "importance": 40,
            "impact": 30,
            "risk": 25,
            "trace": [
                "DETECT",
                "RETRIEVE",
                "VERIFY",
                "RESPOND",
            ],
        }

    top = evidence[0]

    r = risk_score(top)

    tag = top.get(
        "tag",
        "general",
    )

    if tag in {
        "commitment",
        "deadline",
    }:
        title = (
            "Protect the highest-risk commitment"
        )

    elif tag == "follow-up":
        title = (
            "Recover the unresolved follow-up"
        )

    elif tag == "project":
        title = (
            "Move the project forward"
        )

    else:
        title = (
            "Recover the most relevant loop"
        )

    affected = [
        f"{a} → {b}"
        for a, b in dependencies(
            evidence
        )
    ][:4]

    if not affected:
        affected = [
            "Project timeline"
        ]

    recovery = [
        "Review the strongest evidence",
        f'Confirm: {top.get("text", "")[:90]}',
        "Complete or unblock the item",
        "Notify the relevant person",
        "Verify completion and update memory",
    ]

    return {
        "title": title,
        "summary": (
            f"LIFELOOP recovered {len(evidence)} "
            "relevant evidence signal(s) and ranked "
            "the highest-pressure item for action."
        ),
        "person": (
            top.get("person")
            or "Not explicitly recorded"
        ),
        "deadline": (
            top.get("deadline")
            or "Not explicitly recorded"
        ),
        "recovery": recovery,
        "affected": affected,
        "evidence": evidence,
        "confidence": min(
            97,
            62 + len(evidence) * 5,
        ),
        "urgency": min(
            97,
            50 + r // 2,
        ),
        "importance": min(
            97,
            55
            + (
                20
                if top.get("priority")
                == "High"
                else 8
            ),
        ),
        "impact": min(
            97,
            50 + len(affected) * 8,
        ),
        "risk": r,
        "trace": [
            "DETECT",
            "RETRIEVE",
            "REASON",
            "RISK",
            "DEPENDENCY",
            "RECOVERY",
            "VERIFY",
            "RESPOND",
        ],
    }


def what_if(
    query,
    delay_days=1,
):

    r = recovery_engine(query)

    new_risk = min(
        99,
        r["risk"]
        + delay_days * 6
        + (
            5
            if r["risk"] >= 70
            else 0
        ),
    )

    return {
        "delay_days": delay_days,
        "current_risk": r["risk"],
        "projected_risk": new_risk,
        "people": len(
            people_from_memory(
                r["evidence"]
            )
        ),
        "affected": len(
            r["affected"]
        ),
        "chain": r["affected"],
        "plan": r["recovery"][:4],
    }


def next_best_action():

    items = sorted(
        [
            x
            for x in memories()
            if x.get("status")
            not in {
                "DONE",
                "COMPLETED",
            }
        ],
        key=risk_score,
        reverse=True,
    )

    if not items:
        return (
            "Add your first memory",
            100,
            "No open evidence exists.",
        )

    x = items[0]

    return (
        x.get(
            "text",
            "Review your open work.",
        ),
        risk_score(x),
        (
            "Highest combined priority, age, "
            "deadline pressure and dependency impact."
        ),
    )


# ============================================================
# RECOVERY MISSION
# ============================================================

def recovery_mission(query):

    r = recovery_engine(query)

    r["mission"] = [
        "SCAN MEMORY",
        "FIND COMMITMENTS",
        "FIND DEADLINES",
        "CHECK DEPENDENCIES",
        "IDENTIFY RISKS",
        "CHECK CONTRADICTIONS",
        "PRIORITIZE",
        "CREATE RECOVERY PLAN",
        "VERIFY PLAN",
        "PRESENT MISSION",
    ]

    r["agents"] = [
        (
            "Memory Agent",
            len(r["evidence"]),
        ),
        (
            "Evidence Agent",
            len(r["evidence"]),
        ),
        (
            "Risk Agent",
            1,
        ),
        (
            "Dependency Agent",
            len(r["affected"]),
        ),
        (
            "Reasoning Agent",
            1,
        ),
        (
            "Recovery Agent",
            len(r["recovery"]),
        ),
        (
            "Verification Agent",
            1,
        ),
    ]

    approvals = read_json(
        APPROVAL_FILE,
        [],
    )

    approval = {
        "id": len(approvals) + 1,
        "title": r["title"],
        "status": "PENDING",
        "created_at": now_iso(),
    }

    approvals.append(approval)

    write_json(
        APPROVAL_FILE,
        approvals,
    )

    r["approval"] = approval

    return r


# ============================================================
# ACTIVITY
# ============================================================

def save_activity(text):

    data = read_json(
        ACTIVITY_FILE,
        [],
    )

    data.insert(
        0,
        {
            "text": text,
            "time": now_iso(),
        },
    )

    write_json(
        ACTIVITY_FILE,
        data[:100],
    )


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "desk",
    "prompt_input": "",
    "result": None,
    "sessions": [],
    "favorites": [],
    "activity": [],
    "whatif": None,
    "show_evidence": False,
    "confirm_delete_all": False,
    "deen_section": "prayer",
    "deen_prayer": None,
    "deen_quran": None,
    "deen_research": None,
    "prayer_mode": "City",
    "research_running": False,
}

for key, value in DEFAULTS.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# PREMIUM PRISM CSS
# ============================================================

st.html(
    r"""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Playfair+Display:wght@500&display=swap');

*{
    box-sizing:border-box;
}

.stApp{
    background:
        radial-gradient(
            circle at 50% 20%,
            #fffdf8,
            #f8f3eb,
            #f2ede4
        );
    color:#292724;
    font-family:"DM Sans",sans-serif;
}

header,
footer{
    display:none;
}

.block-container{
    max-width:1200px;
    padding:28px 38px 40px 115px;
    position:relative;
    z-index:2;
}


/* ============================================================
   FIXED PREMIUM SIDEBAR
   ============================================================ */

.side-shell{
    position:fixed;
    left:18px;
    top:50%;
    transform:translateY(-50%);
    width:58px;
    padding:9px 7px;
    display:flex;
    flex-direction:column;
    align-items:center;
    gap:7px;

    background:rgba(255,252,246,.94);
    border:1px solid #d8cdbd;
    border-radius:24px;

    box-shadow:
        0 8px 25px #766a5918;

    backdrop-filter:blur(14px);

    z-index:9999;
}


/* Navigation button wrapper */

div[class*="st-key-nav_"]{
    position:fixed!important;

    left:25px!important;

    width:44px!important;
    height:44px!important;

    z-index:10001!important;
}


/* Navigation buttons */

div[class*="st-key-nav_"] button{
    width:42px!important;
    height:42px!important;

    min-width:42px!important;
    min-height:42px!important;

    padding:0!important;

    border-radius:50%!important;

    border:1px solid transparent!important;

    background:transparent!important;

    color:#4b4741!important;

    font-size:18px!important;

    display:flex!important;
    align-items:center!important;
    justify-content:center!important;

    transition:
        .18s ease!important;
}

div[class*="st-key-nav_"] button:hover{
    background:#eee7dc!important;
    border-color:#d8cdbd!important;
    transform:scale(1.06);
}


/* ============================================================
   CENTERED SIDEBAR POSITIONS
   ============================================================ */

div[class*="st-key-nav_desk"]{
    top:calc(50% - 275px)!important;
}

div[class*="st-key-nav_search"]{
    top:calc(50% - 225px)!important;
}

div[class*="st-key-nav_memory"]{
    top:calc(50% - 175px)!important;
}

div[class*="st-key-nav_sessions"]{
    top:calc(50% - 125px)!important;
}

div[class*="st-key-nav_fav"]{
    top:calc(50% - 75px)!important;
}

div[class*="st-key-nav_activity"]{
    top:calc(50% - 25px)!important;
}

div[class*="st-key-nav_radar"]{
    top:calc(50% + 25px)!important;
}

div[class*="st-key-nav_network"]{
    top:calc(50% + 75px)!important;
}

div[class*="st-key-nav_mission"]{
    top:calc(50% + 125px)!important;
}

div[class*="st-key-nav_deen"]{
    top:calc(50% + 175px)!important;
}

div[class*="st-key-nav_settings"]{
    top:calc(50% + 225px)!important;
}


/* ============================================================
   FLOATING BACKGROUND
   ============================================================ */

.bg{
    position:fixed;
    inset:0;
    overflow:hidden;
    pointer-events:none;
    z-index:0;
}

.b{
    position:absolute;
    bottom:-120px;
    left:var(--x);

    width:var(--s);
    height:var(--s);

    border-radius:8px;

    background:
        radial-gradient(
            circle at 27% 22%,
            rgba(255,255,255,.98) 0 5%,
            rgba(255,255,255,.45) 12%,
            transparent 28%
        ),
        linear-gradient(
            135deg,
            var(--l),
            var(--c)
        );

    border:1px solid var(--d);

    box-shadow:
        inset 3px 3px 8px rgba(255,255,255,.8),
        inset -5px -6px 10px rgba(80,70,50,.08),
        0 8px 22px rgba(80,70,50,.08);

    opacity:.62;

    animation:
        rise var(--t) linear infinite,
        sway var(--sw) ease-in-out infinite;
}

.b:before{
    content:"";

    position:absolute;

    width:32%;
    height:32%;

    left:15%;
    top:12%;

    border-radius:50%;

    background:rgba(255,255,255,.7);

    filter:blur(2px);
}

@keyframes rise{

    0%{
        transform:
            translateY(0)
            rotate(-8deg);
    }

    25%{
        transform:
            translate(25px,-28vh)
            rotate(5deg);
    }

    50%{
        transform:
            translate(-20px,-58vh)
            rotate(-5deg);
    }

    75%{
        transform:
            translate(30px,-88vh)
            rotate(7deg);
    }

    100%{
        transform:
            translate(-15px,-135vh)
            rotate(-8deg);
    }
}

@keyframes sway{

    0%,100%{
        margin-left:-5px;
    }

    50%{
        margin-left:10px;
    }
}


/* ============================================================
   HEADER
   ============================================================ */

.top{
    display:flex;
    justify-content:space-between;

    font-size:11px;

    font-weight:600;

    letter-spacing:2px;
}

.dot{
    display:inline-block;

    width:10px;
    height:10px;

    background:#86a36c;

    border-radius:50%;

    margin-right:8px;
}


/* ============================================================
   HERO
   ============================================================ */

.hero{
    margin:35px 0 28px 22px;
}

.hero small{
    font-size:10px;
    letter-spacing:2px;
}

.hero h1{
    font:
        500 56px/.94
        "Playfair Display";

    margin:12px 0;
}

.hero i{
    color:#c9785b;
    font-style:normal;
}


/* ============================================================
   FEATURE CARDS
   ============================================================ */

.features{
    display:flex;
    gap:9px;

    margin:
        0 0 18px 38px;

    flex-wrap:wrap;
}

.feature{
    width:135px;
    min-height:63px;

    padding:12px 8px;

    text-align:center;

    background:#fcf9f3;

    border:1px solid #ded3c3;

    border-radius:8px;

    font-size:12px;

    line-height:1.45;
}


/* ============================================================
   DESK
   ============================================================ */

.desk{
    min-height:430px;

    position:relative;

    overflow:hidden;

    border:
        1px solid #d9cdbc;

    border-radius:24px;

    background:
        rgba(250,247,241,.86);

    box-shadow:
        0 8px 28px #8b7a6210;

    z-index:2;
}

.desk:before{
    content:"";

    position:absolute;

    inset:11px;

    border:
        1px dashed #d9cdbd;

    border-radius:20px;

    pointer-events:none;
}


/* ============================================================
   MEMORY FLOATING CARDS
   ============================================================ */

.mem{
    position:absolute;

    width:82px;

    min-height:72px;

    padding:10px 7px;

    text-align:center;

    border-radius:9px;

    font-size:10px;

    line-height:1.35;

    z-index:5;

    box-shadow:
        0 8px 14px #766a5918;
}

.mem b{
    display:block;
    margin-bottom:4px;
}

.g{
    background:#dfe7d3;
    border:1px solid #abb99e;
}

.p{
    background:#f7d9c9;
    border:1px solid #e2a98c;
}

.k{
    background:#eee4cf;
    border:1px solid #d4bf98;
}

.r{
    background:#ead8da;
    border:1px solid #c9a8ab;
}

.a{
    background:#f4d0bd;
    border:1px solid #dc9c7d;
}

.m1{
    left:19%;
    top:8px;
    transform:rotate(-3deg);
}

.m2{
    left:1%;
    top:25px;
    transform:rotate(-6deg);
}

.m3{
    left:5%;
    top:198px;
}

.m4{
    right:27%;
    top:4px;
    transform:rotate(5deg);
}

.m5{
    right:7%;
    top:62px;
    transform:rotate(5deg);
}

.m6{
    right:17%;
    top:205px;
    transform:rotate(4deg);
}

.m7{
    left:47%;
    top:18px;
    transform:rotate(5deg);
}

.m8{
    left:16%;
    bottom:40px;
    transform:rotate(-3deg);
}

.m9{
    left:35%;
    top:90px;
    transform:rotate(-10deg);
}

.m10{
    left:42%;
    top:120px;
    transform:rotate(-4deg);
}

.m11{
    left:60%;
    bottom:120px;
    transform:rotate(25deg);
}

.m12{
    left:20%;
    top:160px;
    transform:rotate(-3deg);
}

.m13{
    left:30%;
    bottom:30px;
    transform:rotate(-2deg);
}

.m14{
    left:48%;
    bottom:20px;
    transform:rotate(4deg);
}

.m15{
    right:30%;
    bottom:35px;
    transform:rotate(-5deg);
}

.m16{
    right:9%;
    bottom:25px;
    transform:rotate(3deg);
}

.m17{
    left:0;
    bottom:40px;
    transform:rotate(20deg);
}

.m18{
    right:0;
    bottom:120px;
    transform:rotate(30deg);
}


/* ============================================================
   PRISM
   ============================================================ */

.prism{
    position:absolute;

    left:50%;
    top:42%;

    width:270px;
    height:270px;

    transform:
        translate(-50%,-50%)
        rotate(16deg);

    border-radius:31px;

    background:
        linear-gradient(
            145deg,
            #fffefb,
            #edf0e6
        );

    border:2px solid white;

    box-shadow:
        0 28px 35px #6f655530;

    z-index:10;
}

.prismin{
    height:100%;

    display:flex;

    flex-direction:column;

    align-items:center;

    justify-content:center;

    text-align:center;

    transform:rotate(-16deg);
}

.prism small{
    font-size:8px;
    letter-spacing:3px;
}

.prism h2{
    font:
        500 43px
        "Playfair Display";

    margin:18px 0 7px;
}

.prism p{
    font-size:10px;
    color:#6e695f;
}

.prism em{
    font-size:9px;
    letter-spacing:2px;
    color:#c9785b;
}


/* ============================================================
   CARDS
   ============================================================ */

.card{
    background:#fbf8f1f2;

    border:
        1px solid #ded3c3;

    border-radius:11px;

    padding:14px;

    position:relative;

    z-index:3;

    margin-top:10px;
}

.card small{
    font-size:8px;
    letter-spacing:1.7px;
    color:#83786c;
}

.card h3{
    font:
        500 20px
        "Playfair Display";

    margin:7px 0;
}

.card p{
    font-size:11px;
    line-height:1.55;
    color:#6e685f;
}

.score{
    float:right;
    font-size:26px;
}

.score span{
    font-size:12px;
    color:#81786d;
}

.badge{
    display:inline-block;

    padding:5px 7px;

    margin:
        8px 4px 0 0;

    border:
        1px solid #d9cdbd;

    border-radius:5px;

    background:#f1e8da;

    font-size:8px;
}


/* ============================================================
   METRICS
   ============================================================ */

.metricgrid{
    display:grid;

    grid-template-columns:
        repeat(4,1fr);

    gap:9px;

    margin:12px 0;
}

.metric{
    background:#faf7f1;

    border:
        1px solid #ded3c3;

    border-radius:9px;

    padding:12px;
}

.metric small{
    display:block;

    font-size:8px;

    letter-spacing:1.5px;

    color:#83786c;
}

.metric strong{
    display:block;

    font:
        500 26px
        "Playfair Display";

    margin-top:4px;
}

.metric span{
    font-size:8px;
    color:#7c7369;
}


/* ============================================================
   GENERAL
   ============================================================ */

.section-title{
    font:
        500 30px
        "Playfair Display";
}

.deen-hero{
    padding:20px;

    border:
        1px solid #d8cdbd;

    border-radius:18px;

    background:
        linear-gradient(
            135deg,
            #faf7ef,
            #f0eadf
        );

    margin-bottom:14px;
}

.deen-card{
    background:
        rgba(252,249,243,.92);

    border:
        1px solid #ddd1c0;

    border-radius:14px;

    padding:16px;
}

.stButton button{
    border:
        1px solid #d8cdbd!important;

    border-radius:
        8px!important;

    background:
        #fbf8f1!important;

    color:
        #2d2a26!important;
}

.stButton button:hover{
    background:
        #eee7dc!important;
}

.stTextArea textarea,
.stTextInput input{
    background:
        #fffdf9!important;

    color:
        #24221f!important;

    border:
        1px solid #ded3c4!important;

    border-radius:
        8px!important;
}

.foot{
    text-align:center;

    font-size:8px;

    letter-spacing:2px;

    color:#82786c;

    margin:15px;
}


/* ============================================================
   MOBILE
   ============================================================ */

@media(max-width:800px){

    .block-container{
        padding:
            20px
            20px
            20px
            82px;
    }

    .hero h1{
        font-size:42px;
    }

    .features{
        margin-left:0;
    }

    .feature{
        width:29%;
        font-size:9px;
    }

    .prism{
        width:210px;
        height:210px;
    }

    .metricgrid{
        grid-template-columns:
            1fr 1fr;
    }

}

</style>
"""
)


# ============================================================
# FLOATING BACKGROUND
# ============================================================

colors = [
    (
        "#f7d9c9",
        "#fff4ee",
        "#dfaa8d",
    ),
    (
        "#dfe7d3",
        "#f5faef",
        "#aab99d",
    ),
    (
        "#c9dff0",
        "#f4fbff",
        "#8eb4cf",
    ),
    (
        "#ead8da",
        "#fff3f4",
        "#c7a6aa",
    ),
    (
        "#f3df9b",
        "#fff9df",
        "#c8aa52",
    ),
    (
        "#e5c7ed",
        "#fbf0ff",
        "#b58ac0",
    ),
    (
        "#bcded5",
        "#effffc",
        "#76aaa0",
    ),
    (
        "#f1b9d2",
        "#fff0f7",
        "#bd7899",
    ),
]


balloons = []

for i in range(32):

    c, l, d = colors[
        i % len(colors)
    ]

    size = [
        13,
        21,
        29,
        38,
        48,
        62,
        74,
        34,
        56,
    ][i % 9]

    balloons.append(
        f"""
        <span
            class="b"
            style="
                --x:{(i * 3.1) % 99}%;
                --s:{size}px;
                --c:{c};
                --l:{l};
                --d:{d};
                --t:{18 + (i * 7) % 34}s;
                --sw:{3 + i % 6}s;
            ">
        </span>
        """
    )


st.html(
    '<div class="bg">'
    + "".join(balloons)
    + "</div>"
)


# ============================================================
# CUSTOM SIDEBAR
# ============================================================

st.html(
    '<div class="side-shell"></div>'
)


nav = [
    (
        "✦",
        "nav_desk",
        "desk",
        "Prism Desk",
    ),
    (
        "⌕",
        "nav_search",
        "search",
        "Evidence Search",
    ),
    (
        "＋",
        "nav_memory",
        "memory",
        "Long-Term Memory",
    ),
    (
        "⟳",
        "nav_sessions",
        "sessions",
        "Previous Sessions",
    ),
    (
        "♡",
        "nav_fav",
        "favorites",
        "Favorites",
    ),
    (
        "⌁",
        "nav_activity",
        "activity",
        "Activity",
    ),
    (
        "⌘",
        "nav_radar",
        "radar",
        "Risk Radar",
    ),
    (
        "◇",
        "nav_network",
        "network",
        "People & Dependencies",
    ),
    (
        "◈",
        "nav_mission",
        "mission",
        "Recovery Mission",
    ),
    (
        "☾",
        "nav_deen",
        "deen",
        "Deen AI",
    ),
    (
        "⚙",
        "nav_settings",
        "settings",
        "Settings",
    ),
]


for label, key, page, help_text in nav:

    if st.button(
        label,
        key=key,
        help=help_text,
    ):

        st.session_state.page = page

        st.session_state.show_evidence = False

        st.session_state.whatif = None

        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.html(
    """
    <div class="top">
        <div>
            LIFELOOP / PRISM DESK
        </div>

        <div>
            <span class="dot"></span>
            LONG-TERM MEMORY · AGENTIC RECOVERY ·
            DEEN INTELLIGENCE · READY
        </div>
    </div>
    """
)


# ============================================================
# DESK HEADER
# ============================================================

if st.session_state.page == "desk":

    st.html(
        """
        <div class="hero">
            <small>
                Project 07 ·
                <b>Independent Agentic System</b>
            </small>

            <h1>
                A desk for<br>
                what <i>slipped away.</i>
            </h1>
        </div>
        """
    )

    features = [
        "01 · Find hidden<br>commitments",
        "02 · Protect<br>a project",
        "03 · Recover a<br>milestone",
        "04 · Find lost<br>follow-ups",
        "05 · Explain<br>dependencies",
        "06 · Score<br>risk",
    ]

    st.html(
        '<div class="features">'
        + "".join(
            f'<div class="feature">{x}</div>'
            for x in features
        )
        + "</div>"
    )


# ============================================================
# DESK
# ============================================================

if st.session_state.page == "desk":

    st.html(
        r"""
        <div class="desk">

            <div class="mem g m1">
                <b>Forgotten</b><br>
                tasks
            </div>

            <div class="mem p m2">
                <b>Promises</b><br>
                I made
            </div>

            <div class="mem k m3">
                <b>Pending</b><br>
                replies
            </div>

            <div class="mem r m4">
                <b>Deadlines</b><br>
                at risk
            </div>

            <div class="mem g m5">
                <b>Projects</b><br>
                at risk
            </div>

            <div class="mem a m6">
                <b>Lost</b><br>
                follow-ups
            </div>

            <div class="mem k m7">
                <b>Hidden</b><br>
                commitments
            </div>

            <div class="mem p m8">
                <b>Unfinished</b><br>
                loops
            </div>

            <div class="mem g m9">
                <b>Forgotten</b><br>
                tasks
            </div>

            <div class="mem p m10">
                <b>Promises</b><br>
                I made
            </div>

            <div class="mem k m11">
                <b>Pending</b><br>
                replies
            </div>

            <div class="mem r m12">
                <b>Deadlines</b><br>
                at risk
            </div>

            <div class="mem g m13">
                <b>Projects</b><br>
                at risk
            </div>

            <div class="mem a m14">
                <b>Lost</b><br>
                follow-ups
            </div>

            <div class="mem k m15">
                <b>Hidden</b><br>
                commitments
            </div>

            <div class="mem p m16">
                <b>Unfinished</b><br>
                loops
            </div>

            <div class="mem k m17">
                <b>Hidden</b><br>
                commitments
            </div>

            <div class="mem g m18">
                <b>Forgotten</b><br>
                tasks
            </div>

            <div class="prism">

                <div class="prismin">

                    <small>
                        LIFELOOP AI · PRISM DESK
                    </small>

                    <h2>
                        Reflect.
                    </h2>

                    <p>
                        Question → Thinking →
                        Knowledge → Answer
                    </p>

                    <em>
                        THE SQUARE IS LISTENING
                    </em>

                </div>

            </div>

        </div>
        """
    )


    # ========================================================
    # SMART COMPOSER
    # ========================================================

    c1, c2, c3 = st.columns(
        [
            8,
            1.4,
            1.4,
        ]
    )

    with c1:

        st.text_area(
            "SMART COMPOSER · ASK THE RECOVERY ENGINE",
            placeholder=(
                "What might I have promised, "
                "forgotten, or left unresolved?"
            ),
            height=70,
            key="prompt_input",
        )

    with c2:

        st.html(
            "<br>"
)

        if st.button(
            "✦ Send through prism",
            use_container_width=True,
            key="send_prism",
        ):

            query = (
                st.session_state
                .prompt_input
                .strip()
            )

            if not query:

                st.warning(
                    "Enter a question first."
                )

            else:

                result = recovery_engine(
                    query
                )

                st.session_state.result = result

                st.session_state.sessions.insert(
                    0,
                    {
                        "question": query,
                        "title": result[
                            "title"
                        ],
                        "date": str(
                            date.today()
                        ),
                    },
                )

                st.session_state.sessions = (
                    st.session_state.sessions[:50]
                )

                save_activity(
                    "Recovery: "
                    + result["title"]
                )

                st.rerun()

    with c3:

        st.html(
            "<br>"
)

        if st.button(
            "↻ Reset desk",
            use_container_width=True,
            key="reset_desk",
        ):

            st.session_state.prompt_input = ""

            st.session_state.result = None

            st.session_state.whatif = None

            st.session_state.show_evidence = False

            st.rerun()


    # ========================================================
    # DESK METRICS
    # ========================================================

    items = memories()

    health = loop_health()

    risks = sum(
        risk_score(x) >= 70
        for x in items
    )

    deps = len(
        dependencies(items)
    )

    stale = sum(
        _days_old(
            x.get("date", "")
        ) >= 4
        and x.get("status")
        == "OPEN"
        for x in items
    )

    action, action_score, action_reason = (
        next_best_action()
    )


    st.html(
        f"""
        <div class="metricgrid">

            <div class="metric">
                <small>LOOP HEALTH</small>
                <strong>{health}</strong>
                <span>/ 100 · commitment health</span>
            </div>

            <div class="metric">
                <small>AT-RISK ITEMS</small>
                <strong>{risks}</strong>
                <span>need attention</span>
            </div>

            <div class="metric">
                <small>DEPENDENCIES</small>
                <strong>{deps}</strong>
                <span>linked effects</span>
            </div>

            <div class="metric">
                <small>MEMORY DECAY</small>
                <strong>{stale}</strong>
                <span>stale open signals</span>
            </div>

        </div>
        """
)


    st.html(
        f"""
        <div class="card">

            <small>
                06 / NEXT BEST ACTION
            </small>

            <span class="score">
                {action_score}
                <span>%</span>
            </span>

            <h3>
                {action}
            </h3>

            <p>
                {action_reason}
            </p>

            <span class="badge">
                RECOVERY READY
            </span>

            <span class="badge">
                CONFIDENCE ·
                {min(96, action_score + 5)}%
            </span>

        </div>
        """
)


    # ========================================================
    # RESULT
    # ========================================================

    r = st.session_state.result

    if r:

        st.html(
            f"""
            <div class="metricgrid">

                <div class="metric">
                    <small>CONFIDENCE</small>
                    <strong>{r["confidence"]}%</strong>
                    <span>evidence signal</span>
                </div>

                <div class="metric">
                    <small>URGENCY</small>
                    <strong>{r["urgency"]}</strong>
                    <span>priority</span>
                </div>

                <div class="metric">
                    <small>IMPORTANCE</small>
                    <strong>{r["importance"]}</strong>
                    <span>project value</span>
                </div>

                <div class="metric">
                    <small>IMPACT</small>
                    <strong>{r["impact"]}</strong>
                    <span>dependency effect</span>
                </div>

            </div>
            """
)


        affected = "<br>".join(
            r["affected"]
        )

        recovery = "<br>".join(
            f"{i + 1:02d} {x}"
            for i, x in enumerate(
                r["recovery"]
            )
        )


        st.html(
            f"""
            <div class="cards">

                <div>

                    <div class="card">

                        <small>
                            01 / ANSWER SHEET ·
                            RECOVERED SIGNAL
                        </small>

                        <span class="score">
                            {r["confidence"]}
                            <span>%</span>
                        </span>

                        <h3>
                            {r["title"]}
                        </h3>

                        <p>
                            {r["summary"]}
                        </p>

                        <span class="badge">
                            DEADLINE ·
                            {r["deadline"]}
                        </span>

                        <span class="badge">
                            PERSON ·
                            {r["person"]}
                        </span>

                        <span class="badge">
                            SOURCE ·
                            LOCAL EVIDENCE
                        </span>

                    </div>


                    <div class="card">

                        <small>
                            03 / KNOWLEDGE SHEET
                        </small>

                        <h3>
                            Why it matters
                        </h3>

                        <span class="badge">
                            URGENCY ·
                            {r["urgency"]}
                        </span>

                        <span class="badge">
                            IMPORTANCE ·
                            {r["importance"]}
                        </span>

                        <span class="badge">
                            IMPACT ·
                            {r["impact"]}
                        </span>

                        <p>
                            Risk combines memory evidence,
                            priority, age, deadlines
                            and dependencies.
                        </p>

                    </div>

                </div>


                <div>

                    <div class="card">

                        <small>
                            02 / THE MOVEMENT OF THOUGHT
                        </small>

                        <div class="tline">

                            <div class="step">
                                <div class="circle">
                                    01
                                </div>
                                DETECT
                            </div>

                            <div class="step">
                                <div class="circle">
                                    02
                                </div>
                                CONTEXT
                            </div>

                            <div class="step">
                                <div class="circle">
                                    03
                                </div>
                                IMPORTANCE
                            </div>

                            <div class="step">
                                <div class="circle">
                                    04
                                </div>
                                DEPENDENCY
                            </div>

                            <div class="step">
                                <div class="circle">
                                    05
                                </div>
                                RECOVERY
                            </div>

                            <div class="step">
                                <div class="circle">
                                    06
                                </div>
                                FOLLOW-UP
                            </div>

                        </div>

                    </div>


                    <div
                        style="
                            display:grid;
                            grid-template-columns:
                                1fr 1fr;
                            gap:10px;
                        "
                    >

                        <div class="card">

                            <small>
                                04 / KNOWLEDGE SHEET
                            </small>

                            <h3>
                                What it affects
                            </h3>

                            <p>
                                {affected}
                            </p>

                        </div>


                        <div class="card">

                            <small>
                                05 / ACTION SHEET
                            </small>

                            <h3>
                                Recovery protocol
                            </h3>

                            <p>
                                {recovery}
                            </p>

                        </div>

                    </div>

                </div>

            </div>
            """
        )


        p1, p2, p3, p4 = st.columns(4)


        with p1:

            if st.button(
                "◈ What-if simulator",
                use_container_width=True,
                key="desk_whatif",
            ):

                st.session_state.whatif = (
                    what_if(
                        st.session_state
                        .prompt_input
                    )
                )


        with p2:

            if st.button(
                "⌁ Evidence explorer",
                use_container_width=True,
                key="desk_evidence",
            ):

                st.session_state.show_evidence = True


        with p3:

            if st.button(
                "＋ Save to favorites",
                use_container_width=True,
                key="desk_favorite",
            ):

                if r["title"] not in [
                    x["title"]
                    for x in st.session_state.favorites
                ]:

                    st.session_state.favorites.insert(
                        0,
                        r,
                    )

                st.success(
                    "Recovery saved to favorites."
                )


        with p4:

            if st.button(
                "☾ Deen AI",
                use_container_width=True,
                key="desk_deen",
            ):

                st.session_state.page = "deen"

                st.rerun()


        # ====================================================
        # WHAT IF
        # ====================================================

        if st.session_state.whatif:

            w = st.session_state.whatif

            st.html(
                f"""
                <div class="card">

                    <small>
                        07 / WHAT-IF SIMULATOR
                    </small>

                    <h3>
                        If this slips
                    </h3>

                    <p>
                        <b>Current risk:</b>
                        {w["current_risk"]}%

                        ·

                        <b>Projected risk:</b>
                        {w["projected_risk"]}%

                        ·

                        <b>Delay:</b>
                        {w["delay_days"]} day(s)

                        ·

                        <b>People:</b>
                        {w["people"]}

                        ·

                        <b>Affected:</b>
                        {w["affected"]}
                    </p>

                    <p>
                        <b>Causal chain:</b>
                        {" → ".join(w["chain"])}
                    </p>

                    <p>
                        <b>Recovery:</b>
                        {" → ".join(w["plan"])}
                    </p>

                </div>
                """
)


        # ====================================================
        # EVIDENCE
        # ====================================================

        if st.session_state.show_evidence:

            st.markdown(
                "#### Evidence Explorer"
            )

            for i, e in enumerate(
                r["evidence"],
                1,
            ):

                st.markdown(
                    f"""
                    **{i:02d} ·
                    {e.get("tag","general").upper()}
                    ·
                    {e.get("priority","Medium")}**

                    —
                    {e.get("text","")}

                    `Risk {risk_score(e)}%
                    · Confidence
                    {e.get("confidence",80)}%`
                    """
                )


    else:

        st.html(
            """
            <div class="card">

                <small>
                    RECOVERY ENGINE
                </small>

                <h3>
                    Ready for a question.
                </h3>

                <p>
                    Ask about forgotten tasks,
                    promises, deadlines,
                    follow-ups, dependencies,
                    risks, or unfinished loops.
                </p>

            </div>
            """
)


# ============================================================
# SEARCH
# ============================================================

elif st.session_state.page == "search":

    st.html(
        '<div class="section-title">'
        'Evidence Intelligence'
        '</div>'
)

    q = st.text_input(
        "Natural-language memory search",
        placeholder=(
            "Things I still owe people, "
            "Project 7 risks, unfinished promises..."
        ),
        key="memory_search",
    )

    if q.strip():

        results = keyword_retrieve(
            q,
            20,
        )

        st.caption(
            f"{len(results)} matching memory signal(s)"
        )

        for x in results:

            st.html(
                f"""
                <div class="card">

                    <small>
                        M{x["id"]} ·
                        {x.get("tag","general").upper()}
                        ·
                        RISK {risk_score(x)}%
                    </small>

                    <h3>
                        {x["text"]}
                    </h3>

                    <p>
                        Project:
                        {x.get("project") or "—"}

                        ·

                        Person:
                        {x.get("person") or "—"}

                        ·

                        Deadline:
                        {x.get("deadline") or "—"}
                    </p>

                </div>
                """
)

    else:

        st.info(
            "Type a natural-language question "
            "to search your evidence archive."
        )


# ============================================================
# MEMORY
# ============================================================

elif st.session_state.page == "memory":

    st.html(
        '<div class="section-title">'
        'Long-Term Memory'
        '</div>'
)


    with st.container(
        border=True
    ):

        st.markdown(
            "### ＋ Save important information"
        )

        text = st.text_area(
            "Memory",
            placeholder=(
                "I promised Sara I would send "
                "the dataset before August 25, 2026."
            ),
            height=100,
            key="new_memory",
        )


        a, b, c = st.columns(3)

        with a:

            tag = st.selectbox(
                "Type",
                [
                    "general",
                    "project",
                    "follow-up",
                    "deadline",
                    "review",
                    "commitment",
                    "decision",
                ],
                key="mem_tag",
            )

        with b:

            priority = st.selectbox(
                "Priority",
                [
                    "High",
                    "Medium",
                    "Low",
                ],
                key="mem_priority",
            )

        with c:

            confidence = st.slider(
                "Confidence",
                1,
                100,
                85,
                key="mem_conf",
            )


        d, e = st.columns(2)

        with d:

            project = st.text_input(
                "Project",
                key="mem_project",
            )

        with e:

            person = st.text_input(
                "Person",
                key="mem_person",
            )


        if st.button(
            "SAVE TO LONG-TERM MEMORY",
            type="primary",
            use_container_width=True,
            key="save_memory",
        ):

            if text.strip():

                saved = save_memory(
                    text,
                    tag,
                    priority,
                    project,
                    person,
                    confidence=confidence,
                    evidence=[
                        "User-provided memory"
                    ],
                )

                save_activity(
                    f"Memory M{saved['id']} added"
                )

                st.success(
                    f"Memory M{saved['id']} saved permanently."
                )

                st.rerun()

            else:

                st.warning(
                    "Write a memory first."
                )


    # ========================================================
    # MEMORY GENOME
    # ========================================================

    st.markdown(
        "### Memory Genome"
    )

    for x in memories()[::-1][:12]:

        g = genome(x)

        with st.container(
            border=True
        ):

            st.markdown(
                f"""
                **M{g["memory_id"]}
                · {g["type"]}
                · {g["status"]}**
                """
            )

            st.write(
                g["commitment"]
            )

            st.caption(
                f"""
                Person:
                {g["person"] or "—"}

                · Project:
                {g["project"] or "—"}

                · Deadline:
                {g["deadline"] or "—"}

                · Importance:
                {g["importance"]}

                · Confidence:
                {g["confidence"]}%
                """
            )

            if st.button(
                "✓ Mark completed",
                key=f"done_{g['memory_id']}",
            ):

                update_memory(
                    g["memory_id"],
                    status="COMPLETED",
                )

                save_activity(
                    f"Memory M{g['memory_id']} completed"
                )

                st.rerun()


    # ========================================================
    # MEMORY CONTROL
    # ========================================================

    st.divider()

    st.markdown(
        "### Memory Control"
    )

    items = memories()

    if items:

        options = {
            f'M{x["id"]} · {x["text"][:65]}':
                x["id"]
            for x in items
        }

        selected = st.selectbox(
            "Select one memory",
            list(options),
            key="delete_memory_select",
        )

        if st.button(
            "🗑 DELETE SELECTED MEMORY",
            use_container_width=True,
            key="delete_selected",
        ):

            mid = options[selected]

            if delete_memory(mid):

                save_activity(
                    f"Memory M{mid} deleted"
                )

                st.success(
                    f"Memory M{mid} deleted permanently."
                )

                st.rerun()

    else:

        st.info(
            "Memory archive is empty."
        )


    if st.button(
        "🗑 DELETE ALL PREVIOUS MEMORIES",
        use_container_width=True,
        key="delete_all",
    ):

        st.session_state.confirm_delete_all = True


    if st.session_state.confirm_delete_all:

        st.warning(
            "This permanently removes the local "
            "LIFELOOP memory archive."
        )

        a, b = st.columns(2)

        with a:

            if st.button(
                "YES, DELETE EVERYTHING",
                type="primary",
                use_container_width=True,
                key="confirm_delete",
            ):

                delete_all_memories()

                st.session_state.confirm_delete_all = False

                st.session_state.result = None

                save_activity(
                    "All memories deleted"
                )

                st.success(
                    "All memories deleted."
                )

                st.rerun()

        with b:

            if st.button(
                "CANCEL",
                use_container_width=True,
                key="cancel_delete",
            ):

                st.session_state.confirm_delete_all = False

                st.rerun()


# ============================================================
# PREVIOUS SESSIONS
# ============================================================

elif st.session_state.page == "sessions":

    st.html(
        '<div class="section-title">'
        'Previous Prism Sessions'
        '</div>'
)

    if not st.session_state.sessions:

        st.info(
            "No sessions yet. "
            "Ask the Recovery Engine a question."
        )

    for i, s in enumerate(
        st.session_state.sessions
    ):

        with st.container(
            border=True
        ):

            st.markdown(
                f'**{s["title"]}**'
            )

            st.caption(
                f'{s["date"]} · '
                f'{s["question"]}'
            )

            if st.button(
                "Reopen",
                key=f"reopen_{i}",
            ):

                st.session_state.prompt_input = (
                    s["question"]
                )

                st.session_state.result = (
                    recovery_engine(
                        s["question"]
                    )
                )

                st.session_state.page = (
                    "desk"
                )

                st.rerun()


# ============================================================
# FAVORITES
# ============================================================

elif st.session_state.page == "favorites":

    st.html(
        '<div class="section-title">'
        'Favorites'
        '</div>'
)

    if not st.session_state.favorites:

        st.info(
            "No recovery favorites yet."
        )

    for x in st.session_state.favorites:

        with st.container(
            border=True
        ):

            st.markdown(
                f'**{x["title"]}** · '
                f'{x["confidence"]}%'
            )

            st.write(
                x["summary"]
            )


# ============================================================
# ACTIVITY
# ============================================================

elif st.session_state.page == "activity":

    st.html(
        '<div class="section-title">'
        'Activity & Intelligence'
        '</div>'
)

    items = memories()

    promises = promise_radar(
        items
    )

    conflicts = contradiction_scan(
        items
    )

    stale = [
        x
        for x in items
        if _days_old(
            x.get("date", "")
        ) >= 4
        and x.get("status")
        == "OPEN"
    ]


    a, b, c, d = st.columns(4)

    a.metric(
        "Memories",
        len(items),
    )

    b.metric(
        "Promises detected",
        len(promises),
    )

    c.metric(
        "Contradictions",
        len(conflicts),
    )

    d.metric(
        "Memory decay",
        len(stale),
    )


    st.markdown(
        "### Daily AI Briefing"
    )

    st.html(
        f"""
        <div class="card">

            <h3>
                Today
            </h3>

            <p>
                {sum(risk_score(x) >= 70 for x in items)}
                risky signals ·

                {len(promises)}
                promise signals ·

                {len(conflicts)}
                possible conflicts ·

                {len(stale)}
                stale unresolved items.
            </p>

        </div>
        """
)


    st.markdown(
        "### Promise Radar"
    )

    for x in promises[:10]:

        st.write(
            f'🎯 M{x["id"]} · {x["text"]}'
        )


    if conflicts:

        st.markdown(
            "### Contradiction Detector"
        )

        for c in conflicts:

            st.warning(
                "Possible conflict: "
                + ", ".join(
                    c["deadlines"]
                )
                + " · "
                + c["topic"]
            )


    st.markdown(
        "### Recent activity"
    )

    acts = read_json(
        ACTIVITY_FILE,
        [],
    )

    if not acts:

        st.info(
            "No recorded activity yet."
        )

    for a in acts[:20]:

        st.write(
            f'• {a["time"]} — '
            f'{a["text"]}'
        )


# ============================================================
# RISK RADAR
# ============================================================

elif st.session_state.page == "radar":

    st.html(
        '<div class="section-title">'
        'Commitment Risk Radar'
        '</div>'
)

    items = sorted(
        memories(),
        key=risk_score,
        reverse=True,
    )

    a, b, c = st.columns(3)

    a.metric(
        "Loop Health",
        loop_health(),
        "/100",
    )

    b.metric(
        "Critical",
        sum(
            risk_score(x) >= 85
            for x in items
        ),
    )

    c.metric(
        "At Risk",
        sum(
            70 <= risk_score(x) < 85
            for x in items
        ),
    )


    for x in items:

        rs = risk_score(x)

        label = (
            "CRITICAL"
            if rs >= 85
            else "AT RISK"
            if rs >= 70
            else "HEALTHY"
        )

        with st.container(
            border=True
        ):

            st.markdown(
                f"""
                **{label}
                · {rs}%
                · M{x["id"]}**
                """
            )

            st.write(
                x["text"]
            )

            st.caption(
                f'''
                {x.get("tag","general").upper()}
                ·
                {x.get("priority","Medium")}
                ·
                {x.get("date","—")}
                '''
            )


# ============================================================
# PEOPLE / NETWORK
# ============================================================

elif st.session_state.page == "network":

    st.html(
        '<div class="section-title">'
        'People & Dependency Intelligence'
        '</div>'
)

    items = memories()

    a, b = st.columns(2)


    with a:

        st.markdown(
            "### People Map"
        )

        for name, count in people_from_memory(
            items
        ):

            st.write(
                f"**{name}** · "
                f"{count} related signal(s)"
            )


    with b:

        st.markdown(
            "### Dependency Chain"
        )

        for left, right in dependencies(
            items
        ):

            st.write(
                f"**{left}** → **{right}**"
            )


    st.markdown(
        "### Memory Timeline"
    )

    for x in sorted(
        items,
        key=lambda z: z.get(
            "date",
            "",
        ),
        reverse=True,
    ):

        st.write(
            f'''
            **{x.get("date","—")}**
            ·
            `{x.get("tag","general")}`
            ·
            {x["text"]}
            '''
        )


# ============================================================
# RECOVERY MISSION
# ============================================================

elif st.session_state.page == "mission":

    st.html(
        '<div class="section-title">'
        'Recovery Mission'
        '</div>'
)

    q = st.text_input(
        "Mission target",
        value=st.session_state.prompt_input,
        placeholder=(
            "Recover my Project 7 commitments "
            "and deadlines"
        ),
        key="mission_target",
    )


    if st.button(
        "START RECOVERY MISSION",
        type="primary",
        use_container_width=True,
        key="start_mission",
    ):

        st.session_state.result = (
            recovery_mission(q)
        )

        st.session_state.prompt_input = q

        st.rerun()


    r = st.session_state.result


    if r and "mission" in r:

        st.progress(
            r["risk"] / 100
        )

        st.markdown(
            f'### {r["title"]}'
        )

        st.write(
            r["summary"]
        )

        st.caption(
            f'''
            Risk {r["risk"]}%
            ·
            Confidence {r["confidence"]}%
            ·
            Impact {r["impact"]}%
            '''
        )


        st.markdown(
            "### Explainable Agent Trace"
        )

        for i, step in enumerate(
            r["mission"],
            1,
        ):

            st.write(
                f"{i:02d} · {step}"
            )


        st.markdown(
            "### Agent Health"
        )

        for name, count in r["agents"]:

            st.write(
                f"✓ **{name}** · "
                f"Completed · evidence {count}"
            )


        st.markdown(
            "### Human Approval Gate"
        )

        approval = r["approval"]


        if approval["status"] == "PENDING":

            st.warning(
                "AI proposes this recovery action. "
                "Review before approval."
            )

            a, b = st.columns(2)


            with a:

                if st.button(
                    "APPROVE",
                    use_container_width=True,
                    key="approve_mission",
                ):

                    data = read_json(
                        APPROVAL_FILE,
                        [],
                    )

                    for x in data:

                        if (
                            x["id"]
                            == approval["id"]
                        ):

                            x["status"] = (
                                "APPROVED"
                            )

                            x["resolved_at"] = (
                                now_iso()
                            )

                    write_json(
                        APPROVAL_FILE,
                        data,
                    )

                    save_activity(
                        "Recovery mission approved"
                    )

                    st.success(
                        "Approved and recorded."
                    )


            with b:

                if st.button(
                    "REJECT",
                    use_container_width=True,
                    key="reject_mission",
                ):

                    data = read_json(
                        APPROVAL_FILE,
                        [],
                    )

                    for x in data:

                        if (
                            x["id"]
                            == approval["id"]
                        ):

                            x["status"] = (
                                "REJECTED"
                            )

                            x["resolved_at"] = (
                                now_iso()
                            )

                    write_json(
                        APPROVAL_FILE,
                        data,
                    )

                    save_activity(
                        "Recovery mission rejected"
                    )

                    st.info(
                        "Rejected and recorded."
                    )


# ============================================================
# DEEN AI
# ============================================================

elif st.session_state.page == "deen":

    st.html(
        """
        <div class="deen-hero">

            <small>
                ENHANCED INTELLIGENCE ·
                ISLAMIC INTELLIGENCE LAYER
            </small>

            <h1 class="section-title">
                🌙 Deen AI
            </h1>

            <p>
                Prayer intelligence ·
                Quran search ·
                Islamic research
            </p>

        </div>
        """
    )

    a, b, c = st.columns(3)


    with a:

        if st.button(
            "🕌 Prayer Times",
            use_container_width=True,
            key="deen_prayer_tab",
        ):

            st.session_state.deen_section = (
                "prayer"
            )


    with b:

        if st.button(
            "📖 Al-Quran",
            use_container_width=True,
            key="deen_quran_tab",
        ):

            st.session_state.deen_section = (
                "quran"
            )


    with c:

        if st.button(
            "🌍 Islamic Research",
            use_container_width=True,
            key="deen_research_tab",
        ):

            st.session_state.deen_section = (
                "research"
            )


    # ========================================================
    # PRAYER
    # ========================================================

    if st.session_state.deen_section == "prayer":

        st.markdown(
            "### 🕌 Prayer Intelligence"
        )

        mode = st.radio(
            "Location mode",
            [
                "City",
                "Coordinates",
            ],
            horizontal=True,
            key="prayer_mode",
        )


        method = st.selectbox(
            "Calculation method",
            [
                (
                    "Karachi / University "
                    "of Islamic Sciences",
                    1,
                ),
                (
                    "Muslim World League",
                    3,
                ),
                (
                    "Egyptian General Authority",
                    5,
                ),
            ],
            format_func=lambda x: x[0],
            key="prayer_method",
        )


        school = st.selectbox(
            "Asr calculation",
            [
                (
                    "Hanafi",
                    1,
                ),
                (
                    "Standard / Shafi",
                    0,
                ),
            ],
            format_func=lambda x: x[0],
            key="prayer_school",
        )


        if mode == "City":

            a, b = st.columns(2)

            with a:

                city = st.text_input(
                    "City",
                    value="Lahore",
                    key="prayer_city",
                )

            with b:

                country = st.text_input(
                    "Country",
                    value="Pakistan",
                    key="prayer_country",
                )


            if st.button(
                "GET PRAYER TIMES",
                type="primary",
                use_container_width=True,
                key="get_city_prayer",
            ):

                try:

                    st.session_state.deen_prayer = (
                        get_city_prayer_summary(
                            city,
                            country,
                            method=method[1],
                            school=school[1],
                        )
                    )

                    st.success(
                        "Prayer times loaded."
                    )

                except Exception as e:

                    st.error(
                        f"Prayer service unavailable: {e}"
                    )


        else:

            a, b = st.columns(2)

            with a:

                lat = st.number_input(
                    "Latitude",
                    value=31.5204,
                    format="%.6f",
                    key="prayer_lat",
                )

            with b:

                lon = st.number_input(
                    "Longitude",
                    value=74.3587,
                    format="%.6f",
                    key="prayer_lon",
                )


            if st.button(
                "GET PRAYER TIMES",
                type="primary",
                use_container_width=True,
                key="get_coord_prayer",
            ):

                try:

                    st.session_state.deen_prayer = (
                        get_prayer_summary(
                            lat,
                            lon,
                            method=method[1],
                            school=school[1],
                        )
                    )

                    st.success(
                        "Prayer times loaded."
                    )

                except Exception as e:

                    st.error(
                        f"Prayer service unavailable: {e}"
                    )


        if st.session_state.deen_prayer:

            data = (
                st.session_state.deen_prayer
            )

            timings = data["timings"]

            np = next_prayer(
                timings
            )

            st.success(
                f'Next prayer: '
                f'{np["name"]} · '
                f'{np["time"]} · '
                f'countdown '
                f'{countdown(np["target"])}'
            )


            cols = st.columns(5)

            for col, name in zip(
                cols,
                [
                    "Fajr",
                    "Dhuhr",
                    "Asr",
                    "Maghrib",
                    "Isha",
                ],
            ):

                col.metric(
                    name,
                    timings.get(
                        name,
                        "—",
                    ).split(" ")[0],
                )


            hijri = (
                data.get(
                    "date",
                    {},
                ).get(
                    "hijri",
                    {},
                )
            )

            greg = (
                data.get(
                    "date",
                    {},
                ).get(
                    "gregorian",
                    {},
                )
            )


            st.info(
                f'''
                Gregorian:
                {greg.get("date","—")}

                ·

                Hijri:
                {hijri.get("date","—")}
                {hijri.get("month",{}).get("en","")}
                {hijri.get("year","")}
                '''
            )


            st.caption(
                "Calculation method and school are configurable. "
                "Prayer timing is provided as a calculation "
                "service, not a religious ruling."
            )


    # ========================================================
    # QURAN
    # ========================================================

    elif st.session_state.deen_section == "quran":

        st.markdown(
            "### 📖 Quran Intelligence"
        )

        q = st.text_input(
            "Search Quran",
            placeholder=(
                "patience, mercy, parents, promises..."
            ),
            key="quran_query",
        )


        language = st.selectbox(
    "Search language / تلاش کی زبان",
    [
        ("English", "en"),
        ("العربية", "ar"),
        ("اردو", "ur"),
    ],
    format_func=lambda x: x[0],
    key="quran_lang",
)


        if st.button(
            "SEARCH QURAN",
            type="primary",
            use_container_width=True,
            key="search_quran",
        ):

            if not q.strip():

                st.warning(
                    "Enter a Quran topic or phrase first."
                )

            else:

                try:

                    st.session_state.deen_quran = (
                        search_quran(
                            q.strip(),
                            language[1],
                        )
                    )

                except Exception as e:

                    st.error(
                        f"Quran service unavailable: {e}"
                    )


        if (
            st.session_state.deen_quran
            is not None
        ):

            matches = (
                st.session_state.deen_quran
            )

            st.caption(
                f"{len(matches)} match(es) returned"
            )


            for m in matches[:10]:

                surah = m.get(
                    "surah",
                    {},
                )

                st.html(
                    f"""
                    <div class="deen-card">

                        <small>
                            {
                                surah.get(
                                    "englishName",
                                    surah.get(
                                        "name",
                                        "",
                                    ),
                                )
                            }
                            ·
                            {m.get(
                                "numberInSurah",
                                "",
                            )}
                        </small>

                        <p>
                            {m.get(
                                "text",
                                "",
                            )}
                        </p>

                        <small>
                            Ayah
                            {m.get(
                                "number",
                                "",
                            )}
                        </small>

                    </div>
                    """
                )


        st.caption(
            "Quran text/search is provided as an "
            "informational retrieval layer; translations "
            "and interpretations can differ."
        )


    # ========================================================
    # ISLAMIC RESEARCH
    # ========================================================

    else:

        st.markdown(
            "### 🌍 Islamic Research Agent"
        )

        question = st.text_area(
            "Research question",
            placeholder=(
                "Research Islamic teachings about honesty, "
                "keeping promises, patience, etc."
            ),
            height=110,
            key="deen_research_question",
        )


        mode = st.selectbox(
            "Research mode",
            [
                "Quick Research",
                "Deep Research",
                "Quran & Hadith Research",
                "Scholarly Research",
            ],
            key="deen_research_mode",
        )


        if st.button(
            "🔎 START RESEARCH",
            type="primary",
            use_container_width=True,
            key="start_deen_research",
        ):

            if not question.strip():

                st.warning(
                    "Enter a research question first."
                )

            else:

                with st.spinner(
                    "Searching and classifying sources..."
                ):

                    try:

                        st.session_state.deen_research = (
                            research(
                                question.strip(),
                                mode,
                            )
                        )

                    except Exception as e:

                        st.error(
                            f"Research service unavailable: {e}"
                        )


        rr = (
            st.session_state.deen_research
        )


        if rr:

            st.info(
                rr["note"]
            )

            counts = (
                rr["source_counts"]
            )

            a, b, c, d, e = st.columns(5)

            a.metric(
                "Quran",
                counts["Quran"],
            )

            b.metric(
                "Hadith",
                counts["Hadith"],
            )

            c.metric(
                "Tafsir",
                counts["Tafsir"],
            )

            d.metric(
                "Academic",
                counts["Academic"],
            )

            e.metric(
                "General",
                counts["General"],
            )


            st.markdown(
                "### Source Evidence"
            )


            if not rr["sources"]:

                st.warning(
                    "No web results were returned. "
                    "Try a broader question."
                )


            for i, s in enumerate(
                rr["sources"],
                1,
            ):

                st.markdown(
                    f'''
                    **{i:02d} ·
                    {s["source_type"]}
                    ·
                    {s["title"]}**
                    '''
                )

                st.write(
                    s.get(
                        "snippet"
                    )
                    or "No snippet available."
                )

                st.code(
                    s["url"],
                    language="text",
                )


            st.markdown(
                "### Research Guardrail"
            )

            st.write(
                "LIFELOOP distinguishes retrieved "
                "sources from synthesis. It does not "
                "automatically issue a fatwa or claim "
                "that a general web result represents "
                "a consensus ruling. For religious "
                "rulings, consult a qualified scholar."
            )


# ============================================================
# SETTINGS
# ============================================================

elif st.session_state.page == "settings":

    st.html(
        '<div class="section-title">'
        'Prism System Settings'
        '</div>'
)


    a, b = st.columns(2)


    with a:

        st.success(
            "Local memory engine: ONLINE"
        )

        st.success(
            "Recovery workflow: ONLINE"
        )

        st.success(
            "Deen AI module: ONLINE"
        )

        st.info(
            "External LLM: optional"
        )


    with b:

        st.write(
            "**Privacy**"
        )

        st.write(
            "Local evidence is stored in "
            "data/memories.json."
        )

        st.write(
            "API credentials, if added later, "
            "should be stored in environment variables."
        )


    # ========================================================
    # EXPORT
    # ========================================================

    st.markdown(
        "### Export"
    )


    raw = json.dumps(
        memories(),
        indent=2,
        ensure_ascii=False,
    ).encode()


    st.download_button(
        "⇩ Download memory JSON",
        raw,
        "lifeloop_memory.json",
        "application/json",
    )


    buf = io.StringIO()

    fields = [
        "id",
        "text",
        "date",
        "tag",
        "priority",
        "status",
        "confidence",
        "person",
        "project",
        "deadline",
        "source",
        "type",
    ]


    writer = csv.DictWriter(
        buf,
        fieldnames=fields,
        extrasaction="ignore",
    )

    writer.writeheader()

    writer.writerows(
        memories()
    )


    st.download_button(
        "⇩ Download memory CSV",
        buf.getvalue(),
        "lifeloop_memory.csv",
        "text/csv",
    )


    # ========================================================
    # DATA MAINTENANCE
    # ========================================================

    st.markdown(
        "### Recovery / Data Maintenance"
    )


    if st.button(
        "Restore starter archive",
        key="restore_starter",
    ):

        restore_starter()

        save_activity(
            "Starter archive restored"
        )

        st.success(
            "Starter archive restored."
        )

        st.rerun()


    st.caption(
        "Reminder/email integration remains optional "
        "and is intentionally not required for the "
        "core application to run."
    )


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="foot">

        LIFELOOP AI · PROJECT 7 /
        INDEPENDENT AGENTIC SYSTEM ·
        PRISM DESK · DEEN AI EDITION

    </div>
    """
)