from sqlalchemy import String, Integer, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base, TimestampMixin


class SimulationSession(Base, TimestampMixin):
    __tablename__ = "simulation_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("relationship_profiles.id"), nullable=True)
    scenario_description: Mapped[str] = mapped_column(Text, nullable=False)
    role_description: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="active")
    turn_count: Mapped[int] = mapped_column(default=0)

    overall_score: Mapped[float | None] = mapped_column(Float)
    debrief_summary: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[str | None] = mapped_column(Text)
    improvements: Mapped[str | None] = mapped_column(Text)
    dimension_scores: Mapped[str | None] = mapped_column(Text)
    recommended_practice: Mapped[str | None] = mapped_column(Text)

    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship(back_populates="simulations")
    messages: Mapped[list["SimulationMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="SimulationMessage.turn_number")


class SimulationMessage(Base):
    __tablename__ = "simulation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulation_sessions.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text)
    turn_number: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    session: Mapped["SimulationSession"] = relationship(back_populates="messages")