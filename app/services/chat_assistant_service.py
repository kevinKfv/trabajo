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
        jobs_res = await self.db.execute(
            select(Job)
            .where(Job.device_id == device_id)
            .order_by(Job.ai_score.desc().nullslast(), Job.id.desc())
            .limit(30)
        )
        jobs = jobs_res.scalars().all()

        profile_res = await self.db.execute(select(UserProfile).where(UserProfile.device_id == device_id).limit(1))
        profile = profile_res.scalar_one_or_none()

        job_summaries = [
            f"- {j.title} en {j.company} ({j.source.upper()}, Match: {j.ai_score or 0}%, Ubicación: {j.location or 'Remoto'}) | URL/Link de postulación: {j.url}"
            for j in jobs[:20]
        ]
        context_str = "\n".join(job_summaries) if job_summaries else "Sin empleos en la base de datos."

        cv_summary = profile.cv_text if (profile and profile.cv_text) else "Perfil de desarrollador de software sin CV detallado."

        system_prompt = (
            "Eres el Asistente Conversacional Inteligente de Job Hunter AI.\n"
            "Tu misión es ayudar al candidato con orientación profesional y recomendaciones sobre las ofertas laborales disponibles en su cuenta.\n"
            "REGLAS:\n"
            "1. Responde directamente y amablemente a la consulta del usuario.\n"
            "2. Usa formato Markdown limpio (negritas, listas con viñetas, emojis) para que sea visualmente atractivo.\n"
            "3. Si te pide empleos o recomendaciones, analiza las mejores opciones disponibles de la lista y destaca sus puntos fuertes.\n"
            "4. Si el usuario te pide links, enlaces o URLs para postularse, inclúyelos en tu respuesta usando el formato Markdown [Postularme a Título](URL) o indicando la URL directamente.\n"
            "5. Sé profesional, entusiasta y conciso."
        )

        user_prompt = (
            f"CONSULTA DEL USUARIO: '{query}'\n\n"
            f"PERFIL / CV DEL CANDIDATO:\n{cv_summary[:1000]}\n\n"
            f"OFERTAS LABORAL DISPONIBLES EN SU CUENTA CON SUS LINKS DE POSTULACIÓN:\n{context_str}"
        )

        try:
            answer_text = await self.ai_provider.chat_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            return {
                "query": query,
                "answer": answer_text,
                "suggested_jobs": []
            }

        except Exception as e:
            logger.error(f"Error en Chat Assistant: {e}", exc_info=True)
            return {
                "query": query,
                "answer": f"🤖 Encontré **{len(jobs)} ofertas** registradas en el sistema. Puedes explorarlas en la pestaña 'Empleos & Feed'.",
                "suggested_jobs": []
            }

