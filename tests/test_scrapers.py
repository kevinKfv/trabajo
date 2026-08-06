import pytest
from app.scrapers.registry import ScraperRegistry
from app.utils.text_cleaner import clean_html, detect_remote, detect_seniority
from app.utils.tech_extractor import extract_technologies
import app.scrapers  # Asegura la carga e importación de scrapers


def test_scraper_registry():
    """Verifica que los 3 scrapers requeridos estén registrados correctamente."""
    available = ScraperRegistry.list_scrapers()
    assert "linkedin" in available
    assert "bumeran" in available
    assert "computrabajo" in available


def test_tech_extractor():
    """Verifica que la detección de tecnologías funcione correctamente."""
    sample_text = "Buscamos Desarrollador Senior Python con FastAPI, Docker, PostgreSQL y React para trabajo remoto."
    techs = extract_technologies(sample_text)

    assert "Python" in techs
    assert "FastAPI" in techs
    assert "Docker" in techs
    assert "PostgreSQL" in techs
    assert "React" in techs


def test_text_cleaner_and_remote_detection():
    """Verifica la limpieza de HTML y detección de trabajo remoto/seniority."""
    raw_html = "<div class='job'><h2>Senior Python Developer</h2><p>Trabajo 100% Home Office</p></div>"
    cleaned = clean_html(raw_html)

    assert "Senior Python Developer" in cleaned
    assert detect_remote(cleaned) is True
    assert detect_seniority("Senior Python Developer") == "Senior"


@pytest.mark.asyncio
async def test_scrapers_instantiation():
    """Verifica que cada scraper se instancie sin problemas y tenga la firma correcta."""
    for scraper_name in ["linkedin", "bumeran", "computrabajo"]:
        scraper = ScraperRegistry.get_scraper(scraper_name)
        assert scraper.name == scraper_name
        assert hasattr(scraper, "scrape")
