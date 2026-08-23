import json
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from .config import CONVERSATIONS_FILE, GROQ_MODEL
from .models import ChatRequest, ChatResponse
from .agent import agent
from .groq_client import SYSTEM_PROMPT, stream_answer
from .rag import retrieve

app = FastAPI(title="Knowledge-Based Decision Agent", version="1.0.0")


def load_conversations():
    try:
        return json.loads(CONVERSATIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_conversations(items):
    CONVERSATIONS_FILE.write_text(
        json.dumps(items, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


@app.get("/health")
def health():
    return {"status": "ok", "model": GROQ_MODEL}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = agent.invoke({
            "query": request.message,
            "conversation": request.conversation,
            "top_k": request.top_k,
        })

        return ChatResponse(
            answer=result.get("response", ""),
            sources=result.get("sources", []),
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            model=GROQ_MODEL,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    try:
        sources = retrieve(request.message, request.top_k)

        context = "\n\n".join(
            f"[Source {i + 1} — {s['source']}]\n{s['content']}"
            for i, s in enumerate(sources)
        ) or "No relevant private knowledge-base documents were retrieved."

        history = [
            {"role": m["role"], "content": m["content"]}
            for m in request.conversation[-8:]
            if m.get("role") in {"user", "assistant"} and m.get("content")
        ]

        prompt = f"""User request:
{request.message}

Retrieved private knowledge-base context:
{context}

Answer from the private context. If insufficient, say so.
For decisions, give a clear recommendation and concise evidence-based rationale.
Do not expose chain-of-thought."""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        conversation_id = request.conversation_id or str(uuid.uuid4())

        def events():
            safe = [{k: v for k, v in s.items() if k != "content"} for s in sources]
            yield "event: meta\n"
            yield f"data: {json.dumps({'conversation_id': conversation_id, 'model': GROQ_MODEL, 'sources': safe})}\n\n"

            try:
                for token in stream_answer(messages):
                    yield f"data: {json.dumps({'token': token})}\n\n"
                yield "event: done\ndata: {}\n\n"
            except Exception as exc:
                yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/conversations")
def conversations():
    return load_conversations()


@app.post("/api/conversations")
def save_conversation(payload: dict):
    items = load_conversations()
    item = {
        "id": payload.get("id") or str(uuid.uuid4()),
        "title": payload.get("title", "New conversation"),
        "messages": payload.get("messages", []),
        "favorite": bool(payload.get("favorite", False)),
    }
    items = [x for x in items if x.get("id") != item["id"]]
    items.insert(0, item)
    save_conversations(items[:100])
    return item


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    save_conversations([
        x for x in load_conversations()
        if x.get("id") != conversation_id
    ])
    return {"ok": True}
