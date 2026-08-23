# NEXUS — Multi-Agent AI Command Center

A futuristic Streamlit + LangGraph + Groq application based on the Project 3 architecture:

**User → Streamlit UI → Supervisor → Research / Analysis / Execution → Final Synthesis → Streamlit Output**

## What is fixed in this version

- All six top quick-action buttons now do something useful.
- New Chat clears the active conversation and pending state.
- Ask AI / Analyze / Generate preload the mission composer with useful prompts.
- Search opens a searchable history archive.
- History opens the archive and lets you open sessions.
- Favorites can be starred/unstarred.
- Sessions can be deleted.
- History can be cleared.
- Theme toggle works.
- Supervisor routing is now dynamic instead of always forcing every downstream agent.
- Research model has a fallback to the normal Groq model if the configured research model fails.
- Context is aggressively clipped between agents to prevent `413 Request Entity Too Large` errors.
- Tool loops are capped and tool payloads/results are clipped.
- Final synthesis receives a bounded context instead of the full unbounded trace.
- The UI no longer renders assistant responses as raw HTML, so Markdown in model output displays correctly.

## 1. Requirements

- Python 3.10–3.12 recommended
- Git
- A Groq API key

## 2. Create the environment (Git Bash on Windows)

```bash
cd /c/Users/<YOUR_USERNAME>/AGENTICAI
python -m venv .venv
source .venv/Scripts/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure Groq

Copy `.env.example` to `.env` and add your secret:

```env
GROQ_API_KEY=your_real_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_RESEARCH_MODEL=groq/compound
MAX_MESSAGE_CHARS=14000
AGENT_CONTEXT_CHARS=6500
FINAL_CONTEXT_CHARS=17000
```

Never put the Groq key in Streamlit frontend code or commit `.env` to Git.

## 5. Run

```bash
streamlit run app.py
```

Open the local URL Streamlit prints, normally `http://localhost:8501`.

## 6. Buttons

- **New Chat** — resets the active conversation.
- **Ask AI** — switches the composer to a general AI prompt.
- **Analyze** — loads an analysis prompt template.
- **Generate** — loads an implementation/deliverable template.
- **Search** — opens searchable local history.
- **History** — opens the archive.
- **☼ / ☾** — toggles the interface theme.
- **Open** — restores a saved session.
- **☆ / ★** — favorite/unfavorite a session.
- **Delete** — removes one saved session.
- **Clear all** — removes local history.
- **EXECUTE ◇** — sends the mission through the LangGraph multi-agent workflow.

## 7. Architecture

- `app.py` — premium command center UI and interaction state.
- `agents/graph.py` — LangGraph workflow and specialist agents.
- `agents/state.py` — shared graph state.
- `core/groq_client.py` — secure Groq SDK wrapper plus request-size protection.
- `core/tools.py` — calculator, text statistics and plan builder tools.
- `core/prompts.py` — role prompts for Supervisor / Research / Analysis / Execution / Final.
- `core/storage.py` — lightweight local JSON session history and favorites.
- `ui/components.py` — AI Core and UI components.
- `ui/styles.py` — cinematic black/graphite/silver design system.

## 8. How the workflow moves

1. Streamlit captures the mission.
2. Supervisor selects the specialist route.
3. Selected agents run in the route order.
4. Research can use the configured Groq research model.
5. Analysis and Execution can use the local tools through Groq tool calling.
6. Large context is clipped before it is forwarded to later agents.
7. Final Synthesis combines the bounded specialist results.
8. Streamlit displays the final answer, trace, sources and saved session.
