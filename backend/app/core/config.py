from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "E-Commerce Management System"
    API_V1_STR: str = "/api/v1"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_DATABASE_URL: Optional[str] = None
    DATABASE_URL: str = ""
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        # Priority: DATABASE_URL (explicit) > SUPABASE_DATABASE_URL > local fallback
        if not self.DATABASE_URL:
            if self.SUPABASE_DATABASE_URL:
                self.DATABASE_URL = self.SUPABASE_DATABASE_URL
            else:
                # Local PostgreSQL fallback — only used in dev without Supabase config
                self.DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/ecommerce_db"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
