import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Verifica que el endpoint raíz '/' responda 200 OK y sirva la interfaz HTML."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "Job Hunter AI" in response.text


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Verifica que el endpoint /api/v1/health responda correctamente."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_jobs_empty_list(client: AsyncClient):
    """Verifica que el endpoint /api/v1/jobs responda con lista vacía cuando no hay empleos."""
    response = await client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
