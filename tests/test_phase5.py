import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analytics_dashboard(client: AsyncClient):
    res = await client.get("/api/v1/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "total_jobs" in data
    assert "status_distribution" in data
    assert "top_technologies" in data


@pytest.mark.asyncio
async def test_scrapers_status(client: AsyncClient):
    res = await client.get("/api/v1/admin/scrapers-status")
    assert res.status_code == 200
    scrapers = res.json()
    assert isinstance(scrapers, list)
    assert len(scrapers) >= 1
    assert "name" in scrapers[0]


@pytest.mark.asyncio
async def test_chat_assistant_query(client: AsyncClient):
    res = await client.post("/api/v1/chat/query", json={
        "query": "¿Qué ofertas de Python remota hay disponibles?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "query" in data
