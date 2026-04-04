from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    project_name: str = Field(default="CRA Compliance Tool", alias="BACKEND_PROJECT_NAME")
    environment: str = Field(default="development", alias="BACKEND_ENVIRONMENT")
    debug: bool = Field(default=True, alias="BACKEND_DEBUG")

    # --- Server ---
    api_prefix: str = Field(default="/api/v1", alias="BACKEND_API_PREFIX")
    host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    port: int = Field(default=8000, alias="BACKEND_PORT")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@postgres:5432/cra_compliance",
        alias="BACKEND_DATABASE_URL",
    )

    # --- Security ---
    secret_key: str = Field(default="change-me", alias="BACKEND_SECRET_KEY")

    access_token_expire_minutes: int = Field(
        default=60,
        alias="BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    refresh_token_expire_days: int = Field(
        default=7,
        alias="BACKEND_REFRESH_TOKEN_EXPIRE_DAYS",
    )

    # --- CORS ---
    cors_origins: List[str] | str = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="BACKEND_CORS_ORIGINS",
    )

    # --- Logging ---
    log_level: str = Field(default="INFO", alias="BACKEND_LOG_LEVEL")

    # --- Artifact Storage ---
    artifact_upload_dir: str = Field(
        default="/workspace/backend/uploads/artifacts",
        alias="BACKEND_ARTIFACT_UPLOAD_DIR",
    )

    # --- Validators ---
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
