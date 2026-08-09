from typing import Dict, Any, List
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.job import Job, JobStatus
from app.models.application_stage import ApplicationStage, CRMStage


class AnalyticsService:
    """Servicio de analítica y estadísticas avanzadas para el Dashboard."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_metrics(self, device_id: str = "global") -> Dict[str, Any]:
        """Calcula todas las métricas cuantitativas, estadísticas y desglose de tecnologías para un dispositivo."""
        
        # Total jobs
        total_res = await self.db.execute(select(func.count(Job.id)).where(Job.device_id == device_id))
        total_jobs = total_res.scalar_one() or 0
        
        if total_jobs == 0:
            return {
                "total_jobs": 0, "status_distribution": {}, "stage_distribution": {},
                "avg_ai_score": 0.0, "top_technologies": {}, "sources_distribution": {},
                "remote_jobs_count": 0, "remote_percentage": 0.0,
                "high_match_count": 0, "high_match_jobs_count": 0
            }

        # Status distribution
        status_res = await self.db.execute(select(Job.status, func.count(Job.id)).where(Job.device_id == device_id).group_by(Job.status))
        status_distribution = {status.value if hasattr(status, 'value') else str(status): count for status, count in status_res.all()}

        # Avg AI Score
        avg_score_res = await self.db.execute(select(func.avg(Job.ai_score)).where(Job.ai_score.isnot(None), Job.device_id == device_id))
        avg_score_val = avg_score_res.scalar_one()
        avg_score = round(avg_score_val, 1) if avg_score_val is not None else 0.0

        # Remote jobs
        remote_res = await self.db.execute(select(func.count(Job.id)).where(Job.remote == True, Job.device_id == device_id))
        remote_jobs_count = remote_res.scalar_one() or 0

        # High match jobs
        high_res = await self.db.execute(select(func.count(Job.id)).where(Job.ai_score >= 80.0, Job.device_id == device_id))
        high_match_count = high_res.scalar_one() or 0

        # Source distribution
        source_res = await self.db.execute(select(Job.source, func.count(Job.id)).where(Job.device_id == device_id).group_by(Job.source))
        sources_distribution = {str(source).upper(): count for source, count in source_res.all() if source}

        # Top 10 Technologies (fetch just the column to avoid loading full models)
        techs_res = await self.db.execute(select(Job.technologies).where(Job.technologies.isnot(None), Job.device_id == device_id))
        all_techs = []
        for (techs_list,) in techs_res.all():
            if techs_list and isinstance(techs_list, list):
                all_techs.extend(techs_list)
        top_techs = dict(Counter(all_techs).most_common(10))

        # CRM Stages
        stages_res = await self.db.execute(
            select(ApplicationStage.stage, func.count(ApplicationStage.id))
            .join(Job, Job.id == ApplicationStage.job_id)
            .where(Job.device_id == device_id)
            .group_by(ApplicationStage.stage)
        )
        stage_counts = {stage.value if hasattr(stage, 'value') else str(stage): count for stage, count in stages_res.all()}

        return {
            "total_jobs": total_jobs,
            "status_distribution": status_distribution,
            "stage_distribution": stage_counts,
            "avg_ai_score": avg_score,
            "top_technologies": top_techs,
            "sources_distribution": sources_distribution,
            "remote_jobs_count": remote_jobs_count,
            "remote_percentage": round(remote_jobs_count / total_jobs * 100, 1) if total_jobs > 0 else 0.0,
            "high_match_count": high_match_count,
            "high_match_jobs_count": high_match_count
        }
