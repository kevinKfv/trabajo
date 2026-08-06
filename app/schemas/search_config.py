from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SearchConfigBase(BaseModel):
    name: str
    keywords: List[str]
    exclude_keywords: List[str] = []
    sources: List[str] = ["linkedin", "bumeran", "computrabajo"]
    location: Optional[str] = None
    remote_only: bool = False
    seniorities: List[str] = []
    min_salary: Optional[float] = None
    currency: str = "ARS"
    frequency_hours: int = 2
    date_filter: str = "all"
    target_cv_version_id: Optional[int] = None
    is_active: bool = True


class SearchConfigCreate(SearchConfigBase):
    pass


class SearchConfigUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    location: Optional[str] = None
    remote_only: Optional[bool] = None
    seniorities: Optional[List[str]] = None
    min_salary: Optional[float] = None
    currency: Optional[str] = None
    frequency_hours: Optional[int] = None
    date_filter: Optional[str] = None
    target_cv_version_id: Optional[int] = None
    is_active: Optional[bool] = None


class SearchConfigResponse(SearchConfigBase):
    id: int
    last_run_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
