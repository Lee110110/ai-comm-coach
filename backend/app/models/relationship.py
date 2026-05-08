from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base, TimestampMixin


class RelationshipProfile(Base, TimestampMixin):
    __tablename__ = "relationship_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar_emoji: Mapped[str | None] = mapped_column(String(10))
    communication_style: Mapped[str | None] = mapped_column(Text)
    preferences: Mapped[str | None] = mapped_column(Text)
    avoid_topics: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    last_interaction_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="relationships")
    interactions: Mapped[list["InteractionRecord"]] = relationship(back_populates="relationship", cascade="all, delete-orphan")


class InteractionRecord(Base, TimestampMixin):
    __tablename__ = "interaction_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    relationship_id: Mapped[int] = mapped_column(Integer, ForeignKey("relationship_profiles.id"), nullable=False)
    scenario_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("scenarios.id"), nullable=True)
    simulation_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("simulation_sessions.id"), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(50))
    tags: Mapped[str | None] = mapped_column(Text)

    relationship: Mapped["RelationshipProfile"] = relationship(back_populates="interactions")