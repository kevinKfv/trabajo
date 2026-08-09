from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_analytics(
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene métricas analíticas detalladas, KPIs y desglose de tecnologías del mercado."""
    service = AnalyticsService(db)
    return await service.get_dashboard_metrics(device_id=x_device_id)
