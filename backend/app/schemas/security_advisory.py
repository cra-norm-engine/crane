# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AdvisoryStatus, SecurityUpdateSeverity


class SecurityAdvisoryBase(BaseModel):
    # An advisory is scoped to a product; the affected releases are carried
    # separately (release_ids on create/update, releases on read).
    product_id: UUID
    advisory_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1)
    summary: str | None = None
    severity: SecurityUpdateSeverity | None = None
    status: AdvisoryStatus = AdvisoryStatus.draft
    cve_ids_json: list[str] = Field(default_factory=list)
    affected_versions_json: list[str] | dict[str, Any] = Field(default_factory=list)
    fixed_in_versions_json: list[str] = Field(default_factory=list)
    workaround: str | None = None
    remediation_steps: str | None = None
    # Gap 7 — embargo end date; advisory stays internal until this date passes.
    embargo_until: datetime | None = None
    published_at: datetime | None = None


class SecurityAdvisoryCreate(SecurityAdvisoryBase):
    # The affected releases. Explicit ids, or set all_releases=True to snapshot
    # every current release of the product at creation time.
    release_ids: list[UUID] = Field(default_factory=list)
    all_releases: bool = False


class SecurityAdvisoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    summary: str | None = None
    severity: SecurityUpdateSeverity | None = None
    status: AdvisoryStatus | None = None
    cve_ids_json: list[str] | None = None
    affected_versions_json: list[str] | dict[str, Any] | None = None
    fixed_in_versions_json: list[str] | None = None
    workaround: str | None = None
    remediation_steps: str | None = None
    embargo_until: datetime | None = None
    published_at: datetime | None = None
    # When provided, replaces the advisory's affected-release set. None = leave as-is.
    release_ids: list[UUID] | None = None


class AdvisoryReleaseRef(BaseModel):
    """A release an advisory affects, for display."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_version: str
    release_status: str


class SecurityAdvisoryRead(SecurityAdvisoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    product_name: str | None = None
    releases: list[AdvisoryReleaseRef] = Field(default_factory=list)
