from fastapi import APIRouter, Depends
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
    db: AsyncSession = Depends(get_db)
):
    """Procesa una consulta en lenguaje natural mediante el Asistente de IA Conversacional."""
    service = ChatAssistantService(db)
    return await service.answer_user_query(req.query)
