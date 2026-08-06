import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.database.session import init_db
from app.api.v1.router import api_router

# Inicialización de logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación FastAPI (startup y shutdown)."""
    logger.info(f"Iniciando {settings.PROJECT_NAME} en entorno [{settings.ENVIRONMENT}]...")
    
    # Crear tablas en BD al arrancar (en desarrollo)
    try:
        await init_db()
        logger.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logger.error(f"No se pudo conectar/inicializar la BD al arrancar: {e}")

    # Arrancar el scheduler de tareas en segundo plano
    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"Error al iniciar el scheduler: {e}")

    yield

    # Detener scheduler
    shutdown_scheduler()
    logger.info(f"Apagando {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos del frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Inclusión de routers de API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
@app.get("/dashboard")
async def serve_dashboard():
    """Sirve la interfaz web interactiva del Dashboard Job Hunter AI."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": f"Bienvenido a {settings.PROJECT_NAME} API",
        "docs": f"{settings.API_V1_STR}/docs",
        "version": "1.0.0"
    }
