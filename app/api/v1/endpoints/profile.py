import os
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.session import get_db, AsyncSessionLocal
from app.models.user_profile import UserProfile
from app.models.search_config import SearchConfig
from app.models.job import Job
from app.schemas.profile import UserProfileResponse, UserProfileUpdate
from app.services.cv_parser_service import CVParserService
from app.services.scrape_manager import ScrapeManager
from app.ai.factory import AIFactory
from app.core.logging import logger

router = APIRouter()

async def _reset_and_trigger_scrape(db: AsyncSession, profile: UserProfile, background_tasks: BackgroundTasks):
    await db.execute(delete(SearchConfig))
    await db.execute(delete(Job))
    
    keywords = profile.cv_skills[:4] if profile.cv_skills else ["desarrollador"]
    if not keywords:
        keywords = ["desarrollador"]
        
    new_config = SearchConfig(
        name="Búsqueda basada en CV",
        keywords=keywords,
        location="Buenos Aires, Argentina",
        sources=["linkedin", "bumeran", "computrabajo"],
        is_active=True
    )
    db.add(new_config)
    await db.commit()

    async def _bg_scrape():
        async with AsyncSessionLocal() as session:
            manager = ScrapeManager(session)
            await manager.run_all_active_search_configs()
            
    background_tasks.add_task(_bg_scrape)


UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "static", "uploads", "cvs")
os.makedirs(UPLOADS_DIR, exist_ok=True)


@router.get("", response_model=UserProfileResponse)
async def get_profile(db: AsyncSession = Depends(get_db)):
    """Obtiene el perfil del postulante activo (o crea uno por defecto si no existe)."""
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(
            full_name="Mi Perfil",
            email="",
            summary="Perfil inicial de postulante"
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return profile


@router.put("", response_model=UserProfileResponse)
async def update_profile(
    profile_in: UserProfileUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Actualiza la información del perfil de usuario."""
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile()
        db.add(profile)

    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    
    await _reset_and_trigger_scrape(db, profile, background_tasks)
    return profile


@router.post("/cv", response_model=UserProfileResponse)
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Subida y procesamiento de archivo CV (PDF, DOCX, TXT). Extrae texto y habilidades."""
    allowed_extensions = [".pdf", ".docx", ".doc", ".txt"]
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Formatos soportados: {', '.join(allowed_extensions)}"
        )

    file_path = os.path.join(UPLOADS_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error guardando CV: {e}")
        raise HTTPException(status_code=500, detail="No se pudo guardar el archivo CV en el servidor.")

    # Parsear CV
    cv_text, regex_skills = CVParserService.parse_cv_file(file_path)
    
    # Extraer skills con IA (combinar con regex)
    ai_provider = AIFactory.get_provider()
    ai_skills = await ai_provider.extract_cv_skills(cv_text)
    skills = list(set(regex_skills + ai_skills))

    # Actualizar en BD
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile()
        db.add(profile)

    profile.cv_filename = file.filename
    profile.cv_file_path = f"/static/uploads/cvs/{file.filename}"
    profile.cv_text = cv_text
    profile.cv_skills = list(set(profile.cv_skills + skills)) if profile.cv_skills else skills

    await db.commit()
    await db.refresh(profile)
    
    await _reset_and_trigger_scrape(db, profile, background_tasks)
    return profile
