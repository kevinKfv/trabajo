import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_crm_kanban_and_reminders(client: AsyncClient):
    # 1. Obtenemos el tablero Kanban
    res = await client.get("/api/v1/crm/kanban")
    assert res.status_code == 200
    board = res.json()
    assert "POSTULADO" in board
    assert "ENTREVISTA_TECNICA" in board

    # 2. Creamos un recordatorio
    rem_res = await client.post("/api/v1/crm/reminders", json={
        "title": "Entrevista Técnica con Empresa X",
        "description": "Repasar algoritmos y Python",
        "remind_at": "2026-08-10T15:00:00Z",
        "reminder_type": "ENTREVISTA"
    })
    assert rem_res.status_code == 201
    rem_data = rem_res.json()
    assert rem_data["title"] == "Entrevista Técnica con Empresa X"

    # 3. Listamos recordatorios
    list_rem = await client.get("/api/v1/crm/reminders")
    assert list_rem.status_code == 200
    reminders = list_rem.json()
    assert len(reminders) >= 1
