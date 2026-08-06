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

        if provider_name == "openai":
            logger.info("Instanciando proveedor de IA: OpenAI")
            return OpenAIProvider()
        elif provider_name == "ollama":
            logger.info("Instanciando proveedor de IA: Ollama (local)")
            return OllamaProvider()
        else:
            logger.warning(f"Proveedor '{provider_name}' desconocido. Usando OpenAI por defecto.")
            return OpenAIProvider()
