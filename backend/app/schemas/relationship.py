from pydantic import BaseModel, Field
from datetime import datetime


class RelationshipCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    relation_type: str = Field(min_length=1, max_length=50)
    avatar_emoji: str | None = None
    communication_style: list[str] | None = None
    preferences: list[str] | None = None
    avoid_topics: list[str] | None = None
    notes: str | None = None


class RelationshipUpdate(BaseModel):
    name: str | None = None
    relation_type: str | None = None
    avatar_emoji: str | None = None
    communication_style: list[str] | None = None
    preferences: list[str] | None = None
    avoid_topics: list[str] | None = None
    notes: str | None = None


class CommunicationStrategy(BaseModel):
    overall_approach: str
    do_list: list[str]
    dont_list: list[str]
    opening_style: str
    conflict_approach: str


class InteractionOut(BaseModel):
    id: int
    summary: str
    outcome: str | None
    tags: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RelationshipOut(BaseModel):
    id: int
    name: str
    relation_type: str
    avatar_emoji: str | None
    communication_style: list[str] | None = None
    preferences: list[str] | None = None
    avoid_topics: list[str] | None = None
    notes: str | None
    last_interaction_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RelationshipDetail(RelationshipOut):
    recent_interactions: list[InteractionOut] = []
    strategy: CommunicationStrategy | None = None