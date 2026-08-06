import json
import httpx
from app.ai.base import BaseAIProvider, AIAnalysisResult
from app.core.config import settings
from app.core.logging import logger


class OpenAIProvider(BaseAIProvider):
    """Proveedor de IA para analizar ofertas utilizando la API de OpenAI o Groq (compatible con OpenAI)."""

    def __init__(self, api_key: str = "", model: str = "", base_url: str = "") -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.AI_MODEL
        
        # Detección automática de Groq (claves que inician con gsk_) o URL personalizada
        custom_url = base_url or settings.OPENAI_BASE_URL
        if custom_url:
            base = custom_url.rstrip("/")
            self.endpoint = f"{base}/chat/completions" if not base.endswith("/chat/completions") else base
        elif self.api_key.startswith("gsk_"):
            self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
            if self.model in ("gpt-4o-mini", "gpt-4o", ""):
                self.model = "llama-3.3-70b-versatile"
            logger.info(f"Clave API de Groq detectada. Usando endpoint de Groq con modelo '{self.model}'.")
        else:
            self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def analyze_job(self, job_description: str, cv_text: str) -> AIAnalysisResult:
        if not self.api_key:
            logger.warning("OPENAI_API_KEY no configurada. Generando análisis de respaldo en modo mock.")
            return AIAnalysisResult(
                summary="Resumen no disponible. Configure OPENAI_API_KEY en .env",
                technologies=[],
                seniority="Desconocido",
                match_score=50.0,
                reasoning="Clave API no configurada."
            )

        system_prompt = (
            "Eres un experto en reclutamiento técnico e IA. Tu tarea es analizar una oferta laboral "
            "y compararla con el CV del candidato. Debes responder EXCLUSIVAMENTE en formato JSON "
            "con las siguientes claves exactas:\n"
            "- 'summary': (string) Resumen conciso de 2 oraciones sobre el puesto.\n"
            "- 'technologies': (lista de strings) Tecnologías principales requeridas.\n"
            "- 'seniority': (string) Nivel detectado (Junior, Semi-Senior, Senior, Lead).\n"
            "- 'match_score': (float 0-100) Grado de compatibilidad con el CV.\n"
            "- 'reasoning': (string) Explicación de las coincidencias y brechas.\n"
            "- 'advantages': (lista de strings) Habilidades que el candidato posee y coinciden con la oferta.\n"
            "- 'missing_skills': (lista de strings) Requisitos clave que el candidato no tiene.\n"
            "- 'interview_probability': (string) Probabilidad de entrevista (Alta, Media, Baja).\n"
            "- 'recommendation': (string) Recomendación sobre si aplicar ('Aplicar inmediatamente', 'Revisar requisitos', 'Descartar')."
        )

        user_prompt = f"CV DEL CANDIDATO:\n{cv_text}\n\nOFERTA LABORAL:\n{job_description}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                advantages = parsed.get("advantages", [])
                missing_skills = parsed.get("missing_skills", [])
                score = float(parsed.get("match_score", 0.0))

                interview_prob = parsed.get("interview_probability", "Alta" if score >= 80 else ("Media" if score >= 50 else "Baja"))
                rec = parsed.get("recommendation", "Aplicar inmediatamente" if score >= 80 else ("Revisar requisitos" if score >= 50 else "Descartar"))

                return AIAnalysisResult(
                    summary=parsed.get("summary", "Sin resumen"),
                    technologies=parsed.get("technologies", []),
                    seniority=parsed.get("seniority", "No especificado"),
                    match_score=score,
                    reasoning=parsed.get("reasoning", "Sin justificación"),
                    advantages=advantages if isinstance(advantages, list) else [str(advantages)],
                    missing_skills=missing_skills if isinstance(missing_skills, list) else [str(missing_skills)],
                    interview_probability=interview_prob,
                    recommendation=rec
                )
        except Exception as e:
            logger.error(f"Error al llamar a la API de IA ({self.endpoint}): {e}", exc_info=True)
            return AIAnalysisResult(
                summary="Error en procesamiento de IA",
                technologies=[],
                seniority="Error",
                match_score=0.0,
                reasoning=f"Error durante el análisis con IA: {str(e)}",
                advantages=[],
                missing_skills=[],
                interview_probability="Baja",
                recommendation="Descartar"
            )

    async def extract_cv_skills(self, cv_text: str) -> list[str]:
        if not self.api_key:
            return []

        system_prompt = (
            "Eres un experto en reclutamiento técnico. Extrae todas las habilidades "
            "técnicas y herramientas relevantes del siguiente texto de CV. "
            "Responde EXCLUSIVAMENTE con un JSON con la clave 'skills' conteniendo "
            "una lista de strings (por ejemplo: {\"skills\": [\"Python\", \"React\"]})."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": cv_text}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                return parsed.get("skills", [])
        except Exception as e:
            logger.error(f"Error extrayendo skills con IA ({self.endpoint}): {e}")
            return []
