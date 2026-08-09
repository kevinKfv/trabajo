from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.schemas.job import JobResponse
from app.notifications.telegram_provider import TelegramNotificationProvider
from app.notifications.email_provider import EmailNotificationProvider
from app.core.logging import logger


class NotificationService:
    """Servicio para filtrar, formatear y notificar ofertas destacadas por Telegram y Email."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.telegram_provider = TelegramNotificationProvider()
        self.email_provider = EmailNotificationProvider()

    async def notify_high_match_jobs(self, min_score: float = 70.0, limit: int = 10, device_id: str = "global") -> Dict[str, Any]:
        """Obtiene ofertas con estado ANALYZED y ai_score >= min_score y envía alertas."""
        result = await self.db.execute(
            select(Job)
            .where(Job.status == JobStatus.ANALYZED)
            .where(Job.ai_score >= min_score)
            .where(Job.device_id == device_id)
            .order_by(Job.ai_score.desc())
            .limit(limit)
        )
        qualified_jobs = result.scalars().all()

        if not qualified_jobs:
            return {
                "message": f"No hay nuevas ofertas clasificadas con score >= {min_score} pendientes de notificar.",
                "notified_count": 0
            }

        job_responses = [JobResponse.model_validate(j) for j in qualified_jobs]

        # Enviar vía Telegram y Email
        telegram_sent = await self.telegram_provider.send_notification(job_responses)
        email_sent = await self.email_provider.send_notification(job_responses)

        # Actualizar estado a NOTIFIED en la BD
        for job in qualified_jobs:
            job.status = JobStatus.NOTIFIED

        await self.db.commit()

        return {
            "message": f"Se procesaron {len(qualified_jobs)} ofertas destacadas para notificación.",
            "total_notified": len(qualified_jobs),
            "channels": {
                "telegram": "ENVIADO" if telegram_sent else "OMITIDO/MOCK",
                "email": "ENVIADO" if email_sent else "OMITIDO/MOCK"
            }
        }
