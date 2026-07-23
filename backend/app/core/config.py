from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Resolve from backend/.env regardless of the shell's current directory.
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "E-Commerce Management System"
    API_V1_STR: str = "/api/v1"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_DATABASE_URL: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "product-images"
    PRODUCT_IMAGE_STORAGE: str = "auto"
    DATABASE_URL: str = ""
    INITIALIZE_DATABASE_ON_STARTUP: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        """Accept a JSON-encoded list, a comma-separated string, or a plain list."""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            value = value.strip()
            # Try to parse as JSON first (handles '["...", "..."]')
            if value.startswith("["):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("PRODUCT_IMAGE_STORAGE")
    @classmethod
    def validate_product_image_storage(cls, value: str) -> str:
        mode = value.strip().lower()
        if mode not in {"auto", "local", "supabase"}:
            raise ValueError("PRODUCT_IMAGE_STORAGE must be auto, local, or supabase")
        return mode

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
