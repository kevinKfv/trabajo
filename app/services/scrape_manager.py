import asyncio
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.scrapers.registry import ScraperRegistry
from app.services.normalizer_service import NormalizerService
from app.services.deduplication_service import DeduplicationService
from app.services.job_service import JobService
from app.models.scrape_log import ScrapeLog, ScrapeStatus
from app.schemas.job import JobCreate
from app.core.logging import logger


from datetime import datetime, timezone

class ScrapeManager:
    """Orquestador principal del ciclo de vida de raspado, normalización, deduplicación y auditoría."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.job_service = JobService(db)

    async def run_scraping_pipeline(
        self,
        query: str = "desarrollador",
        location: str = "Buenos Aires, Argentina",
        target_scrapers: List[str] = None,
        date_filter: str = "all",
        device_id: str = "global"
    ) -> Dict[str, Any]:
        """Ejecuta la canalización completa de scraping de forma concurrente."""
        available = ScraperRegistry.list_scrapers()
        selected = target_scrapers or available

        scrapers_to_run = [name for name in selected if name in available]

        if not scrapers_to_run:
            return {
                "message": "No hay scrapers válidos para ejecutar",
                "scrapers_executed": [],
                "total_found": 0,
                "total_added": 0
            }

        logger.info(f"Iniciando pipeline de scraping para: {scrapers_to_run}")

        # 1. Ejecución concurrente de scrapers
        tasks = [
            ScraperRegistry.get_scraper(name).scrape(query=query, location=location, date_filter=date_filter)
            for name in scrapers_to_run
        ]
        results_per_scraper = await asyncio.gather(*tasks, return_exceptions=True)

        all_raw_jobs: List[JobCreate] = []
        details = {}
        total_found = 0
        total_added = 0

        # 2. Procesamiento de resultados y auditoría por fuente
        for name, res in zip(scrapers_to_run, results_per_scraper):
            if isinstance(res, Exception):
                logger.error(f"Fallo en el scraper {name}: {res}")
                log_entry = ScrapeLog(
                    source=name,
                    status=ScrapeStatus.FAILED,
                    jobs_found=0,
                    jobs_added=0,
                    error_message=str(res)
                )
                self.db.add(log_entry)
                details[name] = {"status": "FAILED", "found": 0, "added": 0, "error": str(res)}
            else:
                found_count = len(res)
                total_found += found_count
                
                # Normalizar empleos extraídos
                normalized_jobs = NormalizerService.normalize_batch(res)
                all_raw_jobs.extend(normalized_jobs)

                details[name] = {"status": "SUCCESS", "found": found_count}

        # 3. Deduplicación difusa en memoria sobre todo el lote consolidado
        deduplicated_batch = DeduplicationService.deduplicate_in_memory(all_raw_jobs)
        logger.info(f"Lote consolidado: {len(all_raw_jobs)} extraídos -> {len(deduplicated_batch)} únicos tras deduplicación en memoria")

        # 4. Guardado en Base de Datos (omitirá también duplicados preexistentes en la BD)
        _, total_added = await self.job_service.bulk_save_jobs(deduplicated_batch, device_id=device_id)

        # Actualizar logs de auditoría exitosos
        for name in scrapers_to_run:
            if details[name]["status"] == "SUCCESS":
                found = details[name]["found"]
                log_entry = ScrapeLog(
                    source=name,
                    status=ScrapeStatus.SUCCESS,
                    jobs_found=found,
                    jobs_added=total_added if len(scrapers_to_run) == 1 else 0
                )
                self.db.add(log_entry)

        await self.db.commit()

        return {
            "message": "Pipeline de scraping completado exitosamente",
            "query": query,
            "location": location,
            "total_found": total_found,
            "total_unique_in_batch": len(deduplicated_batch),
            "total_added_to_db": total_added,
            "details": details
        }

    async def run_all_active_search_configs(self, device_id: str = "global") -> Dict[str, Any]:
        """Ejecuta el pipeline de scraping iterando sobre todas las configuraciones de búsqueda activas en la BD."""
        from sqlalchemy import select
        from app.models.search_config import SearchConfig

        res = await self.db.execute(select(SearchConfig).where(SearchConfig.is_active == True, SearchConfig.device_id == device_id))
        active_configs = res.scalars().all()

        if not active_configs:
            # Si no hay búsquedas configuradas, usar búsquedas por defecto (pasantía, jóvenes profesionales, desarrollador)
            default_keywords = ["pasantía", "jóvenes profesionales", "desarrollador"]
            total_added = 0
            for kw in default_keywords:
                r = await self.run_scraping_pipeline(query=kw, device_id=device_id)
                total_added += r.get("total_added_to_db", 0)
            return {
                "message": "Se ejecutaron las búsquedas predeterminadas por falta de configuraciones activas.",
                "total_added_to_db": total_added
            }

        total_added = 0
        executed_configs = []

        for config in active_configs:
            logger.info(f"Ejecutando configuración de búsqueda: '{config.name}' con palabras clave {config.keywords}")
            for kw in config.keywords:
                r = await self.run_scraping_pipeline(
                    query=kw,
                    location=config.location or "Buenos Aires, Argentina",
                    target_scrapers=config.sources if config.sources else None,
                    date_filter=getattr(config, "date_filter", "all"),
                    device_id=device_id
                )
                total_added += r.get("total_added_to_db", 0)
            
            config.last_run_at = datetime.now(timezone.utc)
            executed_configs.append(config.name)

        await self.db.commit()

        return {
            "message": f"Se completó la búsqueda para {len(executed_configs)} configuraciones activas.",
            "executed_configs": executed_configs,
            "total_added_to_db": total_added
        }

