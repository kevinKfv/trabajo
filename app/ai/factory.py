from app.ai.base import BaseAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.ollama_provider import OllamaProvider
from app.core.config import settings
from app.core.logging import logger


class AIFactory:
    """Fábrica para instanciar el proveedor de IA configurado en las variables de entorno."""

    @staticmethod
    def get_provider() -> BaseAIProvider:
        provider_name = settings.AI_PROVIDER.lower()

        if provider_name == "groq" or (settings.GROQ_API_KEY and not settings.OPENAI_API_KEY):
            logger.info("Instanciando proveedor de IA: Groq")
            return OpenAIProvider(api_key=settings.GROQ_API_KEY)
        elif provider_name == "openai" and settings.OPENAI_API_KEY:
            logger.info("Instanciando proveedor de IA: OpenAI")
            return OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        elif provider_name == "ollama":
            logger.info("Instanciando proveedor de IA: Ollama (local)")
            return OllamaProvider()
        else:
            key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
            if settings.GROQ_API_KEY and not settings.OPENAI_API_KEY:
                logger.info("Instanciando proveedor de IA: Groq (fallback)")
                return OpenAIProvider(api_key=settings.GROQ_API_KEY)
            logger.info("Instanciando proveedor de IA por defecto: OpenAI")
            return OpenAIProvider(api_key=key)
