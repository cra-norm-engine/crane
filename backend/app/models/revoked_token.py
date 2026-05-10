"""SQLAlchemy model for the JTI blocklist used by logout token invalidation."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    # JWT ID claim — UUID string, 36 chars max.
    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    # When the token would have expired naturally; used for cleanup queries.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
