import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configura el sistema de logging estructurado del proyecto."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reducir verbosidad de librerías externas de scraping / HTTP
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


logger = logging.getLogger("job_hunter")
