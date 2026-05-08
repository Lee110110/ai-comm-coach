from pydantic import BaseModel, Field
from datetime import datetime


class ScenarioCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    context: str | None = None
    relationship_id: int | None = None
    relationship_type: str | None = None
    urgency: str = Field(default="medium", pattern="^(low|medium|high)$")


class Strategy(BaseModel):
    title: str
    approach: str
    scripts: list[str]
    when_to_use: str


class Pitfall(BaseModel):
    warning: str
    why: str
    alternative: str


class PredictedReaction(BaseModel):
    reaction: str
    probability: str
    how_to_handle: str


class ScenarioOut(BaseModel):
    id: int
    title: str
    description: str
    context: str | None
    relationship_type: str | None
    urgency: str
    strategies: dict[str, Strategy] | None = None
    pitfalls: list[Pitfall] | None = None
    predicted_reactions: list[PredictedReaction] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioListItem(BaseModel):
    id: int
    title: str
    description: str
    relationship_type: str | None
    urgency: str
    created_at: datetime

    model_config = {"from_attributes": True}