from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.cv_generator_service import CVGeneratorService
from app.services.cover_letter_service import CoverLetterService

router = APIRouter()


@router.post("/jobs/{job_id}/generate-cv", status_code=status.HTTP_200_OK)
async def generate_tailored_cv(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Genera una versión del CV optimizada y adaptada específicamente para una oferta laboral."""
    service = CVGeneratorService(db)
    result = await service.generate_tailored_cv(job_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/jobs/{job_id}/generate-cover-letter", status_code=status.HTTP_200_OK)
async def generate_cover_letter(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Genera una carta de presentación hiper-personalizada para una oferta laboral."""
    service = CoverLetterService(db)
    result = await service.generate_cover_letter(job_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
