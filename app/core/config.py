from typing import Literal
from pydantic import computed_field, Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    PROJECT_NAME: str = "Job Hunter AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # PostgreSQL (con soporte nativo para Railway y otros PAAS)
    POSTGRES_SERVER: str = Field(default="localhost", validation_alias=AliasChoices('POSTGRES_SERVER', 'PGHOST', 'POSTGRES_HOST'))
    POSTGRES_PORT: int = Field(default=5432, validation_alias=AliasChoices('POSTGRES_PORT', 'PGPORT'))
    POSTGRES_USER: str = Field(default="postgres", validation_alias=AliasChoices('POSTGRES_USER', 'PGUSER'))
    POSTGRES_PASSWORD: str = Field(default="postgres", validation_alias=AliasChoices('POSTGRES_PASSWORD', 'PGPASSWORD'))
    POSTGRES_DB: str = Field(default="job_hunter_db", validation_alias=AliasChoices('POSTGRES_DB', 'PGDATABASE'))

    @computed_field
    @property
    def ASYNC_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # AI Configuration
    AI_PROVIDER: Literal["openai", "ollama", "groq", "anthropic"] = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Notifications
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    NOTIFICATION_EMAIL_TO: str = ""

    # Scheduler
    SCRAPE_INTERVAL_HOURS: int = 6


settings = Settings()
