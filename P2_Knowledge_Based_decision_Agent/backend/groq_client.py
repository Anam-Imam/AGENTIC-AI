from collections.abc import Iterator
from groq import Groq
from .config import GROQ_API_KEY, GROQ_MODEL

SYSTEM_PROMPT = """You are a Knowledge-Based Decision Agent.

Use the private knowledge-base context supplied by the retrieval system.
Never invent private policies, facts, dates, numbers or procedures.
If the context is insufficient, say that the private knowledge base does not contain enough information.
For decisions, give a clear recommendation and a concise evidence-based rationale.
Do not reveal hidden chain-of-thought. Provide only the useful decision rationale.
Use Markdown when helpful.
"""


def client() -> Groq:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to .env.")
    return Groq(api_key=GROQ_API_KEY)


def stream_answer(messages: list[dict]) -> Iterator[str]:
    stream = client().chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.2,
        max_completion_tokens=1600,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def answer(messages: list[dict]) -> str:
    return "".join(stream_answer(messages))
