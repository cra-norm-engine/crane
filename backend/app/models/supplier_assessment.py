from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class Supplier(UUIDTimestampMixin, Base):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("name", name="uq_suppliers_name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    supplier_type: Mapped[str] = mapped_column(String(40), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    security_contact: Mapped[str | None] = mapped_column(String(320), nullable=True)
    website: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    components: Mapped[list["ThirdPartyComponent"]] = relationship(back_populates="supplier")
    assessments: Mapped[list["SupplierAssessment"]] = relationship(back_populates="supplier")


class ThirdPartyComponent(UUIDTimestampMixin, Base):
    __tablename__ = "third_party_components"
    __table_args__ = (UniqueConstraint("supplier_id", "name", "version", name="uq_supplier_component_version"),)

    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    component_type: Mapped[str] = mapped_column(String(30), nullable=False)
    purl: Mapped[str | None] = mapped_column(String(1024), nullable=True, index=True)
    cpe: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    part_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    support_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    update_channel: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier: Mapped[Supplier] = relationship(back_populates="components")
    release_links: Mapped[list["ProductComponentLink"]] = relationship(back_populates="component", cascade="all, delete-orphan")


class ProductComponentLink(UUIDTimestampMixin, Base):
    __tablename__ = "product_component_links"
    __table_args__ = (UniqueConstraint("product_release_id", "component_id", name="uq_release_third_party_component"),)

    product_release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_releases.id", ondelete="CASCADE"), index=True)
    component_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("third_party_components.id", ondelete="CASCADE"), index=True)
    sbom_record_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sbom_records.id", ondelete="SET NULL"), index=True)
    is_direct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_core_function: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criticality: Mapped[str] = mapped_column(String(20), nullable=False, default="low", index=True)
    criticality_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    usage_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    component: Mapped[ThirdPartyComponent] = relationship(back_populates="release_links")


class SupplierAssessment(UUIDTimestampMixin, Base):
    __tablename__ = "supplier_assessments"
    __table_args__ = (UniqueConstraint("supplier_id", "system_version", name="uq_supplier_assessment_version"),)

    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    component_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("third_party_components.id", ondelete="SET NULL"), index=True)
    product_release_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("product_releases.id", ondelete="SET NULL"), index=True)
    system_version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    tier_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", index=True)
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    reviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reassessment_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reassessment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reassessment_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reassessment_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    supplier: Mapped[Supplier] = relationship(back_populates="assessments")
    component: Mapped[ThirdPartyComponent | None] = relationship()
    responses: Mapped[list["AssessmentResponse"]] = relationship(back_populates="assessment", cascade="all, delete-orphan", order_by="AssessmentResponse.criterion_key")
    evidence_links: Mapped[list["AssessmentEvidenceLink"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")
    findings: Mapped[list["SupplierFinding"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")


class AssessmentResponse(UUIDTimestampMixin, Base):
    __tablename__ = "supplier_assessment_responses"
    __table_args__ = (UniqueConstraint("assessment_id", "criterion_key", name="uq_assessment_criterion"),)

    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("supplier_assessments.id", ondelete="CASCADE"), index=True)
    criterion_key: Mapped[str] = mapped_column(String(100), nullable=False)
    criterion_title: Mapped[str] = mapped_column(String(255), nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    assessment: Mapped[SupplierAssessment] = relationship(back_populates="responses")


class AssessmentEvidenceLink(UUIDTimestampMixin, Base):
    __tablename__ = "supplier_assessment_evidence_links"
    __table_args__ = (UniqueConstraint("assessment_id", "evidence_item_id", name="uq_assessment_evidence"),)

    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("supplier_assessments.id", ondelete="CASCADE"), index=True)
    response_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("supplier_assessment_responses.id", ondelete="SET NULL"), index=True)
    evidence_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evidence_items.id", ondelete="RESTRICT"), index=True)
    issued_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment: Mapped[SupplierAssessment] = relationship(back_populates="evidence_links")
    evidence_item: Mapped["EvidenceItem"] = relationship()


class SupplierFinding(UUIDTimestampMixin, Base):
    __tablename__ = "supplier_findings"

    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("supplier_assessments.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    mitigation_plan: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    risk_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("risk_items.id", ondelete="SET NULL"), index=True)
    assessment: Mapped[SupplierAssessment] = relationship(back_populates="findings")


class ComponentMaintainerNotification(UUIDTimestampMixin, Base):
    __tablename__ = "component_maintainer_notifications"

    vulnerability_report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vulnerability_reports.id", ondelete="CASCADE"), index=True)
    component_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("third_party_components.id", ondelete="RESTRICT"), index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)
    recipient: Mapped[str] = mapped_column(String(320), nullable=False)
    notification_method: Mapped[str] = mapped_column(String(50), nullable=False)
    information_shared: Mapped[str] = mapped_column(Text, nullable=False)
    fix_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fix_reference: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    maintainer_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))

    component: Mapped[ThirdPartyComponent] = relationship()
    vulnerability_report: Mapped["VulnerabilityReport"] = relationship()
