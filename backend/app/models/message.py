from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class MessagePolish(Base, TimestampMixin):
    __tablename__ = "message_polishes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("relationship_profiles.id"), nullable=True)
    original_message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text)
    tone: Mapped[str | None] = mapped_column(String(50))

    polished_message: Mapped[str | None] = mapped_column(Text)
    changes: Mapped[str | None] = mapped_column(Text)
    alternative_versions: Mapped[str | None] = mapped_column(Text)

    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship(back_populates="messages")