from typing import List
import httpx
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper
from app.scrapers.registry import ScraperRegistry
from app.schemas.job import JobCreate
from app.utils.text_cleaner import clean_text, detect_remote, detect_seniority
from app.utils.tech_extractor import extract_technologies


@ScraperRegistry.register("linkedin")
class LinkedInScraper(BaseScraper):
    """Scraper para extraer publicaciones de empleo públicas de LinkedIn."""

    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    def __init__(self, name: str = "linkedin") -> None:
        super().__init__(name=name)

    async def scrape(self, query: str = "python", location: str = "remote", date_filter: str = "all") -> List[JobCreate]:
        self.log_start(query, location)
        jobs: List[JobCreate] = []

        params = {
            "keywords": query,
            "location": location,
            "start": 0
        }
        
        if date_filter == "today":
            params["f_TPR"] = "r86400"
        elif date_filter == "week":
            params["f_TPR"] = "r604800"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(self.BASE_URL, params=params, headers=headers)
                if response.status_code != 200:
                    self.log_error(Exception(f"LinkedIn HTTP error {response.status_code}"))
                    return jobs

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.find_all("li")

                for card in cards:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    location_elem = card.find("span", class_="job-search-card__location")
                    link_elem = card.find("a", class_="base-card__full-link")
                    time_elem = card.find("time")

                    if not title_elem or not link_elem:
                        continue

                    title = clean_text(title_elem.text)
                    company = clean_text(company_elem.text) if company_elem else "Empresa No Especificada"
                    job_location = clean_text(location_elem.text) if location_elem else location
                    url = link_elem.get("href", "").split("?")[0]
                    date_published = time_elem.get("datetime") if time_elem else None

                    # Texto base para análisis
                    full_text = f"{title} {job_location}"
                    is_remote = detect_remote(full_text) or "remote" in location.lower()
                    seniority = detect_seniority(title)
                    techs = extract_technologies(title)

                    job = JobCreate(
                        title=title,
                        company=company,
                        location=job_location,
                        salary=None,
                        remote=is_remote,
                        seniority=seniority,
                        description=f"Publicación laboral extraída de LinkedIn para el rol {title} en {company}.",
                        technologies=techs,
                        url=url,
                        published_date=date_published,
                        source="linkedin"
                    )
                    jobs.append(job)

            self.log_success(len(jobs))
        except Exception as e:
            self.log_error(e)

        return jobs
