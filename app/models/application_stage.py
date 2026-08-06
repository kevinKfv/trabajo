import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class CRMStage(str, enum.Enum):
    APPLIED = "POSTULADO"
    HR_CONTACT = "CONTACTO_RRHH"
    TECH_INTERVIEW = "ENTREVISTA_TECNICA"
    CODE_CHALLENGE = "DESAFIO_CODIGO"
    OFFER_RECEIVED = "OFERTA_RECIBIDA"
    ACCEPTED = "ACEPTADO"
    REJECTED = "RECHAZADO"


class ApplicationStage(Base):
    """Modelo ORM para el seguimiento de la etapa de reclutamiento (CRM de Gestión de Carrera)."""
    __tablename__ = "application_stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    stage: Mapped[CRMStage] = mapped_column(
        Enum(CRMStage), default=CRMStage.APPLIED, nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_contact_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    interview_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    salary_offered: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
