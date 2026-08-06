from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.models.application_stage import CRMStage, ApplicationStage
from app.models.reminder import Reminder, ReminderType
from app.models.job import Job
from app.services.crm_service import CRMService
from app.services.calendar_service import CalendarService

router = APIRouter()


class UpdateStageRequest(BaseModel):
    stage: CRMStage
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None
    salary_offered: Optional[str] = None


class ReminderCreate(BaseModel):
    job_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    remind_at: datetime
    reminder_type: ReminderType = ReminderType.INTERVIEW


class ReminderResponse(BaseModel):
    id: int
    job_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    remind_at: datetime
    reminder_type: ReminderType
    is_completed: bool

    model_config = ConfigDict(from_attributes=True)


@router.get("/kanban")
async def get_kanban_board(db: AsyncSession = Depends(get_db)):
    """Obtiene todas las postulaciones organizadas por etapas en el tablero Kanban del CRM."""
    service = CRMService(db)
    return await service.get_kanban_board()


@router.put("/jobs/{job_id}/stage")
async def update_job_stage(
    job_id: int,
    req: UpdateStageRequest,
    db: AsyncSession = Depends(get_db)
):
    """Actualiza la etapa de reclutamiento de un trabajo (Postulado, Contacto RRHH, Entrevista, etc.)."""
    service = CRMService(db)
    result = await service.update_job_stage(
        job_id=job_id,
        new_stage=req.stage,
        notes=req.notes,
        interview_date=req.interview_date,
        salary_offered=req.salary_offered
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/reminders", response_model=List[ReminderResponse])
async def list_reminders(db: AsyncSession = Depends(get_db)):
    """Lista todos los recordatorios y eventos de entrevista."""
    res = await db.execute(select(Reminder).order_by(Reminder.remind_at.asc()))
    return res.scalars().all()


@router.post("/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_in: ReminderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crea un nuevo recordatorio o evento de entrevista."""
    rem = Reminder(**reminder_in.model_dump())
    db.add(rem)
    await db.commit()
    await db.refresh(rem)
    return rem


@router.get("/jobs/{job_id}/export-calendar")
async def export_calendar_event(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Genera el contenido de archivo iCal (.ics) y enlace directo a Google Calendar para una entrevista."""
    job_res = await db.execute(select(Job).where(Job.id == job_id))
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Oferta laboral no encontrada.")

    stage_res = await db.execute(select(ApplicationStage).where(ApplicationStage.job_id == job_id))
    stage_entry = stage_res.scalar_one_or_none()

    start_dt = stage_entry.interview_date if (stage_entry and stage_entry.interview_date) else (datetime.now(timezone.utc) + timedelta(days=1))

    title = f"Entrevista: {job.title} en {job.company}"
    desc = f"Entrevista de selección para el puesto de {job.title}.\nEmpresa: {job.company}\nFuente: {job.source}\nEnlace: {job.url}"

    ics_content = CalendarService.generate_ics_content(title, desc, start_dt)
    gcal_url = CalendarService.generate_google_calendar_url(title, desc, start_dt)

    return {
        "job_id": job.id,
        "title": title,
        "google_calendar_url": gcal_url,
        "ics_content": ics_content
    }
