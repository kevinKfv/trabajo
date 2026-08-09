import json
import httpx
from app.ai.base import BaseAIProvider, AIAnalysisResult
from app.core.config import settings
from app.core.logging import logger


class OllamaProvider(BaseAIProvider):
    """Proveedor de IA local para ejecutar análisis sin costo utilizando Ollama."""

    def __init__(self, base_url: str = "", model: str = "llama3") -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or "llama3"
        self.endpoint = f"{self.base_url}/api/chat"

    async def analyze_job(self, job_description: str, cv_text: str) -> AIAnalysisResult:
        system_prompt = (
            "Eres un experto senior en reclutamiento técnico del mercado IT de Argentina y Latinoamérica. "
            "Analiza la oferta laboral y compárala con el CV del candidato. "
            "Responde SOLAMENTE en formato JSON con la siguiente estructura exacta:\n"
            "{\n"
            '  "summary": "Resumen de 2-3 oraciones: qué hace el puesto, stack principal, tipo de empresa",\n'
            '  "technologies": ["Tech1", "Tech2", "Tech3"],\n'
            '  "seniority": "Trainee/Junior/Semi-Senior/Senior/Lead",\n'
            '  "match_score": 75.0,\n'
            '  "reasoning": "Explicación de 3-5 oraciones sobre coincidencias y brechas del candidato con la oferta",\n'
            '  "advantages": ["Skill del candidato que coincide con la oferta"],\n'
            '  "missing_skills": ["Requisito de la oferta que le falta al candidato"],\n'
            '  "interview_probability": "Alta/Media/Baja",\n'
            '  "recommendation": "Aplicar inmediatamente/Revisar requisitos antes de aplicar/Probablemente no apto"\n'
            "}\n"
            "match_score debe ser 80+ si cumple casi todo, 50-79 si cumple lo básico, menos de 50 si hay brechas críticas. "
            "Si el CV está vacío, asigna match_score 0. Responde SOLO con el JSON, sin texto adicional."
        )

        user_prompt = (
            f"=== CV DEL CANDIDATO ===\n{cv_text or '(CV vacío)'}\n\n"
            f"=== OFERTA LABORAL ===\n{job_description}"
        )


        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": "json",
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.endpoint, json=payload)
                response.raise_for_status()
                data = response.json()

                content = data.get("message", {}).get("content", "{}")
                parsed = json.loads(content)

                advantages = parsed.get("advantages", [])
                missing_skills = parsed.get("missing_skills", [])
                score = float(parsed.get("match_score", 0.0))

                interview_prob = parsed.get("interview_probability", "Alta" if score >= 80 else ("Media" if score >= 50 else "Baja"))
                rec = parsed.get("recommendation", "Aplicar inmediatamente" if score >= 80 else ("Revisar requisitos" if score >= 50 else "Descartar"))

                return AIAnalysisResult(
                    summary=parsed.get("summary", "Sin resumen de Ollama"),
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
            logger.error(f"Error al conectar con Ollama en {self.endpoint}: {e}")
            return AIAnalysisResult(
                summary="Error de conexión con Ollama",
                technologies=[],
                seniority="Desconocido",
                match_score=0.0,
                reasoning=f"Ollama no disponible en {self.base_url}: {str(e)}",
                advantages=[],
                missing_skills=[],
                interview_probability="Baja",
                recommendation="Descartar"
            )

    async def extract_cv_skills(self, cv_text: str) -> list[str]:
        system_prompt = (
            "Eres un experto en reclutamiento. Extrae las habilidades del CV. "
            "Responde SOLAMENTE en formato JSON con la siguiente estructura:\n"
            "{\n"
            '  "skills": ["Habilidad1", "Habilidad2"]\n'
            "}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": cv_text}
            ],
            "format": "json",
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data.get("message", {}).get("content", "{}")
                parsed = json.loads(content)
                return parsed.get("skills", [])
        except Exception as e:
            logger.error(f"Error extrayendo skills con Ollama: {e}")
            return []
