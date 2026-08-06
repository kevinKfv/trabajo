from typing import Dict, Any
from app.models.job import Job


class CompanyRankingService:
    """Servicio para la evaluación y ranking multidimensional de ofertas laborales (0-10)."""

    @classmethod
    def calculate_ranking(cls, job: Job) -> Dict[str, Any]:
        """Calcula el puntaje de ranking multidimensional de 0 a 10 para una oferta."""
        score_components = {}

        # 1. Puntaje por Coincidencia IA (0 - 4 puntos)
        ai_score = job.ai_score or 50.0
        score_components["ai_match"] = round((ai_score / 100.0) * 4.0, 1)

        # 2. Puntaje por Modalidad Remota (0 - 2 puntos)
        score_components["remote_flexibility"] = 2.0 if job.remote else 1.0

        # 3. Puntaje por Stack Técnico Relevante (0 - 2 puntos)
        tech_count = len(job.technologies) if job.technologies else 0
        score_components["tech_stack"] = min(round(tech_count * 0.4, 1), 2.0)

        # 4. Puntaje por Claridad / Reputación de Fuente (0 - 2 puntos)
        source_weight = {"linkedin": 2.0, "bumeran": 1.8, "computrabajo": 1.7}.get(job.source.lower(), 1.5)
        score_components["company_reputation"] = source_weight

        total_score = round(sum(score_components.values()), 1)
        total_score = min(total_score, 10.0)

        return {
            "total_score": total_score,
            "components": score_components,
            "badge_color": "green" if total_score >= 8.0 else ("gold" if total_score >= 6.0 else "gray")
        }
