import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HISTORY_FILE = DATA_DIR / "history.json"
LOG_FILE = DATA_DIR / "logs.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"

DATA_DIR.mkdir(exist_ok=True)


def _read(path, default):
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_history():
    return _read(HISTORY_FILE, [])


def add_to_history(item):
    history = get_history()
    history.append(item)
    _write(HISTORY_FILE, history[-100:])


def get_logs():
    return _read(LOG_FILE, [])


def add_log(event, payload):
    logs = get_logs()
    summary = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    logs.append({
        "event": event,
        "timestamp": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
    })
    _write(LOG_FILE, logs[-200:])


def get_favorites():
    return _read(FAVORITES_FILE, [])


def toggle_favorite(item_id):
    favorites = get_favorites()
    ids = {x.get("id") for x in favorites}
    history = get_history()

    if item_id in ids:
        favorites = [x for x in favorites if x.get("id") != item_id]
    else:
        match = next((x for x in history if x.get("id") == item_id), None)
        if match:
            favorites.append(match)
    _write(FAVORITES_FILE, favorites)
