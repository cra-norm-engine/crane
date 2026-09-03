# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

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
    secret_key: str = Field(alias="BACKEND_SECRET_KEY")
    audit_hmac_key: str = Field(default="", alias="BACKEND_AUDIT_HMAC_KEY")

    # --- Initial admin bootstrap ---
    # Email of the seeded admin account.
    admin_email: str = Field(default="admin@example.com", alias="BACKEND_ADMIN_EMAIL")
    # Password for the seeded admin. If left blank: development builds fall back to
    # the well-known "admin1234" (convenience), while non-development builds generate
    # a random password and log it once — so no known default credentials ever ship
    # to production. The account always starts with must_change_password=True.
    admin_password: str = Field(default="", alias="BACKEND_ADMIN_PASSWORD")

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_not_be_default(cls, v: str) -> str:
        # Refuse to start with known-insecure defaults that exist in the repository.
        _INSECURE_DEFAULTS = {"change-me", "change-me-in-production", "secret", ""}
        if v in _INSECURE_DEFAULTS or len(v) < 32:
            raise ValueError(
                "BACKEND_SECRET_KEY must be a cryptographically random value "
                "(minimum 32 characters). Generate one with: "
                "python3 -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    access_token_expire_minutes: int = Field(
        default=60,
        alias="BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    refresh_token_expire_days: int = Field(
        default=7,
        alias="BACKEND_REFRESH_TOKEN_EXPIRE_DAYS",
    )

    # --- Auth brute-force protection ---
    # Failed logins are counted over a rolling window; once a threshold is hit,
    # further login attempts for that account/IP are rejected with HTTP 429 until
    # older failures age out of the window. Set a threshold to 0 to disable it.
    login_failure_window_minutes: int = Field(
        default=15,
        alias="BACKEND_LOGIN_FAILURE_WINDOW_MINUTES",
    )
    login_max_failures_per_account: int = Field(
        default=10,
        alias="BACKEND_LOGIN_MAX_FAILURES_PER_ACCOUNT",
    )
    login_max_failures_per_ip: int = Field(
        default=50,
        alias="BACKEND_LOGIN_MAX_FAILURES_PER_IP",
    )

    # --- CORS ---
    cors_origins: List[str] | str = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"],
        alias="BACKEND_CORS_ORIGINS",
    )

    # --- Logging ---
    log_level: str = Field(default="INFO", alias="BACKEND_LOG_LEVEL")

    # --- Automated vulnerability scanning ---
    # Recurring re-scan of stored SBOMs so newly-published CVEs surface without a
    # manual click. Disabled by default so environments without outbound internet
    # (e.g. the offline sandbox) are unaffected; scans still degrade gracefully when
    # enabled but a source is unreachable.
    scan_scheduler_enabled: bool = Field(default=False, alias="BACKEND_SCAN_SCHEDULER_ENABLED")
    # Cron expression (5-field: min hour day month day-of-week). Default 02:00 daily.
    scan_schedule_cron: str = Field(default="0 2 * * *", alias="BACKEND_SCAN_SCHEDULE_CRON")
    # Automatically scan an SBOM in the background right after it is uploaded.
    scan_on_upload: bool = Field(default=True, alias="BACKEND_SCAN_ON_UPLOAD")

    # --- Task notifications ---
    task_due_warning_days: int = Field(default=3, ge=0, alias="BACKEND_TASK_DUE_WARNING_DAYS")

    # --- Jira Cloud integration ---
    jira_oauth_client_id: str = Field(default="", alias="BACKEND_JIRA_OAUTH_CLIENT_ID")
    jira_oauth_client_secret: str = Field(default="", alias="BACKEND_JIRA_OAUTH_CLIENT_SECRET")
    jira_oauth_redirect_uri: str = Field(default="http://localhost:8000/api/v1/jira/oauth/callback", alias="BACKEND_JIRA_OAUTH_REDIRECT_URI")
    jira_frontend_settings_url: str = Field(default="http://localhost:5173/settings#jira", alias="BACKEND_JIRA_FRONTEND_SETTINGS_URL")
    jira_forge_app_id: str = Field(default="", alias="BACKEND_JIRA_FORGE_APP_ID")

    # --- Artifact Storage ---
    artifact_upload_dir: str = Field(
        default="/workspace/backend/uploads/artifacts",
        alias="BACKEND_ARTIFACT_UPLOAD_DIR",
    )
    # CRA Art. 31 — minimum retention for technical documentation / evidence.
    # Used to set each artifact's retention_until = created date + this many years.
    artifact_retention_years: int = Field(default=10, alias="BACKEND_ARTIFACT_RETENTION_YEARS")

    # --- LDAP ---
    ldap_enabled: bool = Field(default=False, alias="LDAP_ENABLED")
    ldap_server_url: str = Field(default="ldap://localhost:389", alias="LDAP_SERVER_URL")
    ldap_bind_dn: str = Field(default="", alias="LDAP_BIND_DN")
    ldap_bind_password: str = Field(default="", alias="LDAP_BIND_PASSWORD")
    ldap_base_dn: str = Field(default="", alias="LDAP_BASE_DN")
    ldap_user_filter: str = Field(default="(mail={email})", alias="LDAP_USER_FILTER")
    ldap_attr_email: str = Field(default="mail", alias="LDAP_ATTR_EMAIL")
    ldap_attr_full_name: str = Field(default="displayName", alias="LDAP_ATTR_FULL_NAME")
    ldap_use_tls: bool = Field(default=False, alias="LDAP_USE_TLS")
    ldap_connection_timeout: int = Field(default=5, alias="LDAP_CONNECTION_TIMEOUT")

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
