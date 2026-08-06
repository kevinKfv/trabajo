from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.job_service import JobService


async def get_job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    """Inyector de dependencias para instanciar el servicio JobService."""
    return JobService(db)
