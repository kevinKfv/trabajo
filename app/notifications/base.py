from abc import ABC, abstractmethod
from typing import List
from app.schemas.job import JobResponse


class BaseNotificationProvider(ABC):
    """Interfaz abstracta base para proveedores de notificaciones (Telegram, Email, etc.)."""

    @abstractmethod
    async def send_notification(self, jobs: List[JobResponse]) -> bool:
        """Envía notificaciones de nuevas ofertas encontradas."""
        pass
