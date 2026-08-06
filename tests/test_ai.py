import pytest
from app.ai.factory import AIFactory
from app.ai.openai_provider import OpenAIProvider
from app.ai.ollama_provider import OllamaProvider
from app.ai.base import AIAnalysisResult
from app.core.config import settings


def test_ai_factory():
    """Verifica que AIFactory instancie los proveedores correctamente."""
    provider = AIFactory.get_provider()
    assert isinstance(provider, (OpenAIProvider, OllamaProvider))


@pytest.mark.asyncio
async def test_openai_provider_fallback():
    """Verifica la respuesta segura del proveedor OpenAI/Groq cuando se pasa api_key vacía."""
    provider = OpenAIProvider(api_key="")
    # Forzar temporalmente que no tome la de settings para la prueba de fallback
    provider.api_key = ""
    result = await provider.analyze_job(
        job_description="Puesto Senior Python",
        cv_text="Desarrollador Python"
    )

    assert isinstance(result, AIAnalysisResult)
    assert result.match_score == 50.0
    assert "Configure OPENAI_API_KEY" in result.summary


@pytest.mark.asyncio
async def test_ollama_provider_fallback():
    """Verifica el manejo de errores del proveedor Ollama cuando el servidor no está corriendo."""
    provider = OllamaProvider(base_url="http://localhost:99999")
    result = await provider.analyze_job(
        job_description="Desarrollador Backend",
        cv_text="Programador Python"
    )

    assert isinstance(result, AIAnalysisResult)
    assert result.match_score == 0.0
    assert "Error de conexión" in result.summary
