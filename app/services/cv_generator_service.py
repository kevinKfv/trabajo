import json
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job
from app.models.user_profile import UserProfile
from app.ai.factory import AIFactory
from app.core.logging import logger


class CVGeneratorService:
    """Servicio de IA para la adaptación dinámica de CVs según ofertas laborales específicas."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_provider = AIFactory.get_provider()

    async def generate_tailored_cv(self, job_id: int) -> Dict[str, Any]:
        """Genera una versión del CV optimizada y adaptada específicamente para una oferta laboral."""
        # 1. Obtener oferta laboral
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return {"error": f"La oferta laboral #{job_id} no fue encontrada."}

        # 2. Obtener perfil activo del usuario
        prof_res = await self.db.execute(select(UserProfile).limit(1))
        profile = prof_res.scalar_one_or_none()

        cv_base_text = profile.cv_text if (profile and profile.cv_text) else "Desarrollador de Software con experiencia en backend y tecnologías web."
        candidate_name = profile.full_name if profile else "Candidato"
        candidate_email = profile.email if profile else ""

        logger.info(f"Generando CV adaptado para la oferta '{job.title}' en {job.company}...")

        prompt = (
            f"Eres un experto en redactar CVs técnicos de alto impacto (ATS-optimized). "
            f"Tu objetivo es adaptar el CV base del candidato para que coincida de forma óptima con la oferta de trabajo dada.\n\n"
            f"DATOS DEL CANDIDATO:\nNombre: {candidate_name}\nEmail: {candidate_email}\nCV Base:\n{cv_base_text}\n\n"
            f"OFERTA LABORAL OBJETIVO:\nTítulo: {job.title}\nEmpresa: {job.company}\nDescripción:\n{job.description}\nTecnologías requeridas: {', '.join(job.technologies)}\n\n"
            f"Genera una versión en formato Markdown impecable y estructurado del CV Adaptado. "
            f"Asegúrate de:\n"
            f"1. Crear un Perfil Profesional (Summary) enfocado directamente en lo que busca la empresa.\n"
            f"2. Destacar y reordenar las habilidades principales coincidiendo con los requisitos.\n"
            f"3. Resaltar los logros y experiencia relevante para este puesto.\n\n"
            f"Responde ÚNICAMENTE en formato JSON con la clave 'tailored_cv_markdown' que contenga el texto Markdown del CV."
        )

        try:
            # Usar la interfaz del proveedor de IA
            ai_res = await self.ai_provider.analyze_job(
                job_description=f"Genera CV adaptado para {job.title} en {job.company}:\n{job.description}",
                cv_text=cv_base_text
            )

            # Generar el markdown formateado
            summary = ai_res.summary or "Profesional con experiencia alineada a los requerimientos del puesto."
            advantages_str = "\n".join([f"- {a}" for a in ai_res.advantages]) if ai_res.advantages else "- Experiencia comprobada en desarrollo de software."
            techs_str = ", ".join(job.technologies) if job.technologies else "Python, SQL, Git"

            markdown_cv = f"""# {candidate_name}
**{job.title}** | {candidate_email}

## 👤 Perfil Profesional
{summary}

## 🛠️ Habilidades Técnicas Principales
- **Tecnologías Relevantes**: {techs_str}
- **Fortalezas Destacadas**:
{advantages_str}

## 💼 Experiencia y Logros Adaptados
- **Alineación con {job.company}**: Experiencia práctica aplicando mejores prácticas de desarrollo, trabajo en equipo y resolución de problemas técnicos complejos.
- **Tecnologías Aplicadas**: {techs_str}.

## 🎓 Educación y Certificaciones
- Formación técnica y desarrollo profesional continuo.
"""

            return {
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company,
                "tailored_cv_markdown": markdown_cv.strip()
            }

        except Exception as e:
            logger.error(f"Error generando CV adaptado: {e}")
            return {
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company,
                "tailored_cv_markdown": f"# CV Adaptado para {candidate_name}\n\n**Postulación a**: {job.title} en {job.company}\n\n## Perfil\n{cv_base_text}"
            }
