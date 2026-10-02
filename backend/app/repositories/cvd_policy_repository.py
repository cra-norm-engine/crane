# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.cvd_policy import CvdPolicy, CvdPolicyProduct
from app.models.enums import CvdPolicyStatus
from app.repositories.base import BaseRepository


class CvdPolicyRepository(BaseRepository[CvdPolicy]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CvdPolicy)

    def list_all(self, *, product_id: UUID | None = None) -> list[CvdPolicy]:
        statement = (
            select(CvdPolicy)
            .options(selectinload(CvdPolicy.product_links))
            .order_by(CvdPolicy.created_at.desc())
        )
        if product_id:
            statement = statement.where(
                or_(
                    CvdPolicy.organization_wide.is_(True),
                    CvdPolicy.product_links.any(CvdPolicyProduct.product_id == product_id),
                )
            )
        return list(self.db.scalars(statement).all())

    def get_or_404(self, cvd_policy_id: UUID) -> CvdPolicy:
        policy = self.db.scalar(
            select(CvdPolicy)
            .options(selectinload(CvdPolicy.product_links))
            .where(CvdPolicy.id == cvd_policy_id)
        )
        if policy is None:
            raise NotFoundException("CVD policy not found")
        return policy

    def get_effective_active(self, product_id: UUID) -> CvdPolicy | None:
        return self.db.scalar(
            select(CvdPolicy)
            .where(
                CvdPolicy.status == CvdPolicyStatus.active,
                or_(
                    CvdPolicy.organization_wide.is_(True),
                    CvdPolicy.product_links.any(CvdPolicyProduct.product_id == product_id),
                ),
            )
            .order_by(CvdPolicy.organization_wide.asc(), CvdPolicy.updated_at.desc())
        )
