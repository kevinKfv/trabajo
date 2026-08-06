import re
from typing import List, Set

# Diccionario de tecnologías populares y patrones de búsqueda
COMMON_TECHNOLOGIES = [
    "Python", "FastAPI", "Django", "Flask", "JavaScript", "TypeScript", "React", "Vue", "Angular",
    "Node.js", "Express", "Next.js", "Docker", "Kubernetes", "PostgreSQL", "MySQL", "MongoDB",
    "Redis", "Elasticsearch", "AWS", "GCP", "Azure", "Git", "GitHub", "GitLab", "CI/CD",
    "Playwright", "Selenium", "Scrapy", "BeautifulSoup", "Pandas", "NumPy", "PyTorch", "TensorFlow",
    "GraphQL", "REST", "gRPC", "Kafka", "RabbitMQ", "Celery", "Airflow", "Linux", "Bash", "Java",
    "C#", ".NET", "Go", "Golang", "Rust", "PHP", "Laravel", "Ruby", "Rails", "HTML", "CSS", "Tailwind"
]


def extract_technologies(text: str) -> List[str]:
    """Extrae palabras clave de tecnologías presentes en una descripción o título de trabajo."""
    if not text:
        return []

    found_techs: Set[str] = set()
    text_lower = text.lower()

    for tech in COMMON_TECHNOLOGIES:
        # Escapar caracteres especiales para la expresión regular
        tech_pattern = re.escape(tech.lower())
        
        # Coincidencia exacta de palabras completas
        pattern = r"(?:\b|\W)" + tech_pattern + r"(?:\b|\W)"
        if re.search(pattern, text_lower):
            found_techs.add(tech)

    return sorted(list(found_techs))
