from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_analytics(db: AsyncSession = Depends(get_db)):
    """Obtiene métricas analíticas detalladas, KPIs y desglose de tecnologías del mercado."""
    service = AnalyticsService(db)
    return await service.get_dashboard_metrics()
