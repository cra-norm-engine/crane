# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.advisory_release import AdvisoryRelease
from app.models.security_advisory import SecurityAdvisory
from app.repositories.base import BaseRepository


class SecurityAdvisoryRepository(BaseRepository[SecurityAdvisory]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SecurityAdvisory)

    def _load_opts(self):
        # Eager-load the product and each affected release for the Read payload.
        return (
            selectinload(SecurityAdvisory.product),
            selectinload(SecurityAdvisory.release_links).selectinload(
                AdvisoryRelease.product_release
            ),
        )

    def list_all(
        self, *, product_id: UUID | None = None, release_id: UUID | None = None
    ) -> list[SecurityAdvisory]:
        statement = (
            select(SecurityAdvisory)
            .options(*self._load_opts())
            .order_by(SecurityAdvisory.created_at.desc())
        )
        if product_id:
            statement = statement.where(SecurityAdvisory.product_id == product_id)
        if release_id:
            # Advisories whose affected-release set includes this release.
            statement = statement.where(
                SecurityAdvisory.id.in_(
                    select(AdvisoryRelease.security_advisory_id).where(
                        AdvisoryRelease.product_release_id == release_id
                    )
                )
            )
        return list(self.db.scalars(statement).unique().all())

    def get_or_404(self, advisory_id: UUID) -> SecurityAdvisory:
        statement = (
            select(SecurityAdvisory)
            .options(*self._load_opts())
            .where(SecurityAdvisory.id == advisory_id)
        )
        advisory = self.db.scalars(statement).unique().first()
        if advisory is None:
            raise NotFoundException("Security advisory not found")
        return advisory

    def get_by_advisory_id(self, advisory_id: str) -> SecurityAdvisory | None:
        statement = select(SecurityAdvisory).where(
            SecurityAdvisory.advisory_id == advisory_id
        )
        return self.db.scalars(statement).first()
