from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class ManualTask(UUIDTimestampMixin, Base):
    __tablename__ = "manual_tasks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium", index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    completion_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    archived_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    archive_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_releases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("manual_tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_to_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    artifact_links: Mapped[list["ManualTaskArtifactLink"]] = relationship(
        back_populates="manual_task", cascade="all, delete-orphan", passive_deletes=True
    )
    parent_task: Mapped[ManualTask | None] = relationship(remote_side="ManualTask.id")


class ManualTaskArtifactLink(UUIDTimestampMixin, Base):
    __tablename__ = "manual_task_artifact_links"
    __table_args__ = (UniqueConstraint("manual_task_id", "artifact_revision_id", name="uq_manual_task_artifact"),)

    manual_task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("manual_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_revision_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifact_revisions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    linked_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    manual_task: Mapped[ManualTask] = relationship(back_populates="artifact_links")
    artifact_revision: Mapped["ArtifactRevision"] = relationship("ArtifactRevision")


class TaskNotification(UUIDTimestampMixin, Base):
    __tablename__ = "task_notifications"

    manual_task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("manual_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
