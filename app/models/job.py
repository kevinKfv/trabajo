import enum
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import String, Text, Boolean, Integer, Float, JSON, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class JobStatus(str, enum.Enum):
    NEW = "NEW"
    ANALYZED = "ANALYZED"
    NOTIFIED = "NOTIFIED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    ARCHIVED = "ARCHIVED"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    salary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remote: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    seniority: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, index=True)
    published_date: Mapped[Optional[datetime]] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Control de Estado y Auditoría
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.NEW, nullable=False, index=True
    )
    
    # Análisis de Inteligencia Artificial
    ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_title_company", "title", "company"),
    )
