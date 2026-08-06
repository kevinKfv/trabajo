from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, HttpUrl, ConfigDict, Field
from app.models.job import JobStatus


class JobBase(BaseModel):
    title: str = Field(..., description="Título de la posición")
    company: str = Field(..., description="Nombre de la empresa contratante")
    location: Optional[str] = Field(None, description="Ubicación (ciudad, país)")
    salary: Optional[str] = Field(None, description="Rango salarial si está especificado")
    remote: Optional[bool] = Field(False, description="Indicador de trabajo remoto")
    seniority: Optional[str] = Field(None, description="Nivel de experiencia (Junior, Semi-Senior, Senior, Lead)")
    description: str = Field(..., description="Descripción completa del empleo")
    technologies: list[str] = Field(default_factory=list, description="Lista de tecnologías detectadas")
    url: str = Field(..., description="URL original de la publicación")
    published_date: Optional[str] = Field(None, description="Fecha de publicación informada")
    source: str = Field(..., description="Plataforma de origen (ej: linkedin, bumeran, computrabajo)")


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    remote: Optional[bool] = None
    seniority: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[list[str]] = None
    status: Optional[JobStatus] = None
    ai_score: Optional[float] = None
    ai_summary: Optional[str] = None
    ai_analysis: Optional[dict[str, Any]] = None


class JobResponse(JobBase):
    id: int
    status: JobStatus
    ai_score: Optional[float] = None
    ai_summary: Optional[str] = None
    ai_analysis: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobStatsResponse(BaseModel):
    total_jobs: int
    jobs_by_source: dict[str, int]
    jobs_by_status: dict[str, int]
    remote_jobs_count: int
    high_match_jobs_count: int
