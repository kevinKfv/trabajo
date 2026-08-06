import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_endpoint(client: AsyncClient):
    """Verifica que la ruta raíz '/' sirva el Dashboard HTML."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "Job Hunter AI" in response.text
    assert "Dashboard" in response.text


@pytest.mark.asyncio
async def test_static_css_endpoint(client: AsyncClient):
    """Verifica que el archivo CSS estático esté disponible."""
    response = await client.get("/static/css/style.css")
    assert response.status_code == 200
    assert "--bg-primary" in response.text
