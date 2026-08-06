import asyncio
import pytest
from app.core.scheduler import scheduler, start_scheduler, shutdown_scheduler


@pytest.mark.asyncio
async def test_scheduler_lifecycle():
    """Verifica que el scheduler se configure y detenga correctamente dentro del loop asíncrono."""
    start_scheduler()
    assert scheduler.running is True

    job = scheduler.get_job("job_hunter_pipeline")
    assert job is not None
    assert job.name == "Canalización periódica de Job Hunter AI"

    shutdown_scheduler()
    await asyncio.sleep(0.05)
    assert scheduler.running is False
