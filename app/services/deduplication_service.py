import re
from difflib import SequenceMatcher
from typing import List
from app.schemas.job import JobCreate
from app.core.logging import logger


class DeduplicationService:
    """Servicio de deduplicación difusa (fuzzy deduplication) para identificar ofertas equivalentes."""

    TITLE_SIMILARITY_THRESHOLD = 0.75
    COMPANY_SIMILARITY_THRESHOLD = 0.75

    @staticmethod
    def _normalize_tokens(text: str) -> str:
        """Normaliza, expande abreviaturas comunes y ordena tokens de palabras."""
        if not text:
            return ""
        cleaned = text.lower()
        cleaned = re.sub(r"\bcorp\b", "corporation", cleaned)
        cleaned = re.sub(r"\binc\b", "incorporated", cleaned)
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        words = cleaned.split()
        return " ".join(sorted(words))

    @classmethod
    def _string_similarity(cls, str1: str, str2: str) -> float:
        """Calcula el ratio de similitud entre dos cadenas de texto (0.0 a 1.0) considerando alias y tokens."""
        if not str1 or not str2:
            return 0.0
        
        # Comparación por conjunto de tokens normalizados y ordenados
        tokens1 = cls._normalize_tokens(str1)
        tokens2 = cls._normalize_tokens(str2)
        
        if tokens1 == tokens2:
            return 1.0

        token_ratio = SequenceMatcher(None, tokens1, tokens2).ratio()
        raw_ratio = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

        return max(raw_ratio, token_ratio)

    @classmethod
    def are_jobs_similar(cls, job1: JobCreate, job2_title: str, job2_company: str) -> bool:
        """Evalúa si dos ofertas son equivalentes según la similitud de su título y empresa."""
        title_sim = cls._string_similarity(job1.title, job2_title)
        company_sim = cls._string_similarity(job1.company, job2_company)

        if company_sim >= cls.COMPANY_SIMILARITY_THRESHOLD and title_sim >= cls.TITLE_SIMILARITY_THRESHOLD:
            return True

        return False

    @classmethod
    def deduplicate_in_memory(cls, jobs: List[JobCreate]) -> List[JobCreate]:
        """Elimina duplicados dentro de un mismo lote extraído en memoria."""
        unique_jobs: List[JobCreate] = []

        for job in jobs:
            is_dup = False
            for existing in unique_jobs:
                if job.url == existing.url:
                    is_dup = True
                    break
                if cls.are_jobs_similar(job, existing.title, existing.company):
                    is_dup = True
                    logger.debug(f"Duplicado difuso detectado en memoria: '{job.title}' @ '{job.company}' vs '{existing.title}'")
                    break

            if not is_dup:
                unique_jobs.append(job)

        return unique_jobs
