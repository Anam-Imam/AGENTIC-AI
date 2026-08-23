from pathlib import Path
import hashlib
import re
import chromadb
from sentence_transformers import SentenceTransformer
from .config import CHROMA_DIR, KB_DIR

COLLECTION = "private_knowledge_base"
_model = None


def embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def collection():
    db = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return db.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def split_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))

        if end < len(text):
            boundary = max(
                text.rfind("\n\n", start, end),
                text.rfind("\n", start, end),
                text.rfind(". ", start, end),
            )
            if boundary > start + size // 2:
                end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def ingest_directory(directory: Path = KB_DIR) -> int:
    col = collection()
    total = 0

    for path in sorted(directory.glob("*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue

        chunks = split_text(path.read_text(encoding="utf-8", errors="ignore"))
        if not chunks:
            continue

        vectors = embedding_model().encode(
            chunks, normalize_embeddings=True
        ).tolist()

        ids = []
        metadata = []

        for i, chunk in enumerate(chunks):
            digest = hashlib.sha1(chunk.encode()).hexdigest()[:10]
            ids.append(f"{path.name}:{i}:{digest}")
            metadata.append({
                "source": path.name,
                "title": path.stem.replace("_", " ").title(),
                "chunk": i,
            })

        col.upsert(
            ids=ids,
            documents=chunks,
            embeddings=vectors,
            metadatas=metadata,
        )
        total += len(chunks)

    return total


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    col = collection()

    if col.count() == 0:
        return []

    vector = embedding_model().encode(
        [query], normalize_embeddings=True
    ).tolist()

    result = col.query(
        query_embeddings=vector,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    output = []
    for doc, meta, distance in zip(docs, metas, distances):
        output.append({
            "title": meta.get("title", "Knowledge Base"),
            "source": meta.get("source", "private document"),
            "preview": doc[:360].replace("\n", " "),
            "score": round(max(0.0, 1.0 - float(distance)), 3),
            "content": doc,
        })

    return output
