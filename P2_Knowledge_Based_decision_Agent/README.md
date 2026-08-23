# Knowledge-Based Decision Agent — Premium AI Command Center

Project 2 implementation using Streamlit, FastAPI, Groq, LangGraph, ChromaDB and Agentic RAG.

## Architecture

```text
User → Streamlit UI → FastAPI → LangGraph
                         ↓
                  Query Analysis
                         ↓
                    ChromaDB RAG
                         ↓
                    Groq LLM
                         ↓
                  Streamed Answer
```

## Run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add your key to `.env`:

```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
BACKEND_URL=http://127.0.0.1:8000
```

Index the private knowledge base:

```bash
python scripts/ingest.py
```

Start backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

Start UI in another terminal:

```bash
streamlit run app.py
```

Put your own `.md` and `.txt` files in `data/knowledge_base/`, then run ingestion again.

## Structure

```text
knowledge_based_decision_agent/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── backend/
│   ├── config.py
│   ├── groq_client.py
│   ├── models.py
│   ├── rag.py
│   ├── agent.py
│   └── main.py
├── data/knowledge_base/
│   └── company_policy.md
├── scripts/ingest.py
└── storage/
```

For production, replace the local conversation JSON store with PostgreSQL and add authentication, HTTPS, rate limiting and structured logging.
