# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.security_advisory import SecurityAdvisory
from app.repositories.base import BaseRepository


class SecurityAdvisoryRepository(BaseRepository[SecurityAdvisory]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SecurityAdvisory)

    def list_all(self, *, product_release_id: UUID | None = None) -> list[SecurityAdvisory]:
        statement = select(SecurityAdvisory).order_by(SecurityAdvisory.created_at.desc())
        if product_release_id:
            statement = statement.where(
                SecurityAdvisory.product_release_id == product_release_id
            )
        return list(self.db.scalars(statement).all())

    def get_or_404(self, advisory_id: UUID) -> SecurityAdvisory:
        advisory = self.get_by_id(advisory_id)
        if advisory is None:
            raise NotFoundException("Security advisory not found")
        return advisory

    def get_by_advisory_id(self, advisory_id: str) -> SecurityAdvisory | None:
        statement = select(SecurityAdvisory).where(SecurityAdvisory.advisory_id == advisory_id)
        return self.db.scalars(statement).first()
