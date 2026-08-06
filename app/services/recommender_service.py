from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job, JobStatus
from app.models.user_job_feedback import UserJobFeedback, UserFeedbackAction
from app.services.company_ranking_service import CompanyRankingService
from app.core.logging import logger


class RecommenderService:
    """Motor de recomendación adaptativo que aprende del feedback del candidato (likes/descartes)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recommended_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene las ofertas laborales ordenadas por afinidad adaptativa y ranking multidimensional."""
        # 1. Obtener feedbacks previos (solo campos necesarios)
        fb_res = await self.db.execute(select(UserJobFeedback.action, UserJobFeedback.technologies))
        feedbacks = fb_res.all()

        # Calcular ponderaciones de tecnologías basadas en acciones
        tech_weights: Dict[str, float] = {}
        for action, technologies in feedbacks:
            weight_change = 0.0
            if action == UserFeedbackAction.APPLIED:
                weight_change = 2.0
            elif action == UserFeedbackAction.SAVED:
                weight_change = 1.0
            elif action == UserFeedbackAction.DISMISSED:
                weight_change = -2.5

            for tech in (technologies or []):
                t_lower = tech.lower()
                tech_weights[t_lower] = tech_weights.get(t_lower, 0.0) + weight_change

        # 2. Obtener empleos activos
        jobs_res = await self.db.execute(select(Job).where(Job.status != JobStatus.REJECTED).limit(limit * 2))
        jobs = jobs_res.scalars().all()

        scored_jobs = []
        for job in jobs:
            ranking = CompanyRankingService.calculate_ranking(job)
            base_score = ranking["total_score"]

            # Aplicar ajuste de feedback por tecnología
            feedback_bonus = 0.0
            for tech in (job.technologies or []):
                feedback_bonus += tech_weights.get(tech.lower(), 0.0)

            final_score = round(max(0.0, min(10.0, base_score + (feedback_bonus * 0.2))), 1)

            scored_jobs.append({
                "job": job,
                "ranking_score": final_score,
                "ranking_details": ranking,
                "feedback_bonus": round(feedback_bonus, 1)
            })

        # Ordenar por puntaje final de recomendación descendente
        scored_jobs.sort(key=lambda x: x["ranking_score"], reverse=True)
        return scored_jobs[:limit]

    async def register_feedback(self, job_id: int, action: Any) -> Dict[str, Any]:
        """Registra la interacción del usuario con una oferta (SAVED, DISMISSED, APPLIED)."""
        if isinstance(action, str):
            try:
                action_enum = UserFeedbackAction(action.upper())
            except ValueError:
                action_enum = UserFeedbackAction.SAVED
        else:
            action_enum = action

        job_res = await self.db.execute(select(Job).where(Job.id == job_id))
        job = job_res.scalar_one_or_none()
        if not job:
            return {"error": f"Oferta #{job_id} no encontrada."}

        fb = UserJobFeedback(
            job_id=job_id,
            action=action_enum,
            technologies=job.technologies or []
        )
        self.db.add(fb)

        if action_enum == UserFeedbackAction.DISMISSED:
            job.status = JobStatus.REJECTED

        await self.db.commit()
        logger.info(f"Feedback registrado para job #{job_id}: {action_enum.value}")
        return {"success": True, "job_id": job_id, "action": action_enum.value}
