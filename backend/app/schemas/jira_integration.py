from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JiraConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    cloud_id: str
    site_url: str
    site_name: str
    project_key: str | None
    issue_type: str
    status_mapping_json: dict
    priority_mapping_json: dict
    forge_installation_id: str | None
    is_active: bool
    last_error: str | None
    created_at: datetime


class JiraConnectionUpdate(BaseModel):
    project_key: str = Field(min_length=1, max_length=50)
    issue_type: str = Field(default="Task", min_length=1, max_length=100)
    status_mapping_json: dict[str, str] = Field(default_factory=dict)
    priority_mapping_json: dict[str, str] = Field(default_factory=dict)


class JiraUserMappingWrite(BaseModel):
    crane_user_id: UUID
    jira_account_id: str = Field(min_length=1, max_length=255)
    jira_display_name: str | None = Field(default=None, max_length=255)


class JiraUserMappingRead(JiraUserMappingWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class JiraTaskLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    manual_task_id: UUID
    issue_id: str
    issue_key: str
    issue_url: str
    sync_status: str
    last_synced_at: datetime | None
    last_error: str | None


class JiraSyncRequest(BaseModel):
    direction: Literal["push", "pull"] = "push"


class JiraBoardSyncRead(BaseModel):
    exported: int = 0
    synchronized: int = 0
    skipped: int = 0
    failed: int = 0


class JiraOAuthStartRead(BaseModel):
    authorization_url: str


class JiraForgeTaskRead(BaseModel):
    linked: bool
    issue_key: str | None = None
    task_id: UUID | None = None
    title: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: str | None = None
    product_name: str | None = None
    release_version: str | None = None
    crane_url: str | None = None
    evidence_count: int = 0
    sync_status: str | None = None
