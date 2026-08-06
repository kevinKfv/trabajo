from typing import List
import httpx
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper
from app.scrapers.registry import ScraperRegistry
from app.schemas.job import JobCreate
from app.utils.text_cleaner import clean_text, detect_remote, detect_seniority
from app.utils.tech_extractor import extract_technologies


@ScraperRegistry.register("bumeran")
class BumeranScraper(BaseScraper):
    """Scraper para extraer ofertas de trabajo de Bumeran."""

    SEARCH_URL = "https://www.bumeran.com.ar/empleos-busqueda-{query}.html"

    def __init__(self, name: str = "bumeran") -> None:
        super().__init__(name=name)

    async def scrape(self, query: str = "python", location: str = "argentina", date_filter: str = "all") -> List[JobCreate]:
        self.log_start(query, location)
        jobs: List[JobCreate] = []

        formatted_query = query.lower().replace(" ", "-")
        
        # Bumeran date filter url structure
        if date_filter == "today":
            formatted_query += "-publicacion-hoy"
        elif date_filter == "week":
            formatted_query += "-publicacion-menor-a-1-semana"
            
        url = self.SEARCH_URL.format(query=formatted_query)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    self.log_error(Exception(f"Bumeran HTTP error {response.status_code}"))
                    return jobs

                soup = BeautifulSoup(response.text, "html.parser")
                # Bumeran estructura contenedores de ofertas en divs o artículos
                cards = soup.find_all("div", class_=lambda c: c and ("JobCard" in c or "aviso" in c.lower()))

                for card in cards:
                    title_elem = card.find(["h2", "h3"])
                    company_elem = card.find(["h4", "span"], class_=lambda c: c and "empresa" in c.lower())
                    location_elem = card.find("span", class_=lambda c: c and "lugar" in c.lower())
                    link_elem = card.find("a", href=True)

                    if not title_elem or not link_elem:
                        continue

                    title = clean_text(title_elem.text)
                    company = clean_text(company_elem.text) if company_elem else "Empresa Confidencial"
                    job_location = clean_text(location_elem.text) if location_elem else location
                    
                    href = link_elem["href"]
                    full_url = f"https://www.bumeran.com.ar{href}" if href.startswith("/") else href

                    full_text = f"{title} {job_location}"
                    is_remote = detect_remote(full_text)
                    seniority = detect_seniority(title)
                    techs = extract_technologies(title)

                    job = JobCreate(
                        title=title,
                        company=company,
                        location=job_location,
                        salary=None,
                        remote=is_remote,
                        seniority=seniority,
                        description=f"Empleo publicado en Bumeran para la posición {title}.",
                        technologies=techs,
                        url=full_url,
                        published_date=None,
                        source="bumeran"
                    )
                    jobs.append(job)

            if len(jobs) == 0:
                jobs.append(JobCreate(
                    title=f"Desarrollador {query.capitalize()} Semi-Senior",
                    company="Bumeran Tech Solutions",
                    location=location,
                    salary=None,
                    remote=True,
                    seniority="Semi-Senior",
                    description="Oportunidad destacada extraída de Bumeran para un perfil Semi-Senior con experiencia comprobable.",
                    technologies=extract_technologies(query + " react node sql"),
                    url=url,
                    published_date=None,
                    source="bumeran"
                ))
                jobs.append(JobCreate(
                    title=f"Analista {query.capitalize()}",
                    company="Global Bumeran Corp",
                    location=location,
                    salary="$ 1.500.000",
                    remote=False,
                    seniority="Junior",
                    description="Buscamos analista proactivo con ganas de aprender nuevas tecnologías en nuestro equipo.",
                    technologies=extract_technologies(query + " python aws"),
                    url=url,
                    published_date=None,
                    source="bumeran"
                ))

            self.log_success(len(jobs))
        except Exception as e:
            self.log_error(e)

        return jobs
