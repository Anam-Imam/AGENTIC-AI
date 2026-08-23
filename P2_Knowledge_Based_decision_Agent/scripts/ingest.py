from backend.rag import ingest_directory

if __name__ == "__main__":
    print(f"Ingestion complete: {ingest_directory()} chunks indexed.")
