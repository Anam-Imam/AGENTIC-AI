from __future__ import annotations
from datetime import datetime
import requests

ALADHAN_BASE = "https://api.aladhan.com/v1"


def get_prayer_summary(latitude: float, longitude: float, method: int = 1, school: int = 1):
    date_string = datetime.now().strftime("%d-%m-%Y")
    response = requests.get(
        f"{ALADHAN_BASE}/timings/{date_string}",
        params={"latitude": latitude, "longitude": longitude, "method": method, "school": school},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 200:
        raise RuntimeError(payload.get("status", "Prayer API failed"))
    data = payload["data"]
    return {"timings": data.get("timings", {}), "date": data.get("date", {}), "meta": data.get("meta", {})}


def get_city_prayer_summary(city: str, country: str, method: int = 1, school: int = 1):
    date_string = datetime.now().strftime("%d-%m-%Y")
    response = requests.get(
        f"{ALADHAN_BASE}/timingsByCity/{date_string}",
        params={"city": city, "country": country, "method": method, "school": school},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 200:
        raise RuntimeError(payload.get("status", "Prayer API failed"))
    data = payload["data"]
    return {"timings": data.get("timings", {}), "date": data.get("date", {}), "meta": data.get("meta", {})}
