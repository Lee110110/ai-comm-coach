from pydantic import BaseModel, Field
from datetime import datetime


class SimulationCreate(BaseModel):
    scenario_description: str = Field(min_length=1)
    relationship_id: int | None = None
    role_description: str | None = None
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class SimulationMessageSend(BaseModel):
    content: str = Field(min_length=1)


class DifficultyUpdate(BaseModel):
    difficulty: str = Field(pattern="^(easy|medium|hard)$")


class Feedback(BaseModel):
    score: int
    positives: list[str]
    suggestions: list[str]
    emotional_tone: str


class SimulationMessageOut(BaseModel):
    id: int
    role: str
    content: str
    feedback: Feedback | None = None
    turn_number: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SimulationOut(BaseModel):
    id: int
    scenario_description: str
    role_description: str | None
    difficulty: str
    status: str
    turn_count: int
    overall_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DebriefOut(BaseModel):
    overall_score: float
    summary: str
    strengths: list[str]
    improvements: list[str]
    dimension_scores: dict[str, float]
    recommended_practice: str