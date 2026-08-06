from typing import Optional
from pydantic import BaseModel, Field
from app.models.job import JobStatus


class JobFilter(BaseModel):
    remote: Optional[bool] = Field(None, description="Filtrar por trabajo remoto")
    location: Optional[str] = Field(None, description="Filtrar por ciudad/ubicación")
    company: Optional[str] = Field(None, description="Filtrar por empresa")
    seniority: Optional[str] = Field(None, description="Filtrar por seniority")
    technology: Optional[str] = Field(None, description="Filtrar por tecnología requerida")
    source: Optional[str] = Field(None, description="Filtrar por plataforma de origen")
    min_ai_score: Optional[float] = Field(None, description="Puntaje mínimo de coincidencia IA (0-100)")
    status: Optional[JobStatus] = Field(None, description="Filtrar por estado del trabajo")
    search_query: Optional[str] = Field(None, description="Búsqueda por texto en título o descripción")
    date_filter: Optional[str] = Field(None, description="Filtro de fecha: today, week, all")

    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(20, ge=1, le=100, description="Cantidad por página")
