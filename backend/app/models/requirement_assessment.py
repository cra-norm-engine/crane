# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""Release-level Annex I requirement assessment approval.

A release's requirement assessment (all per-release applicability decisions and
trace records shown in the Annex matrix) can be formally *approved* by a user.
Approval freezes the assessment, records who signed off and when, and gates the
release workflow. Any change after approval requires reopening (amendment) and
re-approval — each approval is captured as an immutable snapshot, so the full
history is append-only.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import RequirementAssessmentStatus

if TYPE_CHECKING:
    from app.models.product import ProductRelease
    from app.models.user import User


class ReleaseRequirementAssessment(UUIDTimestampMixin, Base):
    """The current lifecycle state of one release's requirement assessment.

    One row per release (1:1). Absence of a row is equivalent to an unapproved
    draft, so callers treat "no assessment row" as draft/unlocked.
    """

    __tablename__ = "release_requirement_assessments"
    __table_args__ = (
        UniqueConstraint(
            "product_release_id",
            name="uq_release_requirement_assessments_release",
        ),
    )

    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[RequirementAssessmentStatus] = mapped_column(
        nullable=False,
        default=RequirementAssessmentStatus.draft,
        server_default=RequirementAssessmentStatus.draft.value,
        index=True,
    )
    # Number of times the assessment has been approved (1 after first approval).
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Provenance of the *current* approval (cleared conceptually when reopened —
    # we keep the last values but status=draft means they are historical).
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    product_release: Mapped["ProductRelease"] = relationship("ProductRelease")
    approved_by: Mapped["User"] = relationship("User", foreign_keys=[approved_by_user_id])
    snapshots: Mapped[list["ReleaseRequirementAssessmentSnapshot"]] = relationship(
        "ReleaseRequirementAssessmentSnapshot",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="ReleaseRequirementAssessmentSnapshot.version",
    )


class ReleaseRequirementAssessmentSnapshot(UUIDTimestampMixin, Base):
    """An immutable, frozen copy of the assessment captured at each approval.

    Rows here are never updated or deleted in normal operation — they form the
    append-only approval history (v1, v2, …) and carry an integrity hash.
    """

    __tablename__ = "release_requirement_assessment_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "release_requirement_assessment_id",
            "version",
            name="uq_requirement_assessment_snapshots_version",
        ),
    )

    release_requirement_assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("release_requirement_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Frozen copy of the full matrix + raw decisions/mappings at approval time.
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # SHA-256 of the canonicalised snapshot payload, for tamper-evidence.
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    assessment: Mapped["ReleaseRequirementAssessment"] = relationship(
        "ReleaseRequirementAssessment", back_populates="snapshots"
    )
    approved_by: Mapped["User"] = relationship("User", foreign_keys=[approved_by_user_id])
