from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/scrapers-status")
async def get_scrapers_status(db: AsyncSession = Depends(get_db)):
    """Obtiene el estado de salud, logs de auditoría y métricas de ejecución de los scrapers."""
    service = AdminService(db)
    return await service.get_scrapers_status()
