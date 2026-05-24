"""
Models for CRA Substantial Change Tracking.

This module defines three related tables:
  - Change: records a modification made to a product version
  - SubstantialModificationAssessment: the regulatory assessment deciding whether
    a change is "substantial" under the CRA (i.e. requires re-certification)
  - ChangeComplianceAction: individual compliance tasks that must be completed
    when a change is deemed substantial
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import (
    AssessmentMethodology,
    ChangeStatus,
    ChangeType,
    ComplianceActionStatus,
    ComplianceActionType,
)


class Change(UUIDTimestampMixin, Base):
    """
    Represents a single change made to a product version.

    A change moves through a defined workflow:
      draft → submitted → under_review → assessed → (action_required | closed)

    The 'initiator_user_id' is the person who recorded the change.
    The 'assessor_user_id' is the cybersecurity engineer who claims and assesses it.
    """

    __tablename__ = "changes"

    # --- Relationships ---

    # The product version this change belongs to
    product_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User who initiated/recorded this change
    initiator_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # User who claimed the change for assessment (set on transition to under_review)
    assessor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Task assignment — the user responsible for moving this change forward.
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Optional deadline for completing the assessment or closing the change.
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- Change details ---

    # Category of the change (security patch, new feature, bug fix, maintenance)
    change_type: Mapped[ChangeType] = mapped_column(nullable=False, index=True)

    # Short human-readable title (e.g. "Added BLE connectivity")
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Full description of what changed and why
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Date the change was actually made (may differ from record creation date)
    change_date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Workflow state ---

    # Current lifecycle state of this change record
    status: Mapped[ChangeStatus] = mapped_column(
        nullable=False,
        default=ChangeStatus.draft,
        index=True,
    )

    # Timestamps for key workflow transitions
    submitted_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    assessed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    closed_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- ORM relationships ---

    # One change has at most one assessment
    assessment: Mapped["SubstantialModificationAssessment | None"] = relationship(
        "SubstantialModificationAssessment",
        back_populates="change",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # The product version this change belongs to
    # Explicit foreign_keys required because ProductRelease now has two FK paths
    # back to this table (product_version_id here, and caused_by_change_id on the
    # release side), which would otherwise cause an AmbiguousForeignKeysError.
    product_version: Mapped["ProductRelease"] = relationship(
        "ProductRelease",
        foreign_keys="Change.product_version_id",
        back_populates="changes",
    )


class SubstantialModificationAssessment(UUIDTimestampMixin, Base):
    """
    The CRA substantial modification assessment for a single Change.

    The assessor answers four regulatory criteria (each is a boolean).
    If ANY criterion is True, the change is automatically flagged as substantial
    (is_substantial = True) and a set of compliance actions is required.

    Exception: security-type changes are never substantial under CRA Article 3(4),
    but the form can still be submitted for documentation purposes.
    """

    __tablename__ = "substantial_modification_assessments"
    __table_args__ = (
        # Each change can only have one assessment
        UniqueConstraint("change_id", name="uq_assessment_change"),
    )

    # The change being assessed
    change_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("changes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User who performed the assessment
    assessor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Five CRA Art. 3(30) + Commission guidance §103 assessment criteria ---

    # Art. 3(30)(b): Does this change alter the product's intended purpose or use?
    alters_intended_use: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # §103 criterion 1: Does this change introduce new threat vectors not previously present?
    introduces_new_threat_vectors: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # §103 criterion 2: Does this change enable new attack scenarios that were not possible before?
    enables_new_attack_scenarios: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # §103 criterion 3: Does this change increase the likelihood of previously identified attack scenarios?
    changes_attack_likelihood: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # §103 criterion 4: Does this change increase the impact of previously identified attack scenarios?
    changes_attack_impact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- Outcome ---

    # Derived from the four criteria: True if any criterion is True
    is_substantial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Free-text justification required for the decision
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    # Date the assessment decision was made
    decision_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Assessment methodology (STRIDE, TARA, or custom)
    methodology: Mapped[AssessmentMethodology | None] = mapped_column(nullable=True, index=True)

    # Structured answers per methodology (e.g. {S1: true, S2: false, ...})
    template_answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # --- ORM relationships ---

    change: Mapped["Change"] = relationship("Change", back_populates="assessment")

    # If substantial, one or more compliance actions must be completed
    compliance_actions: Mapped[list["ChangeComplianceAction"]] = relationship(
        "ChangeComplianceAction",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class ChangeComplianceAction(UUIDTimestampMixin, Base):
    """
    A single compliance task that must be completed when a change is substantial.

    Examples: renewing the conformity assessment, updating technical documentation,
    re-releasing the product under the updated DoC.

    These are created automatically when an assessment sets is_substantial = True.
    """

    __tablename__ = "change_compliance_actions"

    # The assessment that triggered this action
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("substantial_modification_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which regulatory compliance task this action represents
    action_type: Mapped[ComplianceActionType] = mapped_column(nullable=False)

    # Current progress on this action
    action_status: Mapped[ComplianceActionStatus] = mapped_column(
        nullable=False,
        default=ComplianceActionStatus.pending,
        index=True,
    )

    # Optional target date for completing this action
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Free-text notes from whoever is handling this action
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # User who marked this action as completed
    completed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- ORM relationship ---
    assessment: Mapped["SubstantialModificationAssessment"] = relationship(
        "SubstantialModificationAssessment",
        back_populates="compliance_actions",
    )
