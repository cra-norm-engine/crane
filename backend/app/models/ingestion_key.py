"""Revocable credentials restricted to one SBOM and one external source."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDTimestampMixin


class IngestionKey(UUIDTimestampMixin, Base):
    __tablename__ = "ingestion_keys"

    name: Mapped[str] = mapped_column(String(100))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    sbom_record_id: Mapped[UUID] = mapped_column(ForeignKey("sbom_records.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(100))
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
