from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AIAnalysisResult(BaseModel):
    summary: str = Field(..., description="Resumen conciso de la oferta laboral")
    technologies: list[str] = Field(default_factory=list, description="Tecnologías extraídas")
    seniority: Optional[str] = Field(None, description="Seniority detectado")
    match_score: float = Field(..., ge=0, le=100, description="Puntaje de compatibilidad 0-100")
    reasoning: str = Field(..., description="Explicación detallada de coincidencia con el CV")
    advantages: list[str] = Field(default_factory=list, description="Fortalezas y coincidencias detectadas (✔ Python, Docker)")
    missing_skills: list[str] = Field(default_factory=list, description="Requisitos o tecnologías faltantes (• AWS, Kubernetes)")
    interview_probability: str = Field("Alta", description="Probabilidad estimada de llamada a entrevista: Alta, Media, Baja")
    recommendation: str = Field("Aplicar inmediatamente", description="Recomendación final: Aplicar inmediatamente, Revisar requisitos, Descartar")


class BaseAIProvider(ABC):
    """Interfaz abstracta base para servicios de análisis con IA (OpenAI, Ollama, etc.)."""

    @abstractmethod
    async def analyze_job(self, job_description: str, cv_text: str) -> AIAnalysisResult:
        """Analiza una oferta laboral comparándola contra el CV del usuario."""
        pass

    @abstractmethod
    async def extract_cv_skills(self, cv_text: str) -> list[str]:
        """Extrae la lista de habilidades técnicas y blandas desde el texto de un CV."""
        pass
