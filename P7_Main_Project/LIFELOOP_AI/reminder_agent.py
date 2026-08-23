import json
from datetime import date, datetime, timedelta
from pathlib import Path

from email_service import send_email

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
MEMORY_FILE = DATA / "memories.json"
HISTORY_FILE = DATA / "reminder_history.json"


def _read(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def _deadline(value):
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%d %b %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def check_deadlines(today=None):
    today = today or date.today()
    target = today + timedelta(days=1)
    memories = _read(MEMORY_FILE, [])
    history = _read(HISTORY_FILE, [])
    reminders = []

    for item in memories:
        due = _deadline(item.get("deadline"))
        if due != target:
            continue
        if str(item.get("status", "OPEN")).upper() in {"COMPLETED", "CLOSED", "DONE"}:
            continue
        if item.get("email_reminder", True) is False:
            continue

        memory_id = str(item.get("id"))
        already = any(
            str(x.get("memory_id")) == memory_id and
            x.get("type") == "one_day_before" and
            x.get("deadline") == due.isoformat()
            for x in history
        )
        if already:
            continue

        text = item.get("text", "Upcoming deadline")
        project = item.get("project") or "General"
        priority = item.get("priority", "Medium")
        subject = f"⚠ LIFELOOP — Deadline Tomorrow: {text[:60]}"
        body = (
            "LIFELOOP DEADLINE REMINDER\n\n"
            f"Task: {text}\n"
            f"Project: {project}\n"
            f"Priority: {priority}\n"
            f"Deadline: {due.isoformat()}\n\n"
            "Your deadline is tomorrow. Please review or complete this item today."
        )
        sent, result = send_email(subject, body)
        if sent:
            history.append({
                "memory_id": item.get("id"),
                "type": "one_day_before",
                "deadline": due.isoformat(),
                "sent_at": datetime.now().isoformat(timespec="seconds")
            })
            reminders.append({"memory_id": item.get("id"), "text": text, "deadline": due.isoformat()})

    _write(HISTORY_FILE, history)
    return reminders


if __name__ == "__main__":
    found = check_deadlines()
    print(f"LIFELOOP reminder check complete. Sent: {len(found)}")
