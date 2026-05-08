from pydantic import BaseModel, Field
from datetime import datetime


class MessagePolishRequest(BaseModel):
    original_message: str = Field(min_length=1)
    context: str | None = None
    relationship_id: int | None = None
    tone: str | None = None


class Change(BaseModel):
    original: str
    polished: str
    reason: str


class AlternativeVersion(BaseModel):
    tone: str
    message: str


class MessagePolishOut(BaseModel):
    id: int
    original_message: str
    polished_message: str | None
    changes: list[Change] | None = None
    alternative_versions: list[AlternativeVersion] | None = None
    tone: str | None
    created_at: datetime

    model_config = {"from_attributes": True}