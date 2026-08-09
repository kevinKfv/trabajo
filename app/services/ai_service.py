from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import AIFactory
from app.models.job import Job, JobStatus
from app.core.logging import logger

DEFAULT_CV = """
Nombre: Kevin Franco Villalba
Email: villalbakevinfranco@gmail.com | Celular: (011) 3259 4683
LinkedIn: https://www.linkedin.com/in/kevinfranco-villalba/
Certificaciones: https://n9.cl/certificacioneskevinvillalba

Perfil Profesional:
Soy organizado, responsable y con experiencia en trabajo en equipo; busco un puesto desafiante en Desarrollo de Software, Sysadmin/DevOps, Analista de Sistemas/Aplicaciones o Ciberseguridad para seguir creciendo profesionalmente.

Experiencia Laboral:
- Central Puerto (Marzo 2025 - Actualidad): Analista de Aplicaciones y Analista de Datos en Seeq. Monitoreo, optimización de procesos y administración del sistema Seeq.
- Desarrollador Freelance (Agos. 2024 - Actualidad): Desarrollo de soluciones personalizadas y aplicaciones web para pymes (interfaces, lógica de negocio y backend).
- Instituto Nac. de Cine y Artes Audiovisuales - INCAA (Abr 2021 - Dic 2024): Sysadmin (Administrator System). Responsable del desarrollo, mantenimiento y administración de aplicaciones internas. Gestión de servidores, respaldos, servicios y soporte técnico a usuarios finales (remoto y presencial).
- Algabo (May 2020 - Dic 2020): Pasantía en Desarrollo.

Educación:
- Ingeniería en Informática (2022 - Presente): Universidad De Las Empresas (Graduado con honores académicos).
- Tecnicatura en Informática (2015 - 2020): Otto Krause Escuela Técnica No. 1.

Certificaciones & Habilidades Clave:
- Ciberseguridad: Seguridad defensiva y ofensiva, Cisco CCNA, herramientas de seguridad.
- Cloud Computing & DevOps: Gestión de servicios en Amazon AWS y prácticas DevOps.
- Inteligencia Artificial: Aplicaciones prácticas en Machine Learning y Deep Learning.
- Idiomas: Español nativo, Inglés intermedio (oral y escrito).
"""



from app.models.user_profile import UserProfile

class AIService:
    """Servicio de evaluación de compatibilidad de ofertas laborales mediante IA."""

    def __init__(self, db: AsyncSession, cv_text: Optional[str] = None) -> None:
        self.db = db
        self.cv_text = cv_text
        self.ai_provider = AIFactory.get_provider()

    async def _get_active_cv_text(self, device_id: str = "global") -> str:
        if self.cv_text:
            return self.cv_text
        result = await self.db.execute(select(UserProfile).where(UserProfile.device_id == device_id).limit(1))
        profile = result.scalar_one_or_none()
        if profile and profile.cv_text and profile.cv_text.strip():
            return profile.cv_text
        return DEFAULT_CV


    async def analyze_job_by_id(self, job_id: int) -> Optional[Job]:
        """Evalúa un trabajo específico por su ID."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            return None

        logger.info(f"Analizando oferta ID {job.id}: '{job.title}' @ '{job.company}' (Device: {job.device_id})")

        active_cv = await self._get_active_cv_text(device_id=job.device_id)
        analysis_result = await self.ai_provider.analyze_job(
            job_description=f"Título: {job.title}\nEmpresa: {job.company}\nDescripción: {job.description}\nTecnologías: {', '.join(job.technologies)}",
            cv_text=active_cv
        )

        job.ai_score = analysis_result.match_score
        job.ai_summary = analysis_result.summary
        job.ai_analysis = {
            "technologies": analysis_result.technologies,
            "seniority": analysis_result.seniority,
            "reasoning": analysis_result.reasoning,
            "advantages": analysis_result.advantages,
            "missing_skills": analysis_result.missing_skills,
            "interview_probability": analysis_result.interview_probability,
            "recommendation": analysis_result.recommendation
        }
        job.status = JobStatus.ANALYZED

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def analyze_pending_jobs(self, limit: int = 10, device_id: str = "global") -> Dict[str, Any]:
        """Analiza en lote los empleos con estado NEW."""
        result = await self.db.execute(
            select(Job).where(Job.status == JobStatus.NEW, Job.device_id == device_id).limit(limit)
        )
        pending_jobs = result.scalars().all()

        if not pending_jobs:
            return {
                "message": "No hay empleos nuevos pendientes de análisis.",
                "total_analyzed": 0
            }

        analyzed_count = 0
        for job in pending_jobs:
            await self.analyze_job_by_id(job.id)
            analyzed_count += 1

        return {
            "message": f"Se completó el análisis de IA para {analyzed_count} ofertas.",
            "total_analyzed": analyzed_count
        }
