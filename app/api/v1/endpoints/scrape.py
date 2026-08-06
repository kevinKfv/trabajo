from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.scrape_manager import ScrapeManager
from app.services.ai_service import AIService
from app.services.notification_service import NotificationService

router = APIRouter()


class ScrapeRequest(BaseModel):
    query: Optional[str] = None
    location: Optional[str] = "Buenos Aires, Argentina"
    scrapers: Optional[List[str]] = None
    use_saved_configs: bool = True


class AnalyzeRequest(BaseModel):
    limit: int = 10
    cv_text: Optional[str] = None


class NotifyRequest(BaseModel):
    min_score: float = 70.0
    limit: int = 10


@router.post("/scrape", status_code=status.HTTP_200_OK)
async def trigger_scrape(
    request: ScrapeRequest = ScrapeRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Ejecuta el pipeline completo de scraping (usando configuraciones guardadas o parámetros personalizados)."""
    manager = ScrapeManager(db)
    if request.use_saved_configs and not request.query:
        return await manager.run_all_active_search_configs()

    query_str = request.query or "desarrollador"
    location_str = request.location or "Buenos Aires, Argentina"
    result = await manager.run_scraping_pipeline(
        query=query_str,
        location=location_str,
        target_scrapers=request.scrapers
    )
    return result


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def trigger_ai_analysis(
    request: AnalyzeRequest = AnalyzeRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Ejecuta la clasificación y evaluación masiva con IA para empleos pendientes."""
    if request.cv_text:
        ai_service = AIService(db, cv_text=request.cv_text)
    else:
        ai_service = AIService(db)

    return await ai_service.analyze_pending_jobs(limit=request.limit)


@router.post("/notify", status_code=status.HTTP_200_OK)
async def trigger_notifications(
    request: NotifyRequest = NotifyRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Desencadena el envío de alertas de ofertas destacadas por Telegram y Email."""
    notif_service = NotificationService(db)
    return await notif_service.notify_high_match_jobs(
        min_score=request.min_score,
        limit=request.limit
    )
