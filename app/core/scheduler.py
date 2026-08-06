from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database.session import AsyncSessionLocal
from app.services.scrape_manager import ScrapeManager
from app.services.ai_service import AIService
from app.services.notification_service import NotificationService
from app.core.config import settings
from app.core.logging import logger

scheduler = AsyncIOScheduler()


async def run_full_job_hunter_pipeline() -> None:
    """Tarea automatizada periódica: ejecuta Scraping, Análisis de IA y Notificaciones."""
    logger.info("⏰ [SCHEDULER] Iniciando ejecución automática de la canalización de Job Hunter AI...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Scraping + Normalización + Deduplicación para Buenos Aires, Argentina
            scrape_manager = ScrapeManager(db)
            total_added = 0
            search_queries = ["desarrollador", "sysadmin", "analista de sistemas", "devops"]
            for q in search_queries:
                res = await scrape_manager.run_scraping_pipeline(query=q, location="Buenos Aires, Argentina")
                total_added += res.get("total_added_to_db", 0)
            logger.info(f"⏰ [SCHEDULER] Scraping completado para Buenos Aires: {total_added} ofertas nuevas guardadas.")

            # 2. Análisis con IA de ofertas pendientes
            ai_service = AIService(db)
            ai_res = await ai_service.analyze_pending_jobs(limit=20)
            logger.info(f"⏰ [SCHEDULER] Análisis IA completado: {ai_res.get('total_analyzed', 0)} ofertas analizadas.")

            # 3. Notificación de ofertas destacadas
            notif_service = NotificationService(db)
            notif_res = await notif_service.notify_high_match_jobs(min_score=70.0)
            logger.info(f"⏰ [SCHEDULER] Notificaciones procesadas: {notif_res.get('total_notified', 0)} enviadas.")

        except Exception as e:
            logger.error(f"⏰ [SCHEDULER] Error durante la ejecución automática: {e}", exc_info=True)


def start_scheduler() -> None:
    """Inicializa y arranca el planificador de tareas en segundo plano."""
    interval_hours = settings.SCRAPE_INTERVAL_HOURS
    
    scheduler.add_job(
        run_full_job_hunter_pipeline,
        trigger=IntervalTrigger(hours=interval_hours),
        id="job_hunter_pipeline",
        name="Canalización periódica de Job Hunter AI",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"⏰ [SCHEDULER] Scheduler iniciado. Ejecución configurada cada {interval_hours} horas.")


def shutdown_scheduler() -> None:
    """Detiene el planificador al apagar la aplicación."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("⏰ [SCHEDULER] Scheduler detenido correctamente.")
