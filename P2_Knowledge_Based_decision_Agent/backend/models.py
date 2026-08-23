from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    conversation: list[dict] = []
    conversation_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=10)


class Source(BaseModel):
    title: str
    source: str
    preview: str = ""
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    conversation_id: str
    model: str
