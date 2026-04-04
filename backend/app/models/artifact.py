from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import ArtifactSourceType, EvidenceType


class Artifact(UUIDTimestampMixin, Base):
    __tablename__ = "artifacts"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_type: Mapped[EvidenceType] = mapped_column(nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    revisions: Mapped[list["ArtifactRevision"]] = relationship(
        "ArtifactRevision",
        back_populates="artifact",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(ArtifactRevision.revision_number)",
    )
    product_links: Mapped[list["ArtifactProductLink"]] = relationship(
        "ArtifactProductLink",
        back_populates="artifact",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ArtifactRevision(UUIDTimestampMixin, Base):
    __tablename__ = "artifact_revisions"
    __table_args__ = (
        UniqueConstraint("artifact_id", "revision_number", name="uq_artifact_revisions_artifact_revision"),
    )

    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[ArtifactSourceType] = mapped_column(nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    artifact: Mapped["Artifact"] = relationship("Artifact", back_populates="revisions")
    uploaded_by_user: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by_user_id])
    release_gate_links: Mapped[list["ReleaseGateEvidenceLink"]] = relationship(
        "ReleaseGateEvidenceLink",
        back_populates="artifact_revision",
        passive_deletes=True,
    )


class ArtifactProductLink(UUIDTimestampMixin, Base):
    __tablename__ = "artifact_product_links"
    __table_args__ = (
        UniqueConstraint("artifact_id", "product_id", name="uq_artifact_product_links_artifact_product"),
    )

    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    artifact: Mapped["Artifact"] = relationship("Artifact", back_populates="product_links")
    product: Mapped["Product"] = relationship("Product")
