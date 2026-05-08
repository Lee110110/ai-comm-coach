from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Scenario(Base, TimestampMixin):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("relationship_profiles.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text)
    relationship_type: Mapped[str | None] = mapped_column(String(50))
    urgency: Mapped[str] = mapped_column(String(20), default="medium")

    strategy_gentle: Mapped[str | None] = mapped_column(Text)
    strategy_direct: Mapped[str | None] = mapped_column(Text)
    strategy_strategic: Mapped[str | None] = mapped_column(Text)
    pitfalls: Mapped[str | None] = mapped_column(Text)
    predicted_reactions: Mapped[str | None] = mapped_column(Text)

    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship(back_populates="scenarios")