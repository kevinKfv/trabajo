from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job
from app.models.user_profile import UserProfile
from app.ai.factory import AIFactory
from app.core.logging import logger


class CoverLetterService:
    """Servicio para la generación de cartas de presentación hiper-personalizadas para cada empleo."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_provider = AIFactory.get_provider()

    async def generate_cover_letter(self, job_id: int) -> Dict[str, Any]:
        """Genera una carta de presentación única y personalizada para la oferta laboral dada."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return {"error": f"La oferta laboral #{job_id} no fue encontrada."}

        prof_res = await self.db.execute(select(UserProfile).limit(1))
        profile = prof_res.scalar_one_or_none()

        candidate_name = profile.full_name if (profile and profile.full_name) else "Candidato"
        candidate_email = profile.email if (profile and profile.email) else ""
        candidate_phone = profile.phone if (profile and profile.phone) else ""
        cv_text = profile.cv_text if (profile and profile.cv_text) else ""

        logger.info(f"Generando Carta de Presentación para '{job.title}' en {job.company}...")

        try:
            ai_res = await self.ai_provider.analyze_job(
                job_description=f"Genera carta de presentación para {job.title} en {job.company}:\n{job.description}",
                cv_text=cv_text
            )

            techs_mentioned = ", ".join(job.technologies[:4]) if job.technologies else "tecnologías clave"
            summary_hook = ai_res.summary or f"la búsqueda del puesto de {job.title}"

            cover_letter_text = f"""Estimado equipo de Selección de {job.company},

Me dirijo a ustedes con gran entusiasmo para presentar mi postulación a la posición de {job.title}. He seguido con atención las búsquedas de {job.company} y considero que mi perfil técnico se alinea fuertemente con los requerimientos y objetivos del equipo.

Revisando la oferta laboral, destaco la importancia de contar con sólidos conocimientos en {techs_mentioned}. En mi trayectoria profesional he trabajado activamente desarrollando soluciones eficientes, optimizando procesos y garantizando la calidad del código en entornos colaborativos.

Agradezco de antemano el tiempo dedicado a revisar mi postulación. Quedo a su entera disposición para mantener una entrevista en la que pueda profundizar sobre cómo mis habilidades pueden aportar valor inmediato a {job.company}.

Atentamente,

{candidate_name}
{candidate_email} {f'| {candidate_phone}' if candidate_phone else ''}
"""

            return {
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company,
                "cover_letter_text": cover_letter_text.strip()
            }

        except Exception as e:
            logger.error(f"Error generando Carta de Presentación: {e}")
            fallback_letter = f"""Estimado equipo de {job.company},

Les escribo para expresar mi interés en la búsqueda de {job.title}. Cuento con experiencia sólida en desarrollo de software y motivación para aportar mis conocimientos en su equipo.

Quedo a su disposición para coordinar una entrevista.

Saludos cordiales,
{candidate_name}
{candidate_email}"""
            return {
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company,
                "cover_letter_text": fallback_letter
            }
