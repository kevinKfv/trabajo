from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class UserCVVersion(Base):
    """Modelo ORM para almacenar múltiples versiones del CV del usuario (Ej: CV Backend, CV Data Science)."""
    __tablename__ = "user_cv_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="CV Principal")
    target_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Ej: Backend, Data Science, DevOps
    
    cv_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cv_file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    cv_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    
    # Secciones extraídas del CV
    skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    experience: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    education: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    languages: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    certifications: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
