from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.scrape_log import ScrapeLog
from app.scrapers.registry import ScraperRegistry


class AdminService:
    """Servicio de auditoría y administración del sistema y scrapers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_scrapers_status(self) -> List[Dict[str, Any]]:
        """Obtiene el estado de salud y últimas ejecuciones de cada scraper activo."""
        available_scrapers = ScraperRegistry.list_scrapers()
        status_list = []

        for scraper_name in available_scrapers:
            log_res = await self.db.execute(
                select(ScrapeLog)
                .where(ScrapeLog.source == scraper_name)
                .order_by(ScrapeLog.id.desc())
                .limit(5)
            )
            logs = log_res.scalars().all()

            total_found = sum([l.jobs_found for l in logs]) if logs else 0
            total_added = sum([l.jobs_added for l in logs]) if logs else 0
            last_run = logs[0].created_at.isoformat() if logs else None
            last_status = logs[0].status.value if logs else "IDLE"

            status_list.append({
                "name": scraper_name,
                "status": last_status,
                "last_run": last_run,
                "recent_found": total_found,
                "recent_added": total_added,
                "is_active": True
            })

        return status_list
