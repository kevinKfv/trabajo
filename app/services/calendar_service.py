from datetime import datetime, timedelta
from typing import Optional


class CalendarService:
    """Servicio para la generación de archivos iCal (.ics) y enlaces de Google Calendar."""

    @staticmethod
    def generate_ics_content(
        title: str,
        description: str,
        start_time: datetime,
        duration_minutes: int = 45,
        location: str = "Videollamada / Remoto"
    ) -> str:
        """Genera el contenido estándar en formato iCalendar (.ics) para exportación de eventos."""
        end_time = start_time + timedelta(minutes=duration_minutes)
        fmt = "%Y%m%dT%H%M%SZ"
        
        start_str = start_time.strftime(fmt)
        end_str = end_time.strftime(fmt)
        now_str = datetime.utcnow().strftime(fmt)

        ics_text = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Job Hunter AI//CRM Calendar//ES
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
SUMMARY:{title}
DESCRIPTION:{description}
LOCATION:{location}
DTSTART:{start_str}
DTEND:{end_str}
DTSTAMP:{now_str}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
        return ics_text.strip()

    @staticmethod
    def generate_google_calendar_url(
        title: str,
        description: str,
        start_time: datetime,
        duration_minutes: int = 45,
        location: str = "Videollamada / Remoto"
    ) -> str:
        """Genera un enlace directo para agregar el evento a Google Calendar en 1-click."""
        from urllib.parse import quote
        end_time = start_time + timedelta(minutes=duration_minutes)
        fmt = "%Y%m%dT%H%M%SZ"
        
        dates = f"{start_time.strftime(fmt)}/{end_time.strftime(fmt)}"
        base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
        
        url = (
            f"{base_url}&text={quote(title)}"
            f"&dates={dates}"
            f"&details={quote(description)}"
            f"&location={quote(location)}"
        )
        return url
