from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db, AsyncSessionLocal
from app.services.scrape_manager import ScrapeManager
from app.models.search_config import SearchConfig
from app.schemas.search_config import (
    SearchConfigCreate,
    SearchConfigUpdate,
    SearchConfigResponse
)

router = APIRouter()


@router.get("", response_model=List[SearchConfigResponse])
async def list_search_configs(
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Lista todas las configuraciones de búsqueda personalizadas."""
    result = await db.execute(select(SearchConfig).where(SearchConfig.device_id == x_device_id).order_by(SearchConfig.id.desc()))
    return result.scalars().all()


@router.post("", response_model=SearchConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_search_config(
    config_in: SearchConfigCreate,
    background_tasks: BackgroundTasks,
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Crea una nueva regla/configuración de búsqueda y dispara su scraping inmediatamente."""
    config = SearchConfig(**config_in.model_dump(), device_id=x_device_id)
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    async def _bg_scrape_config():
        async with AsyncSessionLocal() as session:
            manager = ScrapeManager(session)
            # config_in.date_filter is handled by getattr if not explicitly present in model, but for schema it should be there.
            df = getattr(config_in, "date_filter", "all")
            for kw in config_in.keywords:
                await manager.run_scraping_pipeline(
                    query=kw,
                    location=config_in.location or "Buenos Aires, Argentina",
                    target_scrapers=config_in.sources if config_in.sources else None,
                    date_filter=df,
                    device_id=x_device_id
                )

    background_tasks.add_task(_bg_scrape_config)
    return config


@router.put("/{config_id}", response_model=SearchConfigResponse)
async def update_search_config(
    config_id: int,
    config_in: SearchConfigUpdate,
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Actualiza una configuración de búsqueda existente."""
    result = await db.execute(select(SearchConfig).where(SearchConfig.id == config_id, SearchConfig.device_id == x_device_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuración de búsqueda no encontrada.")

    for field, value in config_in.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_search_config(
    config_id: int,
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Elimina una configuración de búsqueda."""
    result = await db.execute(select(SearchConfig).where(SearchConfig.id == config_id, SearchConfig.device_id == x_device_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuración de búsqueda no encontrada.")

    await db.delete(config)
    await db.commit()
    return None
