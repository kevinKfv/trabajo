from fastapi import APIRouter
from app.api.v1.endpoints import health, jobs, scrape, profile, search_configs, auto_apply, tailored_documents, crm, recommendations, analytics, admin, chat, config

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(scrape.router, tags=["Scraping & AI"])
api_router.include_router(profile.router, prefix="/profile", tags=["Perfil & CV"])
api_router.include_router(search_configs.router, prefix="/search-configs", tags=["Configuración de Búsquedas"])
api_router.include_router(auto_apply.router, prefix="/auto-apply", tags=["Auto-Apply"])
api_router.include_router(tailored_documents.router, tags=["Documentos Adaptados"])
api_router.include_router(crm.router, prefix="/crm", tags=["CRM & Calendario"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recomendaciones & Multicanal"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analítica"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administración"])
api_router.include_router(chat.router, prefix="/chat", tags=["IA Conversacional"])
api_router.include_router(config.router, prefix="/config", tags=["Configuración Sistema"])





