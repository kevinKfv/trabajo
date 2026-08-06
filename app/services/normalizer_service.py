import re
from typing import List
from app.schemas.job import JobCreate
from app.utils.text_cleaner import clean_text, detect_remote, detect_seniority
from app.utils.tech_extractor import extract_technologies


class NormalizerService:
    """Servicio de normalización para estandarizar y enriquecer ofertas laborales."""

    @staticmethod
    def normalize_title(title: str) -> str:
        """Limpia y estandariza el título del puesto eliminando prefijos publicitarios."""
        cleaned = clean_text(title)
        
        # Eliminar prefijos publicitarios en cadena (ej: "Buscamos Urgente:")
        pattern = r"^(buscamos|se busca|urgente|contratación inmediata|búsqueda|se necesita|oferta)[:\s\-]*"
        while re.search(pattern, cleaned, flags=re.IGNORECASE):
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
            
        return cleaned

    @staticmethod
    def normalize_company(company: str) -> str:
        """Estandariza el nombre de la empresa eliminando legal/corporate suffixes."""
        cleaned = clean_text(company)
        # Eliminar sufijos legales de tipo de sociedad (S.A., S.R.L., LLC, Inc.)
        cleaned = re.sub(r"\b(S\.A\.|S\.A|S\.R\.L\.|SRL|Inc\.|LLC|Ltd\.|GmbH)\b", "", cleaned, flags=re.IGNORECASE)
        # Limpiar puntuación sobrante y espacios dobles
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,-")
        return cleaned

    @classmethod
    def normalize_job(cls, job: JobCreate) -> JobCreate:
        """Aplica la canalización completa de normalización sobre un JobCreate."""
        norm_title = cls.normalize_title(job.title)
        norm_company = cls.normalize_company(job.company)
        norm_location = clean_text(job.location) or "No especificada"

        # Combinar texto completo para detección avanzada
        combined_text = f"{norm_title} {job.description} {norm_location}"

        is_remote = job.remote or detect_remote(combined_text)
        seniority = job.seniority or detect_seniority(norm_title) or detect_seniority(job.description)

        # Enriquecer tecnologías combinando las del scraper y las detectadas en la descripción
        extracted_techs = extract_technologies(combined_text)
        all_techs = sorted(list(set(job.technologies + extracted_techs)))

        return JobCreate(
            title=norm_title,
            company=norm_company,
            location=norm_location,
            salary=clean_text(job.salary) if job.salary else None,
            remote=is_remote,
            seniority=seniority,
            description=clean_text(job.description),
            technologies=all_techs,
            url=job.url.strip(),
            published_date=job.published_date,
            source=job.source.lower().strip()
        )

    @classmethod
    def normalize_batch(cls, jobs: List[JobCreate]) -> List[JobCreate]:
        """Normaliza una lista de empleos."""
        return [cls.normalize_job(j) for j in jobs]
