from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.models.application_log import ApplicationLog
from app.models.job import Job, JobStatus
from app.schemas.auto_apply import (
    AutoApplyRequest,
    BatchAutoApplyRequest,
    ApplicationLogResponse
)
from app.services.auto_apply_service import AutoApplyService

router = APIRouter()


@router.post("/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def apply_to_job(
    job_id: int,
    req: AutoApplyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Ejecuta la postulación automática (1-click auto-apply) para una oferta laboral."""
    service = AutoApplyService(db)
    success, message = await service.apply_to_job(
        job_id=job_id,
        dry_run=req.dry_run,
        custom_message=req.custom_message
    )

    if not success and "no fue encontrada" in message:
        raise HTTPException(status_code=404, detail=message)

    return {
        "success": success,
        "message": message,
        "job_id": job_id
    }


@router.post("/batch", status_code=status.HTTP_200_OK)
async def batch_auto_apply(
    req: BatchAutoApplyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Ejecuta postulaciones masivas para empleos con ai_score >= min_ai_score no postulados aún."""
    result = await db.execute(
        select(Job).where(
            Job.ai_score >= req.min_ai_score,
            Job.status != JobStatus.APPLIED
        ).limit(req.max_applications)
    )
    eligible_jobs = result.scalars().all()

    if not eligible_jobs:
        return {
            "message": f"No se encontraron ofertas elegibles con coincidencia IA >= {req.min_ai_score}% pendientes de postular.",
            "total_processed": 0,
            "results": []
        }

    service = AutoApplyService(db)
    results = []
    processed_count = 0

    for job in eligible_jobs:
        success, msg = await service.apply_to_job(job_id=job.id, dry_run=req.dry_run)
        results.append({
            "job_id": job.id,
            "job_title": job.title,
            "company": job.company,
            "success": success,
            "message": msg
        })
        processed_count += 1

    return {
        "message": f"Se procesó la postulación automática para {processed_count} ofertas elegibles.",
        "total_processed": processed_count,
        "results": results
    }


@router.get("/logs", response_model=List[ApplicationLogResponse])
async def list_application_logs(db: AsyncSession = Depends(get_db)):
    """Obtiene el historial de auditoría de postulaciones realizadas por el bot."""
    result = await db.execute(select(ApplicationLog).order_by(ApplicationLog.id.desc()).limit(50))
    return result.scalars().all()
