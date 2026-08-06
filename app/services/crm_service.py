from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job, JobStatus
from app.models.application_stage import ApplicationStage, CRMStage
from app.models.reminder import Reminder, ReminderType
from app.core.logging import logger


class CRMService:
    """Servicio para la administración del CRM Kanban de postulaciones y gestión de etapas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_kanban_board(self) -> Dict[str, List[Dict[str, Any]]]:
        """Obtiene todas las ofertas agrupadas por su etapa actual en el pipeline del CRM."""
        # 1. Obtener trabajos limitando a los últimos 200 que no estén archivados/rechazados
        jobs_res = await self.db.execute(
            select(Job)
            .where(Job.status.notin_([JobStatus.ARCHIVED, JobStatus.REJECTED]))
            .order_by(Job.id.desc())
            .limit(200)
        )
        jobs = jobs_res.scalars().all()
        job_ids = [j.id for j in jobs]

        # 2. Obtener etapas de CRM guardadas solo para esos trabajos
        if job_ids:
            stages_res = await self.db.execute(
                select(ApplicationStage).where(ApplicationStage.job_id.in_(job_ids))
            )
            stages_map = {s.job_id: s for s in stages_res.scalars().all()}
        else:
            stages_map = {}

        board: Dict[str, List[Dict[str, Any]]] = {stage.value: [] for stage in CRMStage}

        for job in jobs:
            stage_entry = stages_map.get(job.id)
            current_stage = stage_entry.stage.value if stage_entry else CRMStage.APPLIED.value

            job_dict = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "source": job.source,
                "location": job.location,
                "url": job.url,
                "ai_score": job.ai_score,
                "stage": current_stage,
                "notes": stage_entry.notes if stage_entry else None,
                "interview_date": stage_entry.interview_date.isoformat() if (stage_entry and stage_entry.interview_date) else None,
                "salary_offered": stage_entry.salary_offered if stage_entry else None
            }

            if current_stage in board:
                board[current_stage].append(job_dict)
            else:
                board[CRMStage.APPLIED.value].append(job_dict)

        return board

    async def update_job_stage(
        self,
        job_id: int,
        new_stage: CRMStage,
        notes: Optional[str] = None,
        interview_date: Optional[datetime] = None,
        salary_offered: Optional[str] = None
    ) -> Dict[str, Any]:
        """Actualiza la etapa de reclutamiento de una oferta en el CRM."""
        job_res = await self.db.execute(select(Job).where(Job.id == job_id))
        job = job_res.scalar_one_or_none()
        if not job:
            return {"error": f"Oferta #{job_id} no encontrada."}

        stage_res = await self.db.execute(select(ApplicationStage).where(ApplicationStage.job_id == job_id))
        stage_entry = stage_res.scalar_one_or_none()

        if not stage_entry:
            stage_entry = ApplicationStage(job_id=job_id, stage=new_stage)
            self.db.add(stage_entry)

        stage_entry.stage = new_stage
        stage_entry.last_contact_date = datetime.now(timezone.utc)
        if notes:
            stage_entry.notes = notes
        if interview_date:
            stage_entry.interview_date = interview_date
        if salary_offered:
            stage_entry.salary_offered = salary_offered

        if new_stage == CRMStage.APPLIED and job.status != JobStatus.APPLIED:
            job.status = JobStatus.APPLIED

        await self.db.commit()
        await self.db.refresh(stage_entry)

        logger.info(f"Oferta #{job_id} ({job.title} @ {job.company}) movida a etapa '{new_stage.value}'")

        return {
            "success": True,
            "job_id": job_id,
            "stage": stage_entry.stage.value,
            "notes": stage_entry.notes
        }
