import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import set_key
from app.core.config import settings

router = APIRouter()

class ConfigUpdate(BaseModel):
    AI_PROVIDER: str
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

@router.get("/")
async def get_config():
    """Obtiene la configuración actual de APIs y notificaciones."""
    return {
        "AI_PROVIDER": settings.AI_PROVIDER,
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "GROQ_API_KEY": settings.GROQ_API_KEY,
        "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
        "TELEGRAM_BOT_TOKEN": settings.TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": settings.TELEGRAM_CHAT_ID,
    }

@router.post("/")
async def update_config(config_data: ConfigUpdate):
    """Actualiza la configuración en memoria y la persiste en .env."""
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env")
    
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            pass

    try:
        # Update settings object in memory
        settings.AI_PROVIDER = config_data.AI_PROVIDER
        settings.OPENAI_API_KEY = config_data.OPENAI_API_KEY
        settings.GROQ_API_KEY = config_data.GROQ_API_KEY
        settings.ANTHROPIC_API_KEY = config_data.ANTHROPIC_API_KEY
        settings.TELEGRAM_BOT_TOKEN = config_data.TELEGRAM_BOT_TOKEN
        settings.TELEGRAM_CHAT_ID = config_data.TELEGRAM_CHAT_ID

        # Update .env file
        set_key(env_file, "AI_PROVIDER", config_data.AI_PROVIDER)
        set_key(env_file, "OPENAI_API_KEY", config_data.OPENAI_API_KEY)
        set_key(env_file, "GROQ_API_KEY", config_data.GROQ_API_KEY)
        set_key(env_file, "ANTHROPIC_API_KEY", config_data.ANTHROPIC_API_KEY)
        set_key(env_file, "TELEGRAM_BOT_TOKEN", config_data.TELEGRAM_BOT_TOKEN)
        set_key(env_file, "TELEGRAM_CHAT_ID", config_data.TELEGRAM_CHAT_ID)

        return {"message": "Configuración guardada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
