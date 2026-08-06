import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from app.notifications.base import BaseNotificationProvider
from app.schemas.job import JobResponse
from app.core.config import settings
from app.core.logging import logger


class EmailNotificationProvider(BaseNotificationProvider):
    """Proveedor de notificaciones por correo electrónico vía SMTP."""

    def __init__(self) -> None:
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_to = settings.NOTIFICATION_EMAIL_TO

    async def send_notification(self, jobs: List[JobResponse]) -> bool:
        if not self.smtp_user or not self.email_to:
            logger.warning("Credenciales SMTP o correo de destino no configurados. Modo mock para Email.")
            return False

        if not jobs:
            return True

        # Construir resumen HTML consolidado
        html_items = ""
        for job in jobs:
            score_str = f"{job.ai_score:.0f}/100" if job.ai_score is not None else "N/A"
            html_items += f"""
            <div style="border: 1px solid #e0e0e0; padding: 15px; margin-bottom: 15px; border-radius: 8px;">
                <h3 style="color: #1a73e8; margin-top: 0;">{job.title} - {job.company}</h3>
                <p><strong>Ubicación:</strong> {job.location or 'N/A'} | <strong>Score IA:</strong> <span style="color: #2e7d32; font-weight: bold;">{score_str}</span></p>
                <p><strong>Resumen IA:</strong> {job.ai_summary or 'Sin resumen'}</p>
                <p><a href="{job.url}" style="background-color: #1a73e8; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px;">Ver Oferta</a></p>
            </div>
            """

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>🎯 Job Hunter AI - Resumen de Ofertas Destacadas</h2>
                <p>Se han encontrado <strong>{len(jobs)}</strong> empleos nuevos con alta coincidencia:</p>
                {html_items}
            </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎯 Job Hunter AI: {len(jobs)} nuevas ofertas destacadas"
        msg["From"] = self.smtp_user
        msg["To"] = self.email_to

        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            logger.info(f"Correo de notificación enviado exitosamente a {self.email_to}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar correo electrónico SMTP: {e}")
            return False
