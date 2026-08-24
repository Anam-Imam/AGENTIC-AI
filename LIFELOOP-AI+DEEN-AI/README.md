# LIFELOOP AI — PRISM DESK + Deen AI

Project 7 — Independent Agentic AI System.

This build preserves the Prism Desk concept and adds a Deen AI module with three testable capabilities:

- Prayer Intelligence — city or coordinate based prayer timings, next prayer, countdown and Hijri date.
- Quran Intelligence — no-key Quran search using a public Quran retrieval API.
- Islamic Research Agent — web search, source classification and evidence display.

## Core LIFELOOP capabilities

- Smart Composer / Recovery Engine
- Long-Term Memory
- Memory Genome
- Promise Radar
- Loop Health Score
- Risk Radar
- Dependency Chain
- People Map
- Contradiction Detector
- Memory Decay Detection
- What-If Simulator
- Recovery Mission
- Explainable Agent Trace
- Human Approval Gate
- Previous Sessions
- Favorites
- Activity / Daily Briefing
- Delete one memory
- Delete all memories
- JSON/CSV export
- Local persistent storage

## Run

```bash
python -m venv .venv
```

Windows:

```bash
.venv\\Scripts\\activate
```

Install:

```bash
pip install -r requirements.txt
```

Start:

```bash
streamlit run app.py
```

## Data

The application creates these files under `data/` as needed:

- `memories.json`
- `memory_versions.json`
- `scenarios.json`
- `decisions.json`
- `approvals.json`
- `activity.json`

No API key is required for the core LIFELOOP features.

## Deen AI notes

Prayer timings are retrieved from AlAdhan and are configurable by calculation method and Asr school. Quran search uses a public Quran retrieval endpoint. Islamic Research uses web search and labels sources by type. The research layer is informational and does not automatically issue religious rulings; source differences should be reviewed with a qualified scholar.

## Suggested tests

1. Prism Desk → ask: `What commitments have I forgotten?`
2. Click `✦ Send through prism`.
3. Click `↻ Reset desk` and confirm the composer/result clear.
4. Memory → save a memory → delete selected memory.
5. Memory → delete all → confirm.
6. Deen AI → Prayer Times → enter a city and load timings.
7. Deen AI → Al-Quran → search `patience`.
8. Deen AI → Islamic Research → search a topic.
