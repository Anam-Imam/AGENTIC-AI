from pathlib import Path
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config import CHROMA_PATH, CHUNK_SIZE, CHUNK_OVERLAP

class ChromaStore:
    def __init__(self):
        Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = client.get_or_create_collection("aurelia_documents")

    def index(self, text, document_id, filename):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.split_text(text)
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metas = [{"document_id": document_id, "filename": filename, "chunk": i+1}
                 for i in range(len(chunks))]
        if chunks:
            self.collection.add(ids=ids, documents=chunks, metadatas=metas)
        return len(chunks)

    def search(self, query, document_id, n=6):
        count = self.collection.count()
        if count == 0:
            return []
        result = self.collection.query(
            query_texts=[query],
            n_results=min(n, count),
            where={"document_id": document_id}
        )
        return result.get("documents", [[]])[0]
