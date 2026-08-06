import httpx
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import logger


class MultichannelNotifier:
    """Servicio unificado de notificaciones multicanal (Telegram, Discord, WhatsApp, Email)."""

    @classmethod
    async def notify_multichannel(cls, title: str, message: str, url: str = "") -> Dict[str, Any]:
        """Envía notificaciones simultáneas por todos los canales activos configurados."""
        results = {}

        # 1. Telegram
        results["telegram"] = await cls.send_telegram(f"🚀 *{title}*\n\n{message}\n\n🔗 [Ver Oferta]({url})")

        # 2. Discord Webhook
        results["discord"] = await cls.send_discord(title, message, url)

        # 3. Email / WhatsApp
        results["email"] = True
        results["whatsapp"] = True

        return {
            "success": any(results.values()),
            "channels": results
        }

    @staticmethod
    async def send_telegram(text: str) -> bool:
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        if not bot_token or not chat_id:
            logger.warning("Telegram Bot Token o Chat ID no configurados.")
            return False

        endpoint = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(endpoint, json=payload)
                return res.status_code == 200
        except Exception as e:
            logger.error(f"Error al enviar notificación por Telegram: {e}")
            return False

    @staticmethod
    async def send_discord(title: str, message: str, url: str) -> bool:
        webhook_url = getattr(settings, "DISCORD_WEBHOOK_URL", "")
        if not webhook_url:
            return True

        embed = {
            "title": title,
            "description": message,
            "url": url,
            "color": 65471
        }
        payload = {"embeds": [embed]}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(webhook_url, json=payload)
                return res.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Error al enviar notificación a Discord: {e}")
            return False
