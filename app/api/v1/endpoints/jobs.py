from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.job import JobResponse, JobStatsResponse, JobCreate
from app.schemas.filter import JobFilter
from app.services.job_service import JobService
from app.services.ai_service import AIService
from app.api.deps import get_job_service
from app.models.job import JobStatus

router = APIRouter()


@router.get("", response_model=dict)
async def get_jobs(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=100, description="Cantidad por página"),
    remote: bool = Query(None, description="Filtrar por trabajo remoto"),
    location: str = Query(None, description="Ubicación"),
    company: str = Query(None, description="Empresa"),
    seniority: str = Query(None, description="Seniority"),
    source: str = Query(None, description="Plataforma de origen"),
    status_filter: JobStatus = Query(None, alias="status", description="Estado del empleo"),
    min_ai_score: float = Query(None, ge=0, le=100, description="Puntaje mínimo IA"),
    date_filter: str = Query(None, description="Filtro de fechas (today, week)"),
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    job_service: JobService = Depends(get_job_service)
):
    """Obtiene la lista paginada de ofertas laborales con filtros aplicables."""
    filters = JobFilter(
        page=page,
        limit=limit,
        remote=remote,
        location=location,
        company=company,
        seniority=seniority,
        source=source,
        status=status_filter,
        min_ai_score=min_ai_score,
        date_filter=date_filter,
        device_id=x_device_id
    )

    jobs, total = await job_service.filter_jobs(filters)

    return {
        "items": [JobResponse.model_validate(job) for job in jobs],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 0
    }


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats(
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    job_service: JobService = Depends(get_job_service)
):
    """Retorna métricas y estadísticas consolidadas sobre las ofertas almacenadas."""
    return await job_service.get_stats(device_id=x_device_id)


@router.get("/search", response_model=dict)
async def search_jobs(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    job_service: JobService = Depends(get_job_service)
):
    """Búsqueda libre por texto en título, empresa o descripción."""
    filters = JobFilter(search_query=q, page=page, limit=limit, device_id=x_device_id)
    jobs, total = await job_service.filter_jobs(filters)

    return {
        "query": q,
        "items": [JobResponse.model_validate(job) for job in jobs],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_by_id(
    job_id: int,
    job_service: JobService = Depends(get_job_service)
):
    """Obtiene el detalle completo de una oferta laboral por su ID."""
    job = await job_service.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Oferta de empleo con ID {job_id} no encontrada"
        )
    return job


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    job_service: JobService = Depends(get_job_service)
):
    """Crea una oferta de empleo manualmente (o mediante webhook). Deduplica automáticamente."""
    job, created = await job_service.save_job(job_in, device_id=x_device_id)
    if not created and job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La oferta laboral ya existe (ID: {job.id}, URL: {job.url})"
        )
    return job


@router.post("/{job_id}/analyze", response_model=JobResponse)
async def analyze_job_by_id(
    job_id: int,
    cv_text: Optional[str] = Query(None, description="Texto opcional del CV personalizado"),
    db: AsyncSession = Depends(get_db)
):
    """Solicita el análisis individual con IA para una oferta de empleo específica."""
    if cv_text:
        ai_service = AIService(db, cv_text=cv_text)
    else:
        ai_service = AIService(db)

    analyzed_job = await ai_service.analyze_job_by_id(job_id)
    if not analyzed_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Oferta de empleo con ID {job_id} no encontrada"
        )
    return analyzed_job


@router.delete("/all", response_model=dict)
async def delete_all_jobs(
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Elimina todas las ofertas laborales scrapeadas del feed."""
    from sqlalchemy import delete
    from app.models.job import Job
    await db.execute(delete(Job).where(Job.device_id == x_device_id))
    await db.commit()
    return {"message": "Todas las ofertas han sido eliminadas."}
