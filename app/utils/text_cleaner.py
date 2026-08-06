import re
from typing import Optional
from bs4 import BeautifulSoup


def clean_html(html_content: str) -> str:
    """Remueve etiquetas HTML y limpia espacios innecesarios."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_text(text: Optional[str]) -> str:
    """Limpia espacios extras y saltos de línea redundantes."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def detect_remote(text: str) -> bool:
    """Detecta si un texto menciona trabajo remoto, home office o híbrido."""
    if not text:
        return False
    keywords = ["remoto", "remote", "home office", "teletrabajo", "híbrido", "hibrido", "work from home"]
    pattern = re.compile(r"\b(" + "|".join(keywords) + r")\b", re.IGNORECASE)
    return bool(pattern.search(text))


def detect_seniority(text: str) -> Optional[str]:
    """Detecta el nivel de seniority en un título o descripción."""
    if not text:
        return None
    lower_text = text.lower()
    if "trainee" in lower_text:
        return "Trainee"
    if "junior" in lower_text or "jr" in lower_text:
        return "Junior"
    if "lead" in lower_text or "principal" in lower_text or "tech lead" in lower_text:
        return "Lead / Principal"
    if "senior" in lower_text or "sr" in lower_text:
        return "Senior"
    if "semi-senior" in lower_text or "semi senior" in lower_text or "ssr" in lower_text:
        return "Semi-Senior"
    return "No especificado"
