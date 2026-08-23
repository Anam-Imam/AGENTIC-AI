from agents.extraction_agent import ExtractionAgent
from rag.chroma_store import ChromaStore
from core.validator import validate
from core.config import MAX_RETRIES

class DocumentProcessor:
    def __init__(self):
        self.agent = ExtractionAgent()
        self.store = ChromaStore()

    def process(self, text, document_id, filename, instruction):
        chunks = self.store.index(text, document_id, filename)
        query = instruction.strip() or "important facts entities dates amounts action items"
        context_docs = self.store.search(query, document_id)
        context = "\n\n--- SOURCE CHUNK ---\n\n".join(context_docs)
        issues = []
        attempts = []
        result = None
        valid = False

        for attempt in range(MAX_RETRIES + 1):
            feedback = instruction
            if issues:
                feedback += "\nFix these validation issues: " + "; ".join(issues)
            result = self.agent.extract(text, context, feedback)
            valid, issues = validate(result, text)
            attempts.append({"attempt": attempt + 1, "valid": valid, "issues": issues[:]})
            if valid:
                break

        return {
            "result": result, "valid": valid, "issues": issues,
            "attempts": attempts, "chunks": chunks, "sources": context_docs
        }
