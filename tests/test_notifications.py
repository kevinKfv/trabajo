import pytest
from app.notifications.telegram_provider import TelegramNotificationProvider
from app.notifications.email_provider import EmailNotificationProvider
from app.schemas.job import JobResponse
from datetime import datetime


@pytest.mark.asyncio
async def test_telegram_provider_mock_behavior():
    """Verifica que el proveedor de Telegram responda de forma segura cuando no hay credenciales."""
    provider = TelegramNotificationProvider(bot_token="", chat_id="")
    provider.bot_token = ""
    provider.chat_id = ""
    jobs = [
        JobResponse(
            id=1,
            title="Senior Python Engineer",
            company="Acme Inc",
            location="Remote",
            salary="$4000",
            remote=True,
            seniority="Senior",
            description="Role description",
            technologies=["Python", "FastAPI"],
            url="https://example.com/job/1",
            published_date=None,
            source="linkedin",
            status="ANALYZED",
            ai_score=90.0,
            ai_summary="Excelente coincidencia con tu perfil",
            ai_analysis={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    result = await provider.send_notification(jobs)
    assert result is False  # Falso indica modo mock por falta de tokens


@pytest.mark.asyncio
async def test_email_provider_mock_behavior():
    """Verifica el comportamiento de resiliencia del proveedor de Email cuando no hay credenciales SMTP."""
    provider = EmailNotificationProvider()
    provider.smtp_user = ""
    provider.email_to = ""
    jobs = [
        JobResponse(
            id=1,
            title="Senior Python Engineer",
            company="Acme Inc",
            location="Remote",
            salary="$4000",
            remote=True,
            seniority="Senior",
            description="Role description",
            technologies=["Python"],
            url="https://example.com/job/1",
            published_date=None,
            source="linkedin",
            status="ANALYZED",
            ai_score=90.0,
            ai_summary="Resumen",
            ai_analysis={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    result = await provider.send_notification(jobs)
    assert result is False  # Falso indica modo mock por falta de credenciales SMTP
