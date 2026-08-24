from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from tavily import TavilyClient


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

tavily_client = None

if TAVILY_API_KEY:
    tavily_client = TavilyClient(
        api_key=TAVILY_API_KEY
    )


# ============================================================
# TRUSTED ISLAMIC SOURCE DOMAINS
# ============================================================

QURAN_DOMAINS = {
    "quran.com",
    "corpus.quran.com",
}

HADITH_DOMAINS = {
    "sunnah.com",
}

TAFSIR_DOMAINS = {
    "altafsir.com",
}

ACADEMIC_DOMAIN_HINTS = {
    ".edu",
    ".ac.",
    "jstor.org",
    "cambridge.org",
    "oxford",
    "brill.com",
}


# ============================================================
# SOURCE CLASSIFICATION
# ============================================================

def classify_source(
    title: str,
    url: str,
    snippet: str,
) -> str:

    combined = (
        f"{title} {url} {snippet}"
    ).lower()

    # --------------------------------------------------------
    # Quran
    # --------------------------------------------------------

    if any(
        domain in combined
        for domain in QURAN_DOMAINS
    ):
        return "Quran"

    # --------------------------------------------------------
    # Hadith
    # --------------------------------------------------------

    if any(
        domain in combined
        for domain in HADITH_DOMAINS
    ):
        return "Hadith"

    # --------------------------------------------------------
    # Tafsir
    # --------------------------------------------------------

    if any(
        domain in combined
        for domain in TAFSIR_DOMAINS
    ):
        return "Tafsir"

    if any(
        keyword in combined
        for keyword in [
            "tafsir",
            "ibn kathir",
            "ibn kathīr",
            "al-tabari",
            "al tabari",
            "qurtubi",
            "al-qurtubi",
        ]
    ):
        return "Tafsir"

    # --------------------------------------------------------
    # Academic
    # --------------------------------------------------------

    if any(
        hint in combined
        for hint in ACADEMIC_DOMAIN_HINTS
    ):
        return "Academic"

    if any(
        keyword in combined
        for keyword in [
            "academic journal",
            "peer reviewed",
            "research paper",
            "islamic studies",
            "university research",
        ]
    ):
        return "Academic"

    # --------------------------------------------------------
    # General
    # --------------------------------------------------------

    return "General"


# ============================================================
# SEARCH QUERY BUILDER
# ============================================================

def build_query(
    question: str,
    mode: str,
) -> str:

    question = question.strip()

    if mode == "Quick Research":

        return (
            f"{question} "
            "Islam Quran Hadith"
        )

    if mode == "Deep Research":

        return (
            f"{question} "
            "Islam Quran Hadith tafsir "
            "Islamic scholarship sources"
        )

    if mode == "Quran & Hadith Research":

        return (
            f"{question} "
            "Quran verses Hadith Sunnah "
            "Islamic sources"
        )

    if mode == "Scholarly Research":

        return (
            f"{question} "
            "Islamic studies academic research "
            "peer reviewed scholarship Quran Hadith"
        )

    return (
        f"{question} "
        "Islam Quran Hadith tafsir"
    )


# ============================================================
# SEARCH DEPTH
# ============================================================

def get_search_depth(
    mode: str,
) -> str:

    if mode in {
        "Deep Research",
        "Scholarly Research",
    }:
        return "advanced"

    return "basic"


# ============================================================
# SOURCE COUNTS
# ============================================================

def empty_source_counts():

    return {
        "Quran": 0,
        "Hadith": 0,
        "Tafsir": 0,
        "Academic": 0,
        "General": 0,
    }


# ============================================================
# MAIN ISLAMIC RESEARCH ENGINE
# ============================================================

def research(
    question: str,
    mode: str = "Quick Research",
) -> dict[str, Any]:

    question = question.strip()

    # --------------------------------------------------------
    # Validate question
    # --------------------------------------------------------

    if not question:

        return {
            "note": (
                "Please enter an Islamic research "
                "question."
            ),
            "source_counts": empty_source_counts(),
            "sources": [],
        }

    # --------------------------------------------------------
    # Check Tavily configuration
    # --------------------------------------------------------

    if tavily_client is None:

        return {
            "note": (
                "Tavily is not configured. "
                "Add TAVILY_API_KEY to your .env file "
                "and restart Streamlit."
            ),
            "source_counts": empty_source_counts(),
            "sources": [],
        }

    # --------------------------------------------------------
    # Build query
    # --------------------------------------------------------

    query = build_query(
        question,
        mode,
    )

    search_depth = get_search_depth(
        mode
    )

    # --------------------------------------------------------
    # Tavily search
    # --------------------------------------------------------

    try:

        response = tavily_client.search(
            query=query,
            search_depth=search_depth,
            max_results=10,
            include_answer=False,
            include_raw_content=False,
        )

    except Exception as exc:

        return {
            "note": (
                "Tavily search failed: "
                f"{exc}"
            ),
            "source_counts": empty_source_counts(),
            "sources": [],
        }

    # --------------------------------------------------------
    # Extract results
    # --------------------------------------------------------

    results = response.get(
        "results",
        [],
    )

    sources = []

    for item in results:

        title = (
            item.get("title")
            or "Untitled source"
        )

        url = (
            item.get("url")
            or ""
        )

        snippet = (
            item.get("content")
            or ""
        )

        source_type = classify_source(
            title,
            url,
            snippet,
        )

        sources.append(
            {
                "source_type": source_type,
                "title": title,
                "snippet": snippet,
                "url": url,
            }
        )

    # --------------------------------------------------------
    # Count sources
    # --------------------------------------------------------

    source_counts = (
        empty_source_counts()
    )

    for source in sources:

        source_type = source.get(
            "source_type",
            "General",
        )

        if source_type in source_counts:

            source_counts[
                source_type
            ] += 1

    # --------------------------------------------------------
    # Research note
    # --------------------------------------------------------

    if sources:

        note = (
            f"Found {len(sources)} web source(s) "
            f"using {mode}. Results are retrieved "
            "evidence organized by the Islamic "
            "research layer. They are not a fatwa "
            "or a substitute for qualified scholarly "
            "guidance."
        )

    else:

        note = (
            "No web results were returned. "
            "Try a broader or differently worded "
            "research question."
        )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {
        "note": note,
        "source_counts": source_counts,
        "sources": sources,
        "query": query,
        "mode": mode,
    }