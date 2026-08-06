from abc import ABC, abstractmethod
from typing import List
from app.schemas.job import JobCreate
from app.core.logging import logger


class BaseScraper(ABC):
    """Interfaz abstracta base para todos los scrapers de ofertas laborales.
    
    Cada scraper (LinkedIn, Bumeran, Computrabajo, etc.) debe heredar de esta clase
    e implementar la lógica de extracción retornando instancias de JobCreate.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def scrape(self, query: str = "", location: str = "", date_filter: str = "all") -> List[JobCreate]:
        """Ejecuta el proceso de scraping y devuelve una lista unificada de ofertas de empleo."""
        pass

    def log_start(self, query: str, location: str) -> None:
        logger.info(f"[{self.name}] Iniciando scraping - query='{query}', location='{location}'")

    def log_success(self, count: int) -> None:
        logger.info(f"[{self.name}] Scraping finalizado exitosamente - {count} ofertas extraídas")

    def log_error(self, error: Exception) -> None:
        logger.error(f"[{self.name}] Error durante la ejecución del scraping: {str(error)}", exc_info=True)
