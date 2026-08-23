from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
CHROMA_DIR = ROOT / "storage" / "chroma"
KB_DIR = ROOT / "data" / "knowledge_base"
CONVERSATIONS_FILE = ROOT / "storage" / "conversations.json"

for folder in (CHROMA_DIR, KB_DIR, CONVERSATIONS_FILE.parent):
    folder.mkdir(parents=True, exist_ok=True)

if not CONVERSATIONS_FILE.exists():
    CONVERSATIONS_FILE.write_text("[]", encoding="utf-8")
