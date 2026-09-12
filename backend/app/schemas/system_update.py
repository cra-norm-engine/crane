# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


UpdatePolicy = Literal["manual", "security", "all"]


class UpdateArtifact(BaseModel):
    image: str = Field(min_length=1)
    digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @property
    def immutable_reference(self) -> str:
        return f"{self.image}@{self.digest}"


class UpdateManifest(BaseModel):
    schema_version: int = Field(default=1, ge=1, le=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
    channel: Literal["stable", "preview"] = "stable"
    update_type: Literal["security", "maintenance", "feature"]
    severity: Literal["none", "low", "medium", "high", "critical"] = "none"
    published_at: datetime
    expires_at: datetime
    minimum_upgrade_version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
    database_revision: str = Field(min_length=1, max_length=64)
    postgres_major_versions: list[int] = Field(min_length=1)
    automatic_update_allowed: bool = False
    rollback_mode: Literal["image-only", "database-restore"] = "database-restore"
    backend: UpdateArtifact
    frontend: UpdateArtifact
    advisory_url: HttpUrl | None = None
    release_notes_url: HttpUrl
    download_url: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_security_release(self) -> "UpdateManifest":
        if self.update_type == "security" and self.severity == "none":
            raise ValueError("security updates require a severity")
        if self.expires_at <= self.published_at:
            raise ValueError("expires_at must be after published_at")
        return self


class SystemUpdatePolicy(BaseModel):
    policy: UpdatePolicy
    channel: Literal["stable", "preview"] = "stable"
    maintenance_day: int = Field(ge=0, le=6)
    maintenance_hour_utc: int = Field(ge=0, le=23)
    postponed_until: datetime | None = None

    @field_validator("postponed_until")
    @classmethod
    def postponed_until_must_include_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("postponed_until must include a timezone")
        return value


class SystemUpdateStatus(BaseModel):
    installed_version: str
    configured: bool
    update_checks_enabled: bool
    policy: SystemUpdatePolicy
    update_available: bool = False
    automatic_update_eligible: bool = False
    manifest: UpdateManifest | None = None
    last_checked_at: datetime | None = None
    last_error: str | None = None
    last_operation: dict[str, object] | None = None
    manual_command: str = "./crane-update apply"
