import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job, JobStatus


@pytest.mark.asyncio
async def test_recommendations_and_feedback(client: AsyncClient, db_session: AsyncSession):
    # 1. Insertar trabajo de prueba
    job = Job(
        title="Senior Python Developer",
        company="TechCorp",
        location="Remoto",
        description="Buscamos dev Python con FastAPI y Docker",
        technologies=["Python", "FastAPI", "Docker"],
        url="https://example.com/job/test1",
        source="linkedin",
        status=JobStatus.NEW,
        ai_score=88.0
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # 2. Enviar feedback de guardado
    fb_res = await client.post(f"/api/v1/recommendations/feedback/{job.id}", json={"action": "SAVED"})
    assert fb_res.status_code == 200
    assert fb_res.json()["action"] == "SAVED"

    # 3. Obtener lista de recomendados por ranking multidimensional
    rec_res = await client.get("/api/v1/recommendations/jobs")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["total"] >= 1
    assert "items" in rec_data


@pytest.mark.asyncio
async def test_multichannel_notification(client: AsyncClient):
    notif_res = await client.post("/api/v1/recommendations/notify/multichannel", json={
        "title": "Oferta Recomendada: Backend Python",
        "message": "Match 92% - Remoto 🏠",
        "url": "https://example.com/job/1"
    })
    assert notif_res.status_code == 200
    assert "success" in notif_res.json()
