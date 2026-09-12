from __future__ import annotations

from uuid import UUID
from urllib.parse import urlsplit

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, SecretStr, field_validator


class ConnectionCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    server_url: str = Field(min_length=1, max_length=2000)
    api_key: SecretStr = Field(min_length=1, max_length=1000)

    @field_validator("server_url")
    @classmethod
    def server_origin(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        url = urlsplit(value)
        if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("Enter the Dependency-Track backend URL, without credentials or query parameters")
        if url.path.endswith("/api/v1"):
            value = value[:-7]
        return value


class ConnectionCreate(ConnectionCredentials):
    project_id: UUID
    sbom_record_id: UUID
    automatic_sync: bool = False


class ConnectionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    automatic_sync: bool


class ProjectOption(BaseModel):
    uuid: UUID
    name: str
    version: str | None = None


class SbomOption(BaseModel):
    id: UUID
    label: str


class ConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    server_url: str
    project_id: UUID
    project_name: str
    sbom_record_id: UUID
    automatic_sync: bool
    last_attempt_at: AwareDatetime | None
    last_synced_at: AwareDatetime | None
    last_error: str | None
    last_result: dict | None
