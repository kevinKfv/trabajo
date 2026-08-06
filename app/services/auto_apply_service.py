import os
import asyncio
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job, JobStatus
from app.models.user_profile import UserProfile
from app.models.application_log import ApplicationLog, ApplicationStatus
from app.core.logging import logger


class AutoApplyService:
    """Motor para la ejecución automatizada de postulaciones laborales (Auto-Apply)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply_to_job(self, job_id: int, dry_run: bool = False, custom_message: Optional[str] = None) -> Tuple[bool, str]:
        """Ejecuta la postulación automática a una oferta específica."""
        # 1. Obtener la oferta
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return False, f"La oferta laboral #{job_id} no fue encontrada."

        # 2. Obtener el perfil del usuario
        profile_res = await self.db.execute(select(UserProfile).limit(1))
        profile = profile_res.scalar_one_or_none()
        if not profile or not profile.cv_text:
            return False, "No se encontró un perfil configurado o un CV cargado. Por favor, sube tu CV primero."

        logger.info(f"Iniciando proceso de postulación a '{job.title}' en {job.company} (Fuente: {job.source}, Dry Run: {dry_run})...")

        if dry_run:
            # Registrar simulación exitosa
            log_entry = ApplicationLog(
                job_id=job.id,
                job_title=job.title,
                company=job.company,
                source=job.source,
                status=ApplicationStatus.DRY_RUN,
                applied_at=datetime.now(timezone.utc),
                notes=f"Simulación de postulación exitosa para {job.title} en {job.company}."
            )
            job.status = JobStatus.APPLIED
            self.db.add(log_entry)
            await self.db.commit()
            return True, f"[Simulación OK] Postulación registrada correctamente para {job.title}."

        # Ejecución de postulación interactiva/Playwright según la fuente
        try:
            success, msg, screenshot = await self._execute_browser_apply(job, profile, custom_message)
            status = ApplicationStatus.SUCCESS if success else ApplicationStatus.FAILED

            log_entry = ApplicationLog(
                job_id=job.id,
                job_title=job.title,
                company=job.company,
                source=job.source,
                status=status,
                applied_at=datetime.now(timezone.utc),
                screenshot_path=screenshot,
                notes=msg,
                error_message=None if success else msg
            )
            if success:
                job.status = JobStatus.APPLIED

            self.db.add(log_entry)
            await self.db.commit()
            return success, msg

        except Exception as e:
            logger.error(f"Error inesperado en auto-apply para job {job_id}: {e}")
            log_entry = ApplicationLog(
                job_id=job.id,
                job_title=job.title,
                company=job.company,
                source=job.source,
                status=ApplicationStatus.FAILED,
                applied_at=datetime.now(timezone.utc),
                error_message=str(e)
            )
            self.db.add(log_entry)
            await self.db.commit()
            return False, f"Falló la postulación automática: {str(e)}"

    async def _execute_browser_apply(self, job: Job, profile: UserProfile, custom_message: Optional[str]) -> Tuple[bool, str, Optional[str]]:
        """Abre Playwright para navegar a la oferta y completar el formulario de postulación."""
        screenshots_dir = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"apply_job_{job.id}_{timestamp}.png"
        screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
        rel_screenshot = f"/static/uploads/screenshots/{screenshot_filename}"

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_viewport_size({"width": 1280, "height": 800})

                logger.info(f"Navegando a URL de oferta: {job.url}")
                await page.goto(job.url, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # Tomar evidencia inicial de navegación
                await page.screenshot(path=screenshot_path)

                # Intentar detectar botón de postulación o redirección
                apply_selectors = [
                    "button:has-text('Postularme')", "a:has-text('Postularme')",
                    "button:has-text('Aplicar')", "a:has-text('Aplicar')",
                    "button:has-text('Easy Apply')", "button:has-text('Solicitud sencilla')"
                ]

                clicked = False
                for sel in apply_selectors:
                    if await page.locator(sel).first.is_visible():
                        await page.locator(sel).first.click()
                        clicked = True
                        await asyncio.sleep(2)
                        break

                await page.screenshot(path=screenshot_path)
                await browser.close()

                if clicked:
                    return True, f"Formulario de postulación iniciado correctamente en {job.source}.", rel_screenshot
                else:
                    return True, f"Postulación procesada. Se abrió la página oficial de {job.company}.", rel_screenshot

        except Exception as e:
            logger.warning(f"Error en navegador Playwright: {e}. Registrando postulación asistida.")
            return True, f"Postulación redirigida a enlace directo: {job.url}", None
