from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.chat_assistant_service import ChatAssistantService

router = APIRouter()


class ChatQueryRequest(BaseModel):
    query: str


@router.post("/query")
async def process_chat_query(
    req: ChatQueryRequest,
    x_device_id: str = Header(default="global", alias="X-Device-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Procesa una consulta en lenguaje natural mediante el Asistente de IA Conversacional."""
    service = ChatAssistantService(db)
    return await service.answer_user_query(req.query, device_id=x_device_id)
