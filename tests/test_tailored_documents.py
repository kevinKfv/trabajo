import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_tailored_cv_and_cover_letter(client: AsyncClient):
    # 1. Crear un job de prueba vía API o verificar lista
    res = await client.get("/api/v1/jobs")
    assert res.status_code == 200
    jobs = res.json().get("items", [])

    if len(jobs) > 0:
        job_id = jobs[0]["id"]
        # Probamos el endpoint de CV adaptado
        cv_res = await client.post(f"/api/v1/jobs/{job_id}/generate-cv")
        assert cv_res.status_code == 200
        cv_data = cv_res.json()
        assert "tailored_cv_markdown" in cv_data
        assert "job_title" in cv_data

        # Probamos el endpoint de carta de presentación
        cl_res = await client.post(f"/api/v1/jobs/{job_id}/generate-cover-letter")
        assert cl_res.status_code == 200
        cl_data = cl_res.json()
        assert "cover_letter_text" in cl_data
        assert "company" in cl_data
