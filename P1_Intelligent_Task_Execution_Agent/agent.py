import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# =========================================================
# LOAD ENVIRONMENT
# =========================================================

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

from langchain.agents import create_agent
from langchain_groq import ChatGroq

from tools import TOOLS


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are Nexa, an intelligent task execution agent.

Your job:
1. Understand the user's goal.
2. Break complex goals into smaller steps internally.
3. Select the appropriate tool(s) when tools can improve the result.
4. Observe tool results and decide whether another step is required.
5. Stop when you have enough information.
6. Give a concise, useful final answer.

Rules:
- Never claim a tool was used if it was not.
- For calculations, use the calculator tool rather than mental arithmetic when practical.
- For current or factual web information, use web_search when appropriate.
- Explain important assumptions.
- Do not expose hidden chain-of-thought.
- Provide only a short execution summary when useful.
"""


# =========================================================
# BUILD AGENT
# =========================================================

def build_agent():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add it to .env before running the app."
        )

    model = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=api_key,
    temperature=0.2,
    timeout=60,
    max_retries=2,
)

    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


# =========================================================
# MESSAGE TEXT HELPER
# =========================================================

def _message_text(message: Any) -> str:

    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
        )

    return str(content)


# =========================================================
# RUN AGENT
# =========================================================

def run_agent(goal: str) -> dict:

    agent = build_agent()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": goal,
                }
            ]
        }
    )

    messages = result.get("messages", [])

    answer = ""

    for msg in reversed(messages):

        if getattr(msg, "type", "") == "ai":

            text = _message_text(msg)

            if text.strip():
                answer = text
                break

    if not answer:
        answer = (
            "I completed the task but did not receive "
            "a final text response."
        )

    return {
        "answer": answer,
        "messages": messages,
    }


# =========================================================
# EXTRACT TOOL EVENTS
# =========================================================

def extract_tool_events(result: dict) -> list[dict]:

    events = []

    for msg in result.get("messages", []):

        if getattr(msg, "type", "") == "tool":

            name = getattr(
                msg,
                "name",
                "tool"
            )

            content = _message_text(msg)

            events.append(
                {
                    "tool": name,
                    "input": content,
                }
            )

    return events


# =========================================================
# EXTRACT SOURCES
# =========================================================

def extract_sources(result: dict) -> list[dict]:

    sources = []
    seen = set()

    for msg in result.get("messages", []):

        if getattr(msg, "type", "") != "tool":
            continue

        content = getattr(
            msg,
            "content",
            ""
        )

        if not isinstance(content, str):
            continue

        try:
            data = json.loads(content)

        except Exception:
            continue

        if isinstance(data, dict) and data.get("sources"):

            for source in data["sources"]:

                url = source.get(
                    "url",
                    ""
                )

                if url and url not in seen:

                    seen.add(url)
                    sources.append(source)

    return sources