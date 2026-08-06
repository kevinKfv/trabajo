import enum
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class UserFeedbackAction(str, enum.Enum):
    SAVED = "SAVED"
    DISMISSED = "DISMISSED"
    APPLIED = "APPLIED"


class UserJobFeedback(Base):
    """Modelo ORM para registrar la interacción del usuario con las ofertas (para el motor de recomendación)."""
    __tablename__ = "user_job_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action: Mapped[UserFeedbackAction] = mapped_column(
        Enum(UserFeedbackAction), nullable=False, index=True
    )
    technologies: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
