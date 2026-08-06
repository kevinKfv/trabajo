from typing import List
import httpx
from app.notifications.base import BaseNotificationProvider
from app.schemas.job import JobResponse
from app.core.config import settings
from app.core.logging import logger


class TelegramNotificationProvider(BaseNotificationProvider):
    """Proveedor de notificaciones para Telegram a través de Telegram Bot API."""

    def __init__(self, bot_token: str = "", chat_id: str = "") -> None:
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send_notification(self, jobs: List[JobResponse]) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.warning("TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados. Modo mock para Telegram.")
            return False

        if not jobs:
            return True

        success = True
        async with httpx.AsyncClient(timeout=15.0) as client:
            for job in jobs:
                remote_badge = "🏠 Remoto" if job.remote else "🏢 Presencial / Híbrido"
                score_str = f"{job.ai_score:.0f}/100" if job.ai_score is not None else "N/A"

                message = (
                    f"🎯 <b>NUEVA OFERTA COMPATIBLE ({score_str})</b>\n\n"
                    f"💼 <b>Puesto:</b> {job.title}\n"
                    f"🏢 <b>Empresa:</b> {job.company}\n"
                    f"📍 <b>Ubicación:</b> {job.location or 'No especificada'} ({remote_badge})\n"
                    f"⭐ <b>Match Score:</b> {score_str}\n"
                    f"🛠️ <b>Tecnologías:</b> {', '.join(job.technologies[:5])}\n\n"
                    f"📝 <b>Resumen IA:</b> {job.ai_summary or 'Sin resumen'}\n\n"
                    f"🔗 <a href='{job.url}'>Ver Oferta y Postularse</a>"
                )

                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False
                }

                try:
                    response = await client.post(self.api_url, json=payload)
                    response.raise_for_status()
                    logger.info(f"Notificación de Telegram enviada exitosamente para oferta ID {job.id}")
                except Exception as e:
                    logger.error(f"Error al enviar notificación por Telegram para empleo ID {job.id}: {e}")
                    success = False

        return success
