import pytest
from app.schemas.job import JobCreate
from app.services.normalizer_service import NormalizerService
from app.services.deduplication_service import DeduplicationService


def test_normalizer_service():
    """Verifica que NormalizerService limpie y estandarice títulos, empresas y tecnologías."""
    raw_job = JobCreate(
        title="  Buscamos Urgente: Senior Python Developer  ",
        company=" Acme Corporation S.A. ",
        location=" Buenos Aires ",
        salary="$2000 - $3000 USD",
        remote=False,
        description="Puesto 100% Home Office requiriendo FastAPI, Docker y PostgreSQL.",
        technologies=["Python"],
        url="https://example.com/job/1",
        published_date=None,
        source="linkedin"
    )

    normalized = NormalizerService.normalize_job(raw_job)

    assert normalized.title == "Senior Python Developer"
    assert normalized.company == "Acme Corporation"
    assert normalized.location == "Buenos Aires"
    assert normalized.remote is True
    assert normalized.seniority == "Senior"
    assert "FastAPI" in normalized.technologies
    assert "Docker" in normalized.technologies
    assert "PostgreSQL" in normalized.technologies


def test_deduplication_service_similar_jobs():
    """Verifica que DeduplicationService detecte ofertas duplicadas entre distintas plataformas."""
    job1 = JobCreate(
        title="Senior Python Developer",
        company="Acme Corp",
        location="Remote",
        description="Python backend role",
        technologies=["Python"],
        url="https://linkedin.com/jobs/101",
        source="linkedin"
    )

    job2 = JobCreate(
        title="Senior Python Developer",
        company="Acme Corporation",
        location="Remoto",
        description="Backend role Python",
        technologies=["Python"],
        url="https://computrabajo.com/jobs/999",
        source="computrabajo"
    )

    is_sim = DeduplicationService.are_jobs_similar(job1, job2.title, job2.company)
    assert is_sim is True


def test_deduplication_in_memory_batch():
    """Verifica que la deduplicación en memoria filtre duplicados dentro de un lote consolidado."""
    job1 = JobCreate(
        title="Backend Engineer Python",
        company="Tech Company",
        location="Remote",
        description="Role 1",
        technologies=["Python"],
        url="https://source1.com/job/1",
        source="source1"
    )

    job2 = JobCreate(
        title="Backend Engineer Python",
        company="Tech Company",
        location="Remote",
        description="Role 1 - Duplicate",
        technologies=["Python"],
        url="https://source2.com/job/2",
        source="source2"
    )

    job3 = JobCreate(
        title="Frontend React Engineer",
        company="Other Company",
        location="Remote",
        description="Role 2",
        technologies=["React"],
        url="https://source1.com/job/3",
        source="source1"
    )

    raw_batch = [job1, job2, job3]
    unique_batch = DeduplicationService.deduplicate_in_memory(raw_batch)

    assert len(unique_batch) == 2
    assert unique_batch[0].title == "Backend Engineer Python"
    assert unique_batch[1].title == "Frontend React Engineer"
