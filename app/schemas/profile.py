from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr


class UserProfileBase(BaseModel):
    full_name: str = "Candidato"
    email: str = ""
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    cv_skills: List[str] = []
    cv_text: Optional[str] = None
    cover_letter_template: Optional[str] = None


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: int
    cv_file_path: Optional[str] = None
    cv_filename: Optional[str] = None
    cv_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
