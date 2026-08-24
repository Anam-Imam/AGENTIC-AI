from __future__ import annotations
import requests

BASE = "https://api.alquran.cloud/v1"


def search_quran(query: str, language: str = "en"):
    """No-key Quran search using AlQuran.cloud's public API.
    Returns matching ayahs plus references. Network failures are surfaced cleanly.
    """
    response = requests.get(f"{BASE}/search/{requests.utils.quote(query)}/all/{language}", timeout=15)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 200:
        raise RuntimeError(payload.get("status", "Quran search failed"))
    return payload.get("data", {}).get("matches", [])


def get_surah(surah_number: int, edition: str = "en.asad"):
    response = requests.get(f"{BASE}/surah/{int(surah_number)}/{edition}", timeout=15)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 200:
        raise RuntimeError(payload.get("status", "Surah request failed"))
    return payload.get("data", {})
