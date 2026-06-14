# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class UserPreference(UUIDTimestampMixin, Base):
    """Per-user personal settings, surfaced in the Settings hub.

    One row per user (created on first read/write). Kept separate from the User
    model so identity/auth stays lean and preferences can grow independently.
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # "dark" | "light" — mirrors the frontend theme tokens.
    theme: Mapped[str] = mapped_column(String(20), nullable=False, default="dark")
    # IANA timezone name, e.g. "UTC", "Europe/Berlin".
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    # Date display pattern token, e.g. "YYYY-MM-DD".
    date_format: Mapped[str] = mapped_column(String(32), nullable=False, default="YYYY-MM-DD")
    # Route name the user lands on after login.
    default_landing_page: Mapped[str] = mapped_column(String(64), nullable=False, default="dashboard")

    user: Mapped["User"] = relationship("User", back_populates="preferences")
