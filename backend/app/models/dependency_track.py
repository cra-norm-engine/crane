from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDTimestampMixin


class DependencyTrackConnection(UUIDTimestampMixin, Base):
    __tablename__ = "dependency_track_connections"
    __table_args__ = (UniqueConstraint("server_url", "project_id", "sbom_record_id", name="uq_dtrack_mapping"),)

    server_url: Mapped[str] = mapped_column(String(2000))
    api_key_encrypted: Mapped[str] = mapped_column(Text)
    project_id: Mapped[UUID]
    project_name: Mapped[str] = mapped_column(String(500))
    sbom_record_id: Mapped[UUID] = mapped_column(ForeignKey("sbom_records.id", ondelete="CASCADE"))
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    automatic_sync: Mapped[bool] = mapped_column(Boolean, default=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    last_result: Mapped[dict | None] = mapped_column(JSONB)
