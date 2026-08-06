from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.application_log import ApplicationStatus


class AutoApplyRequest(BaseModel):
    dry_run: bool = False
    custom_message: Optional[str] = None


class BatchAutoApplyRequest(BaseModel):
    min_ai_score: float = 80.0
    dry_run: bool = False
    max_applications: int = 10


class ApplicationLogResponse(BaseModel):
    id: int
    job_id: int
    job_title: str
    company: str
    source: str
    status: ApplicationStatus
    applied_at: datetime
    screenshot_path: Optional[str] = None
    notes: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
