from pydantic import BaseModel, Field
from typing import List

class DocumentResult(BaseModel):
    document_type: str
    title: str
    summary: str
    key_entities: List[str] = Field(default_factory=list)
    important_dates: List[str] = Field(default_factory=list)
    important_amounts: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
