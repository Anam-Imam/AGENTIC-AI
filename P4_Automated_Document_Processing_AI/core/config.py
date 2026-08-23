import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
CHROMA_PATH = str(ROOT / "data" / "chroma")
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 180
MAX_RETRIES = 2
