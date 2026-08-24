from __future__ import annotations
from datetime import datetime, timedelta

PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

def clean_time(value: str) -> str:
    return (value or "").split(" ")[0]

def next_prayer(timings: dict, now: datetime | None = None):
    now = now or datetime.now()
    for name in PRAYERS:
        value = clean_time(timings.get(name, ""))
        try:
            hour, minute = map(int, value.split(":")[:2])
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target > now:
                return {"name": name, "time": value, "target": target}
        except Exception:
            continue
    value = clean_time(timings.get("Fajr", "--:--"))
    try:
        hour, minute = map(int, value.split(":")[:2])
        target = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    except Exception:
        target = now
    return {"name": "Fajr", "time": value, "target": target}

def countdown(target, now=None):
    now = now or datetime.now()
    seconds = max(0, int((target - now).total_seconds()))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
