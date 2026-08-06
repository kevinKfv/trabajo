from typing import Dict, Type, List
from app.scrapers.base import BaseScraper
from app.core.logging import logger


class ScraperRegistry:
    """Registro centralizado para administrar e instanciar scrapers dinámicamente."""

    _scrapers: Dict[str, Type[BaseScraper]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorador para registrar un scraper por nombre."""
        def decorator(scraper_cls: Type[BaseScraper]):
            cls._scrapers[name.lower()] = scraper_cls
            logger.info(f"Scraper registrado: '{name.lower()}' ({scraper_cls.__name__})")
            return scraper_cls
        return decorator

    @classmethod
    def get_scraper(cls, name: str) -> BaseScraper:
        """Obtiene una instancia del scraper registrado."""
        scraper_cls = cls._scrapers.get(name.lower())
        if not scraper_cls:
            raise KeyError(f"Scraper '{name}' no encontrado en el registro. Scrapers disponibles: {cls.list_scrapers()}")
        return scraper_cls(name=name.lower())

    @classmethod
    def list_scrapers(cls) -> List[str]:
        """Devuelve la lista de scrapers disponibles."""
        return list(cls._scrapers.keys())

    @classmethod
    def get_all_scrapers(cls) -> List[BaseScraper]:
        """Instancia todos los scrapers registrados."""
        return [cls.get_scraper(name) for name in cls._scrapers.keys()]
