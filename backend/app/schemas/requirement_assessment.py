# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import RequirementAssessmentStatus


class RequirementAssessmentRead(BaseModel):
    """Status of a release's Annex I requirement assessment (for the matrix banner)."""

    product_release_id: UUID
    status: RequirementAssessmentStatus
    # Number of approvals so far (0 = never approved).
    version: int
    approved_at: datetime | None = None
    approved_by_name: str | None = None
    # True when approved → the matrix is read-only.
    is_locked: bool
    # True when the assessment may be approved now (every requirement finalized).
    can_approve: bool
    # Codes of requirements not yet finalized (blocks approval).
    unfinalized_codes: list[str] = []
