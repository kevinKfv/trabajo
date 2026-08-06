from app.scrapers.base import BaseScraper
from app.scrapers.registry import ScraperRegistry

# Importar scrapers para asegurar su autorregistro automático en ScraperRegistry
from app.scrapers.linkedin import LinkedInScraper
from app.scrapers.bumeran import BumeranScraper
from app.scrapers.computrabajo import ComputrabajoScraper

__all__ = [
    "BaseScraper",
    "ScraperRegistry",
    "LinkedInScraper",
    "BumeranScraper",
    "ComputrabajoScraper",
]
