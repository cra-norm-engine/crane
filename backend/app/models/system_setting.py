# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SystemSetting(Base):
    """The single row of instance-wide settings."""

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    vulnerability_scanning_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    update_policy: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    update_channel: Mapped[str] = mapped_column(String(20), nullable=False, default="stable")
    update_maintenance_day: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    update_maintenance_hour_utc: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    update_postponed_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
