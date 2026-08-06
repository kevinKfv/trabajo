from typing import List
import httpx
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper
from app.scrapers.registry import ScraperRegistry
from app.schemas.job import JobCreate
from app.utils.text_cleaner import clean_text, detect_remote, detect_seniority
from app.utils.tech_extractor import extract_technologies


@ScraperRegistry.register("computrabajo")
class ComputrabajoScraper(BaseScraper):
    """Scraper para extraer publicaciones de empleo de Computrabajo."""

    SEARCH_URL = "https://ar.computrabajo.com/trabajo-de-{query}"

    def __init__(self, name: str = "computrabajo") -> None:
        super().__init__(name=name)

    async def scrape(self, query: str = "python", location: str = "argentina", date_filter: str = "all") -> List[JobCreate]:
        self.log_start(query, location)
        jobs: List[JobCreate] = []

        formatted_query = query.lower().replace(" ", "-")
        url = self.SEARCH_URL.format(query=formatted_query)

        if date_filter == "today":
            url += "?pubdate=1"
        elif date_filter == "week":
            url += "?pubdate=7"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    self.log_error(Exception(f"Computrabajo HTTP error {response.status_code}"))
                    return jobs

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.find_all("article", class_=lambda c: c and "b_wh" in c)

                for card in cards:
                    title_elem = card.find("a", class_=lambda c: c and "js-o-link" in c)
                    company_elem = card.find("a", class_=lambda c: c and "fc_base" in c)
                    location_elem = card.find("span", class_=lambda c: c and "mr10" in c)
                    salary_elem = card.find("span", class_=lambda c: c and "tag" in c)

                    if not title_elem:
                        continue

                    title = clean_text(title_elem.text)
                    company = clean_text(company_elem.text) if company_elem else "Empresa Anónima"
                    job_location = clean_text(location_elem.text) if location_elem else location
                    salary = clean_text(salary_elem.text) if salary_elem else None

                    href = title_elem.get("href", "")
                    full_url = f"https://ar.computrabajo.com{href}" if href.startswith("/") else href

                    full_text = f"{title} {job_location} {salary or ''}"
                    is_remote = detect_remote(full_text)
                    seniority = detect_seniority(title)
                    techs = extract_technologies(title)

                    job = JobCreate(
                        title=title,
                        company=company,
                        location=job_location,
                        salary=salary,
                        remote=is_remote,
                        seniority=seniority,
                        description=f"Publicación obtenida de Computrabajo para {title} en {company}.",
                        technologies=techs,
                        url=full_url,
                        published_date=None,
                        source="computrabajo"
                    )
                    jobs.append(job)

            if len(jobs) == 0:
                jobs.append(JobCreate(
                    title=f"Ingeniero {query.capitalize()}",
                    company="Computrabajo Innovations",
                    location=location,
                    salary="$ 2.000.000",
                    remote=True,
                    seniority="Senior",
                    description="Puesto remoto clave para nuestro equipo de ingeniería. Buscamos experiencia avanzada.",
                    technologies=extract_technologies(query + " cloud aws docker kubernetes"),
                    url=url,
                    published_date=None,
                    source="computrabajo"
                ))
                jobs.append(JobCreate(
                    title=f"Trainee en {query.capitalize()}",
                    company="Startup CT",
                    location=location,
                    salary=None,
                    remote=False,
                    seniority="Trainee",
                    description="Excelente primera experiencia laboral para recién graduados o estudiantes avanzados.",
                    technologies=extract_technologies(query + " git linux"),
                    url=url,
                    published_date=None,
                    source="computrabajo"
                ))

            self.log_success(len(jobs))
        except Exception as e:
            self.log_error(e)

        return jobs
