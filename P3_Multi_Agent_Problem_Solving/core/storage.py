from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
HISTORY_FILE = DATA_DIR / "history.json"
SEED_FILE = DATA_DIR / "history.seed.json"


def _ensure() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text(SEED_FILE.read_text(encoding="utf-8"), encoding="utf-8")


def load_history() -> list[dict[str, Any]]:
    _ensure()
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_history(items: list[dict[str, Any]]) -> None:
    _ensure()
    HISTORY_FILE.write_text(json.dumps(items[-100:], indent=2, ensure_ascii=False), encoding="utf-8")


def add_session(
    title: str,
    request: str,
    response: str,
    agents: list[str],
    sources: list[dict[str, str]],
) -> None:
    items = load_history()
    items.append(
        {
            "title": title[:100],
            "request": request,
            "response": response,
            "agents": agents,
            "sources": sources,
            "favorite": False,
        }
    )
    save_history(items)


def update_favorite(index: int, value: bool) -> None:
    items = load_history()
    if 0 <= index < len(items):
        items[index]["favorite"] = bool(value)
        save_history(items)


def delete_session(index: int) -> None:
    items = load_history()
    if 0 <= index < len(items):
        items.pop(index)
        save_history(items)


def clear_history() -> None:
    save_history([])
