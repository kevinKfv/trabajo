from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class SearchConfig(Base):
    __tablename__ = "search_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    keywords: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    sources: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)  # linkedin, bumeran, computrabajo
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remote_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seniorities: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False) # Trainee, Junior, Pasantia, etc.
    exclude_keywords: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False) # PHP, WordPress, etc.
    min_salary: Mapped[Optional[float]] = mapped_column(JSON, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="ARS", nullable=False)
    frequency_hours: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    date_filter: Mapped[str] = mapped_column(String(50), default="all", nullable=False)
    target_cv_version_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
