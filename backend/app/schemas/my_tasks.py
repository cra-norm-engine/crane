from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaskItem(BaseModel):
    """Unified task shape returned by the My Tasks endpoint."""
    model_config = ConfigDict(from_attributes=True)

    # Which entity type this task comes from.
    entity_type: str

    # UUID of the entity record.
    entity_id: UUID

    # Human-readable title of the task (drawn from the entity's title field).
    title: str

    # Current status string (varies by entity type).
    status: str

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
