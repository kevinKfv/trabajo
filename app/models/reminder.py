import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class ReminderType(str, enum.Enum):
    INTERVIEW = "ENTREVISTA"
    FOLLOW_UP = "SEGUIMIENTO"
    CHALLENGE_DEADLINE = "ENTREGA_CHALLENGE"


class Reminder(Base):
    """Modelo ORM para alertas y recordatorios de entrevistas o correos de seguimiento."""
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    reminder_type: Mapped[ReminderType] = mapped_column(
        Enum(ReminderType), default=ReminderType.INTERVIEW, nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
