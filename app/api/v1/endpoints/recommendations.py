from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user_job_feedback import UserFeedbackAction
from app.services.recommender_service import RecommenderService
from app.services.multichannel_notifier import MultichannelNotifier

router = APIRouter()


class FeedbackRequest(BaseModel):
    action: str


class MultichannelNotifyRequest(BaseModel):
    title: str
    message: str
    url: Optional[str] = ""


@router.post("/feedback/{job_id}", status_code=status.HTTP_200_OK)
async def register_job_feedback(
    job_id: int,
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Registra la reacción del usuario ante una oferta (Guardar, Descartar, Postular) para entrenar al motor de recomendaciones."""
    service = RecommenderService(db)
    res = await service.register_feedback(job_id, req.action)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/jobs")
async def get_recommended_jobs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene el feed de empleos ordenados por recomendación adaptativa e inteligencia multidimensional."""
    service = RecommenderService(db)
    items = await service.get_recommended_jobs(limit=limit)
    
    # Formatear respuesta JSON limpia
    formatted = []
    for item in items:
        j = item["job"]
        j_dict = {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "remote": j.remote,
            "seniority": j.seniority,
            "technologies": j.technologies,
            "url": j.url,
            "source": j.source,
            "ai_score": j.ai_score,
            "status": j.status,
            "ranking_score": item["ranking_score"],
            "ranking_badge_color": item["ranking_details"]["badge_color"]
        }
        formatted.append(j_dict)
    return {"total": len(formatted), "items": formatted}


@router.post("/notify/multichannel", status_code=status.HTTP_200_OK)
async def trigger_multichannel_notification(req: MultichannelNotifyRequest):
    """Envía notificaciones simultáneas por Telegram, Discord, WhatsApp y Email."""
    return await MultichannelNotifier.notify_multichannel(
        title=req.title,
        message=req.message,
        url=req.url or ""
    )
