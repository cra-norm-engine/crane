from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import CertificationScheme, CertificationStatus


class CertificationRecord(UUIDTimestampMixin, Base):
    __tablename__ = "certification_records"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    certification_scheme: Mapped[CertificationScheme] = mapped_column(
        nullable=False,
        index=True,
    )
    certification_scheme_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    certification_body_name: Mapped[str] = mapped_column(String(255), nullable=False)
    certificate_number: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    scope_description: Mapped[str] = mapped_column(Text, nullable=False)

    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[CertificationStatus] = mapped_column(
        nullable=False,
        default=CertificationStatus.pending,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recertification_required_by: Mapped[date | None] = mapped_column(Date, nullable=True)

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="certification_records",
    )
    artifact_links: Mapped[list["CertificationRecordArtifactLink"]] = relationship(
        "CertificationRecordArtifactLink",
        back_populates="certification_record",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CertificationRecordArtifactLink(UUIDTimestampMixin, Base):
    """
    Links an artifact revision to a certification record as supporting evidence.

    Allows certification records to have file attachments (reports, test evidence, etc.)
    with full revision history and SHA-256 integrity verification.
    """

    __tablename__ = "certification_record_artifact_links"
    __table_args__ = (
        UniqueConstraint(
            "certification_record_id",
            "artifact_revision_id",
            name="uq_certification_artifact_revision",
        ),
    )

    certification_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("certification_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    artifact_revision_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifact_revisions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    linked_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    certification_record: Mapped["CertificationRecord"] = relationship(
        "CertificationRecord",
        back_populates="artifact_links",
    )
    artifact_revision: Mapped["ArtifactRevision"] = relationship("ArtifactRevision")
    linked_by_user: Mapped["User"] = relationship("User")
