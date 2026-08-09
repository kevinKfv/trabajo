from typing import AsyncGenerator
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.database.base import Base
from app.core.logging import logger

# Motor de base de datos asíncrono SQLAlchemy
engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    echo=False, # settings.DEBUG by default logs all SQL queries, disable it for cleaner console
    future=True,
    pool_pre_ping=True
)

# Generador de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


def _auto_migrate_columns(sync_conn):
    """Verifica e inserta columnas faltantes en tablas existentes sin requerir migraciones manuales."""
    inspector = inspect(sync_conn)
    db_tables = inspector.get_table_names()

    # Columnas esperadas por tabla y sus definiciones SQL seguras
    column_definitions = {
        "search_configs": {
            "exclude_keywords": "JSON DEFAULT '[]'",
            "min_salary": "JSON DEFAULT 'null'",
            "currency": "VARCHAR DEFAULT 'ARS'",
            "frequency_hours": "INTEGER DEFAULT 2",
            "date_filter": "VARCHAR DEFAULT 'all'",
            "target_cv_version_id": "INTEGER",
            "device_id": "VARCHAR DEFAULT 'global'"
        },
        "jobs": {
            "technologies": "JSON DEFAULT '[]'",
            "seniority": "VARCHAR",
            "source": "VARCHAR DEFAULT 'linkedin'",
            "status": "VARCHAR DEFAULT 'NEW'",
            "ai_score": "FLOAT",
            "ai_analysis": "JSON",
            "device_id": "VARCHAR DEFAULT 'global'"
        },
        "user_profiles": {
            "cv_skills": "JSON DEFAULT '[]'",
            "cv_filename": "VARCHAR",
            "cv_file_path": "VARCHAR",
            "cv_text": "TEXT",
            "device_id": "VARCHAR DEFAULT 'global'"
        }
    }

    for table_name, columns in column_definitions.items():
        if table_name in db_tables:
            existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
            for col_name, col_def in columns.items():
                if col_name not in existing_cols:
                    try:
                        alter_query = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}"
                        sync_conn.execute(text(alter_query))
                        logger.info(f"Columna agregada automáticamente a {table_name}: {col_name}")
                    except Exception as e:
                        logger.warning(f"No se pudo agregar columna {col_name} a {table_name}: {e}")


async def init_db() -> None:
    """Crea las tablas y migra columnas faltantes en la base de datos automáticamente."""
    # Importar modelos para registrarlos en Base.metadata antes de create_all
    import app.models  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_auto_migrate_columns)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Inyector de dependencias FastAPI para obtener sesión de base de datos."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
