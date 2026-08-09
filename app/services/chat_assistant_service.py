from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job
from app.models.user_profile import UserProfile
from app.ai.factory import AIFactory
from app.core.logging import logger


class ChatAssistantService:
    """Asistente de IA Conversacional para consultas en lenguaje natural sobre la base de datos de empleos."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_provider = AIFactory.get_provider()

    async def answer_user_query(self, query: str, device_id: str = "global") -> Dict[str, Any]:
        """Procesa una pregunta del usuario y retorna una respuesta relevante y estructurada."""
        query_lower = query.lower()
        logger.info(f"Procesando consulta de Chat IA: '{query}'")

        # 1. Obtener contexto de empleos y perfil
        jobs_res = await self.db.execute(select(Job).where(Job.device_id == device_id).limit(20))
        jobs = jobs_res.scalars().all()

        profile_res = await self.db.execute(select(UserProfile).where(UserProfile.device_id == device_id).limit(1))
        profile = profile_res.scalar_one_or_none()

        job_summaries = [f"- {j.title} en {j.company} ({j.source.upper()}, Match: {j.ai_score or 0}%, {j.location or 'Remoto'})" for j in jobs[:10]]
        context_str = "\n".join(job_summaries) if job_summaries else "Sin empleos en la base de datos."

        prompt_context = f"Responde a la siguiente consulta sobre las ofertas de trabajo disponibles:\n\nCONSULTA: '{query}'\n\nOFFERTAS DISPONIBLES:\n{context_str}"

        try:
            ai_res = await self.ai_provider.analyze_job(
                job_description=prompt_context,
                cv_text=profile.cv_text if (profile and profile.cv_text) else "Desarrollador de Software"
            )

            # Generar respuesta amigable
            answer = f"🤖 **Respuesta del Asistente IA**:\n\n{ai_res.summary}\n\n💡 **Recomendación**: {ai_res.recommendation}.\n\n📌 **Ofertas Relevantes**:\n{context_str}"

            return {
                "query": query,
                "answer": answer,
                "suggested_jobs": [j.title for j in jobs[:3]]
            }

        except Exception as e:
            logger.error(f"Error en Chat Assistant: {e}")
            return {
                "query": query,
                "answer": f"🤖 Encontré **{len(jobs)} ofertas** registradas en el sistema. Puedes explorarlas en la pestaña 'Empleos & Feed'.",
                "suggested_jobs": []
            }
