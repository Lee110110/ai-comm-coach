from sqlalchemy import String, Integer, Float, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base, TimestampMixin


class CommunicationPattern(Base, TimestampMixin):
    __tablename__ = "communication_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    assertiveness: Mapped[float] = mapped_column(Float, default=50.0)
    empathy: Mapped[float] = mapped_column(Float, default=50.0)
    clarity: Mapped[float] = mapped_column(Float, default=50.0)
    adaptability: Mapped[float] = mapped_column(Float, default=50.0)
    conflict_handling: Mapped[float] = mapped_column(Float, default=50.0)
    active_listening: Mapped[float] = mapped_column(Float, default=50.0)

    data_source_count: Mapped[int] = mapped_column(default=0)
    last_computed_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="patterns")
    insights: Mapped[list["PatternInsight"]] = relationship(back_populates="pattern", cascade="all, delete-orphan")


class PatternInsight(Base, TimestampMixin):
    __tablename__ = "pattern_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    pattern_id: Mapped[int] = mapped_column(Integer, ForeignKey("communication_patterns.id"), nullable=False)

    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    suggested_practice: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    pattern: Mapped["CommunicationPattern"] = relationship(back_populates="insights")