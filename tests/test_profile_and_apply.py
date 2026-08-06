import pytest
from httpx import AsyncClient
from app.services.cv_parser_service import CVParserService


@pytest.mark.asyncio
async def test_cv_parser_extract_skills():
    sample_text = """
    Soy desarrollador Python y React. Tengo experiencia en PostgreSQL, Docker, FastApi y Git.
    Nivel de inglés intermedio.
    """
    skills = CVParserService.extract_skills(sample_text)
    assert "Python" in skills or "PYTHON" in skills
    assert "React" in skills or "REACT" in skills
    assert "Docker" in skills or "DOCKER" in skills


@pytest.mark.asyncio
async def test_get_and_update_profile(client: AsyncClient):
    # GET profile
    res = await client.get("/api/v1/profile")
    assert res.status_code == 200
    data = res.json()
    assert "full_name" in data

    # PUT profile
    update_res = await client.put("/api/v1/profile", json={
        "full_name": "Juan Perez",
        "email": "juan@example.com",
        "phone": "+541112345678"
    })
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["full_name"] == "Juan Perez"
    assert updated_data["email"] == "juan@example.com"


@pytest.mark.asyncio
async def test_search_config_crud(client: AsyncClient):
    # CREATE search config
    create_res = await client.post("/api/v1/search-configs", json={
        "name": "Pasantías Tech",
        "keywords": ["pasantía", "pasante"],
        "sources": ["linkedin", "bumeran"],
        "location": "Buenos Aires, Argentina",
        "remote_only": True
    })
    assert create_res.status_code == 201
    config_data = create_res.json()
    config_id = config_data["id"]
    assert config_data["name"] == "Pasantías Tech"

    # LIST search configs
    list_res = await client.get("/api/v1/search-configs")
    assert list_res.status_code == 200
    configs = list_res.json()
    assert len(configs) >= 1

    # DELETE search config
    del_res = await client.delete(f"/api/v1/search-configs/{config_id}")
    assert del_res.status_code == 204
