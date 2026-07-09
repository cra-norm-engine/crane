# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class AdvisoryRelease(UUIDTimestampMixin, Base):
    """
    Join row linking one SecurityAdvisory to one affected ProductRelease.

    A security advisory is scoped to a product and may affect many of its
    releases (one, several, or all). This is the structured link between an
    advisory and each release it applies to. Deleting either side cascades the
    join row away (but never the advisory itself — that is the point of moving
    the advisory's primary FK to the product).
    """

    __tablename__ = "advisory_releases"
    __table_args__ = (
        UniqueConstraint(
            "security_advisory_id",
            "product_release_id",
            name="uq_advisory_release",
        ),
    )

    security_advisory_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("security_advisories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    security_advisory: Mapped["SecurityAdvisory"] = relationship(
        "SecurityAdvisory",
        back_populates="release_links",
    )
    product_release: Mapped["ProductRelease"] = relationship("ProductRelease")
