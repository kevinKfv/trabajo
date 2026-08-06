from typing import Optional, List
from sqlalchemy import String, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Candidato")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Datos de CV
    cv_file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    cv_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cv_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cv_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    cover_letter_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
