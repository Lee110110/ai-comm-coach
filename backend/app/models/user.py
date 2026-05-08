from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    scenarios: Mapped[list["Scenario"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    simulations: Mapped[list["SimulationSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    messages: Mapped[list["MessagePolish"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    relationships: Mapped[list["RelationshipProfile"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    patterns: Mapped[list["CommunicationPattern"]] = relationship(back_populates="user", cascade="all, delete-orphan")