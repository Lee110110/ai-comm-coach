from pydantic import BaseModel
from datetime import datetime


class PatternCurrent(BaseModel):
    dimensions: dict[str, float]
    data_source_count: int
    last_computed_at: datetime | None

    model_config = {"from_attributes": True}


class InsightOut(BaseModel):
    id: int
    insight_type: str
    category: str
    title: str
    description: str
    evidence: list[str] | None = None
    suggested_practice: str | None = None
    is_read: bool

    model_config = {"from_attributes": True}


class PatternTrend(BaseModel):
    periods: list[str]
    dimensions: dict[str, list[float]]