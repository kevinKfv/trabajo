from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobUpdate, JobStatsResponse
from app.schemas.filter import JobFilter
from app.core.logging import logger


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, job_id: int) -> Optional[Job]:
        """Obtiene un trabajo por su ID primario."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> Optional[Job]:
        """Busca si una oferta laboral ya existe en la BD por su URL."""
        result = await self.db.execute(select(Job).where(Job.url == url))
        return result.scalar_one_or_none()

    async def get_by_title_and_company(self, title: str, company: str) -> Optional[Job]:
        """Busca si existe una oferta con el mismo título y empresa."""
        result = await self.db.execute(
            select(Job).where(
                and_(
                    func.lower(Job.title) == title.lower(),
                    func.lower(Job.company) == company.lower()
                )
            )
        )
        return result.scalar_one_or_none()

    async def save_job(self, job_in: JobCreate) -> Tuple[Optional[Job], bool]:
        """Guarda un trabajo eliminando duplicados. Retorna (Job, creado: bool)."""
        # 1. Verificar duplicado por URL
        existing_job = await self.get_by_url(job_in.url)
        if existing_job:
            logger.debug(f"Job omitido por URL duplicada: {job_in.url}")
            return existing_job, False

        # 2. Verificar duplicado por Título + Empresa
        existing_job = await self.get_by_title_and_company(job_in.title, job_in.company)
        if existing_job:
            logger.debug(f"Job omitido por Título y Empresa duplicada: {job_in.title} @ {job_in.company}")
            return existing_job, False

        # 3. Crear nuevo registro
        new_job = Job(
            title=job_in.title,
            company=job_in.company,
            location=job_in.location,
            salary=job_in.salary,
            remote=job_in.remote,
            seniority=job_in.seniority,
            description=job_in.description,
            technologies=job_in.technologies,
            url=job_in.url,
            published_date=job_in.published_date,
            source=job_in.source,
            status=JobStatus.NEW
        )

        self.db.add(new_job)
        await self.db.commit()
        await self.db.refresh(new_job)
        return new_job, True

    async def bulk_save_jobs(self, jobs_in: List[JobCreate]) -> Tuple[int, int]:
        """Guarda un lote de trabajos omitiendo duplicados. Retorna (total_recibidos, total_creados)."""
        created_count = 0
        for job_in in jobs_in:
            _, created = await self.save_job(job_in)
            if created:
                created_count += 1
        return len(jobs_in), created_count

    async def filter_jobs(self, filters: JobFilter) -> Tuple[List[Job], int]:
        """Aplica filtros, paginación y ordenamiento sobre las ofertas laborales."""
        query = select(Job)
        count_query = select(func.count(Job.id))

        conditions = []

        if filters.remote is not None:
            conditions.append(Job.remote == filters.remote)

        if filters.location:
            conditions.append(Job.location.ilike(f"%{filters.location}%"))

        if filters.company:
            conditions.append(Job.company.ilike(f"%{filters.company}%"))

        if filters.seniority:
            conditions.append(Job.seniority.ilike(f"%{filters.seniority}%"))

        if filters.source:
            conditions.append(Job.source.ilike(f"%{filters.source}%"))

        if filters.status:
            conditions.append(Job.status == filters.status)

        if filters.min_ai_score is not None:
            conditions.append(Job.ai_score >= filters.min_ai_score)

        if filters.date_filter == "today":
            from datetime import datetime, timedelta, timezone
            conditions.append(Job.created_at >= datetime.now(timezone.utc) - timedelta(days=1))
        elif filters.date_filter == "week":
            from datetime import datetime, timedelta, timezone
            conditions.append(Job.created_at >= datetime.now(timezone.utc) - timedelta(days=7))

        if filters.search_query:
            search = f"%{filters.search_query}%"
            conditions.append(
                or_(
                    Job.title.ilike(search),
                    Job.company.ilike(search),
                    Job.description.ilike(search)
                )
            )

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Total de resultados para paginación
        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one() or 0

        # Paginación y ordenamiento por fecha de creación descendente
        offset = (filters.page - 1) * filters.limit
        query = query.order_by(Job.id.desc()).offset(offset).limit(filters.limit)

        result = await self.db.execute(query)
        jobs = result.scalars().all()

        return list(jobs), total

    async def get_stats(self) -> JobStatsResponse:
        """Calcula estadísticas generales de las ofertas almacenadas."""
        total_res = await self.db.execute(select(func.count(Job.id)))
        total_jobs = total_res.scalar_one() or 0

        remote_res = await self.db.execute(select(func.count(Job.id)).where(Job.remote == True))
        remote_jobs_count = remote_res.scalar_one() or 0

        high_match_res = await self.db.execute(select(func.count(Job.id)).where(Job.ai_score >= 80.0))
        high_match_jobs_count = high_match_res.scalar_one() or 0

        # Conteo por fuente
        source_res = await self.db.execute(select(Job.source, func.count(Job.id)).group_by(Job.source))
        jobs_by_source = {source: count for source, count in source_res.all()}

        # Conteo por estado
        status_res = await self.db.execute(select(Job.status, func.count(Job.id)).group_by(Job.status))
        jobs_by_status = {status.value if hasattr(status, 'value') else str(status): count for status, count in status_res.all()}

        return JobStatsResponse(
            total_jobs=total_jobs,
            jobs_by_source=jobs_by_source,
            jobs_by_status=jobs_by_status,
            remote_jobs_count=remote_jobs_count,
            high_match_jobs_count=high_match_jobs_count
        )
