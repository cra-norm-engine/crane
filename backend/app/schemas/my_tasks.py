# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ManualTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    due_date: date | None = None
    assigned_to_user_id: UUID | None = None
    product_id: UUID | None = None
    product_release_id: UUID | None = None
    priority: Literal["low", "medium", "high"] = "medium"


class ManualTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    due_date: date | None = None
    assigned_to_user_id: UUID | None = None
    product_id: UUID | None = None
    product_release_id: UUID | None = None
    priority: Literal["low", "medium", "high"] | None = None


class ManualTaskStatusUpdate(BaseModel):
    status: str


class ManualTaskComplete(BaseModel):
    completion_note: str | None = Field(default=None, max_length=5000)


class ManualTaskReason(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class TaskArtifactRead(BaseModel):
    id: UUID
    revision_id: UUID
    artifact_id: UUID
    title: str
    filename: str | None
    uploader_name: str | None
    revision_number: int
    linked_at: datetime


class TaskActivityRead(BaseModel):
    id: UUID
    occurred_at: datetime
    actor_name: str | None
    action_type: str
    details: dict = Field(default_factory=dict)


class TaskNotificationRead(BaseModel):
    id: UUID
    manual_task_id: UUID
    event_type: str
    title: str
    message: str
    read_at: datetime | None
    created_at: datetime


class TaskItem(BaseModel):
    """Unified task shape returned by the My Tasks endpoint."""
    model_config = ConfigDict(from_attributes=True)

    # Which entity type this task comes from.
    entity_type: str

    # UUID of the entity record.
    entity_id: UUID

    # Human-readable title of the task (drawn from the entity's title field).
    title: str

    # Optional supporting detail (currently used by manually created tasks).
    description: str | None = None

    # Current status string (varies by entity type).
    status: str

    created_at: datetime | None = None

    # Optional target completion date.
    due_date: date | None

    # True when due_date is in the past and the task is still open.
    is_overdue: bool

    # Product and release context for display — may be None for orphaned records.
    product_name: str | None
    release_version: str | None

    # Severity / risk level where applicable (None for entity types without it).
    severity: str | None

    # Parent entity ID used for deep-link navigation:
    #   risk_item          → risk_assessment_id  (→ /risk-assessments/:id)
    #   release_gate_item  → product_release_id  (→ /releases/:id)
    #   others             → None
    parent_id: UUID | None = None

    # Display name of whoever created or reported this item (for "Assigned by" display).
    created_by_name: str | None = None

    assigned_to_user_id: UUID | None = None
    assigned_to_name: str | None = None
    related_product_id: UUID | None = None
    related_release_id: UUID | None = None
    viewer_is_assignee: bool = True
    viewer_is_creator: bool = False
    is_completed: bool = False
    priority: str | None = None
    completed_at: datetime | None = None
    completed_by_name: str | None = None
    completion_note: str | None = None
    archived_at: datetime | None = None
    archive_reason: str | None = None
    can_edit_definition: bool = False
    can_update_status: bool = False
    can_archive: bool = False
    evidence: list[TaskArtifactRead] = Field(default_factory=list)
